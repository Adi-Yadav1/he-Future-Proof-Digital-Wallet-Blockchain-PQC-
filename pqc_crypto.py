import base64
import hashlib
import json
import secrets
from typing import Any, Tuple

# ---------------------------------------------------------------------------
# Signature primitive — prefer ML-DSA-65 (Dilithium Level 3 / NIST standard).
# Fall back to the older pqcrypto "dilithium2" alias for backward compatibility.
# DILITHIUM_LEVEL and DILITHIUM_LABEL are set at import time so every caller
# (e.g. /crypto_info, frontend CryptographyInfo) can show a consistent label.
# ---------------------------------------------------------------------------
try:
    from pqcrypto.sign import ml_dsa_65 as _dilithium_module
    DILITHIUM_LEVEL = 3
    DILITHIUM_LABEL = "ML-DSA (Dilithium Level 3 / ml_dsa_65)"
except ImportError:
    try:
        from pqcrypto.sign import dilithium3 as _dilithium_module  # type: ignore
        DILITHIUM_LEVEL = 3
        DILITHIUM_LABEL = "ML-DSA (Dilithium Level 3 / dilithium3)"
    except ImportError:
        from pqcrypto.sign import dilithium2 as _dilithium_module  # type: ignore
        DILITHIUM_LEVEL = 2
        DILITHIUM_LABEL = "ML-DSA (Dilithium Level 2 / dilithium2)"

# Internal alias used throughout this module.
dilithium2 = _dilithium_module  # noqa: N816  (kept for internal compatibility)

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ---------------------------------------------------------------------------
# KEM primitive — prefer ML-KEM-512 (Kyber512 / NIST standard).
# ---------------------------------------------------------------------------
try:
    from pqcrypto.kem import ml_kem_512 as kem_kyber512
    KEM_LABEL = "ML-KEM (Kyber512 / ml_kem_512)"
except ImportError:
    from pqcrypto.kem import kyber512 as kem_kyber512  # type: ignore
    KEM_LABEL = "ML-KEM (Kyber512)"

# Number of bits for message hash (SHA-256 = 256 bits)
HASH_BITS = 256


def sha256(data: bytes) -> bytes:
    """Return SHA-256 hash of input data."""
    return hashlib.sha256(data).digest()


def _to_message_bytes(message: Any) -> bytes:
    if isinstance(message, bytes):
        return message
    return str(message).encode("utf-8")


def _encode_b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _decode_b64(data: Any) -> bytes:
    if isinstance(data, bytes):
        return data
    if isinstance(data, str):
        return base64.b64decode(data.encode("ascii"))
    raise TypeError("Expected bytes or base64 string")


def _is_lamport_key(key: Any) -> bool:
    return (
        isinstance(key, list)
        and len(key) == HASH_BITS
        and all(
            isinstance(item, (list, tuple))
            and len(item) == 2
            and isinstance(item[0], bytes)
            and isinstance(item[1], bytes)
            for item in key
        )
    )


def generate_keypair() -> Tuple[str, str]:
    """
    Generate Dilithium keypair (level determined at import time) and return
    base64-serialized keys.

    Returns:
        (private_key_b64, public_key_b64)
    """
    public_key, private_key = dilithium2.generate_keypair()
    return _encode_b64(private_key), _encode_b64(public_key)


def generate_kem_keypair() -> Tuple[str, str]:
    """
    Generate ML-KEM keypair (Kyber512-compatible) and return base64-serialized keys.

    Returns:
        (private_key_b64, public_key_b64)
    """
    public_key, private_key = kem_kyber512.generate_keypair()
    return _encode_b64(private_key), _encode_b64(public_key)


def encrypt_message(public_key: Any, plaintext: Any) -> dict:
    """
    Encrypt plaintext with hybrid PQC KEM + AES-GCM.

    1) KEM encapsulation produces (encapsulated_key, shared_secret)
    2) SHA-256(shared_secret) derives AES-256 key material
    3) AES-GCM encrypts the plaintext for authenticated confidentiality
    """
    public_key_bytes = _decode_b64(public_key)

    if isinstance(plaintext, (dict, list)):
        plaintext_bytes = json.dumps(plaintext, sort_keys=True).encode("utf-8")
    elif isinstance(plaintext, bytes):
        plaintext_bytes = plaintext
    else:
        plaintext_bytes = str(plaintext).encode("utf-8")

    encapsulated_key, shared_secret = kem_kyber512.encrypt(public_key_bytes)
    aes_key = sha256(shared_secret)

    nonce = secrets.token_bytes(12)
    ciphertext = AESGCM(aes_key).encrypt(nonce, plaintext_bytes, associated_data=None)

    return {
        "ciphertext": _encode_b64(ciphertext),
        "encapsulated_key": _encode_b64(encapsulated_key),
        "nonce": _encode_b64(nonce),
    }


def decrypt_message(private_key: Any, ciphertext: dict):
    """
    Decrypt payload produced by encrypt_message.

    1) Decapsulate shared secret with receiver private key
    2) Derive AES key with SHA-256(shared_secret)
    3) AES-GCM decrypt and authenticate ciphertext
    """
    private_key_bytes = _decode_b64(private_key)

    encapsulated_key = _decode_b64(ciphertext["encapsulated_key"])
    encrypted_bytes = _decode_b64(ciphertext["ciphertext"])
    nonce = _decode_b64(ciphertext["nonce"])

    shared_secret = kem_kyber512.decrypt(private_key_bytes, encapsulated_key)
    aes_key = sha256(shared_secret)

    plaintext_bytes = AESGCM(aes_key).decrypt(nonce, encrypted_bytes, associated_data=None)
    plaintext_text = plaintext_bytes.decode("utf-8")

    try:
        return json.loads(plaintext_text)
    except json.JSONDecodeError:
        return plaintext_text


def sign_message(message: Any, private_key: Any):
    """
    Sign message using the Dilithium variant loaded at import time.

    For backward compatibility, if a Lamport private key structure is passed,
    this falls back to Lamport signing and returns legacy byte-list signatures.
    """
    if _is_lamport_key(private_key):
        return _sign_lamport_message(message, private_key)

    message_bytes = _to_message_bytes(message)
    private_key_bytes = _decode_b64(private_key)

    signature = None
    for args in ((private_key_bytes, message_bytes), (message_bytes, private_key_bytes)):
        try:
            signature = dilithium2.sign(*args)
            break
        except Exception:
            continue

    if signature is None:
        raise ValueError("Unable to sign message with available ML-DSA binding signature")

    return _encode_b64(signature)


def verify_signature(message: Any, signature: Any, public_key: Any) -> bool:
    """
    Verify signature with automatic compatibility handling.

    - Dilithium2 signatures: base64 string (or bytes)
    - Legacy Lamport signatures: list[bytes] with Lamport public key structure
    """
    if _is_lamport_key(public_key):
        return _verify_lamport_signature(message, signature, public_key)

    message_bytes = _to_message_bytes(message)

    try:
        signature_bytes = _decode_b64(signature)
        public_key_bytes = _decode_b64(public_key)
    except (TypeError, ValueError):
        return False

    result = None
    verify_attempts = (
        (signature_bytes, message_bytes, public_key_bytes),
        (message_bytes, signature_bytes, public_key_bytes),
        (public_key_bytes, message_bytes, signature_bytes),
    )

    for args in verify_attempts:
        try:
            result = dilithium2.verify(*args)
            break
        except Exception:
            continue

    if result is None:
        return False

    # Some bindings return None on success and raise on failure.
    if isinstance(result, bool):
        return result
    return True


def generate_lamport_keypair():
    """
    Legacy helper kept for compatibility and benchmarking.
    """
    private_key = []
    public_key = []

    for _ in range(HASH_BITS):
        sk0 = secrets.token_bytes(32)
        sk1 = secrets.token_bytes(32)
        private_key.append((sk0, sk1))

        pk0 = sha256(sk0)
        pk1 = sha256(sk1)
        public_key.append((pk0, pk1))

    return private_key, public_key


def _sign_lamport_message(message: Any, private_key):
    message_hash = sha256(_to_message_bytes(message))
    signature = []

    for i, bit in enumerate(message_hash):
        for j in range(8):
            bit_value = (bit >> (7 - j)) & 1
            signature.append(private_key[i * 8 + j][bit_value])

    return signature


def _verify_lamport_signature(message: Any, signature, public_key) -> bool:
    if not isinstance(signature, list) or len(signature) != HASH_BITS * 8:
        return False

    message_hash = sha256(_to_message_bytes(message))
    sig_index = 0

    for i, byte in enumerate(message_hash):
        for j in range(8):
            bit_value = (byte >> (7 - j)) & 1
            expected_hash = public_key[i * 8 + j][bit_value]

            if sha256(signature[sig_index]) != expected_hash:
                return False

            sig_index += 1

    return True


if __name__ == "__main__":
    private_key, public_key = generate_keypair()
    message = "Hello Dilithium"

    signature = sign_message(message, private_key)
    result = verify_signature(message, signature, public_key)

    print("Signature valid:", result)