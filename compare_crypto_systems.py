"""Compare classical and post-quantum cryptography metrics.

Algorithms compared:
- ECDSA (classical)
- Dilithium (ML-DSA, via Wallet/pqcrypto)
- Kyber (ML-KEM hybrid encryption, via pqc_crypto)
"""

import base64
import time
from statistics import mean

from ecdsa import SECP256k1, SigningKey

from pqc_crypto import decrypt_message, encrypt_message, generate_kem_keypair, verify_signature
from wallet import Wallet

RUNS = 20


def _avg_ms(samples: list[float]) -> float:
    return (mean(samples) * 1000) if samples else 0.0


def ecdsa_metrics() -> dict:
    verify_times = []
    message = b"comparison-message"

    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.verifying_key
    signature = sk.sign(message)

    for _ in range(RUNS):
        t0 = time.perf_counter()
        vk.verify(signature, message)
        verify_times.append(time.perf_counter() - t0)

    return {
        "algorithm": "ECDSA",
        "key_size_bytes": len(vk.to_string()),
        "signature_size_bytes": len(signature),
        "verify_time_ms": round(_avg_ms(verify_times), 6),
        "encryption_time_ms": None,
    }


def dilithium_metrics() -> dict:
    verify_times = []
    message = "comparison-message"

    wallet = Wallet()
    signature = wallet.sign(message)

    for _ in range(RUNS):
        t0 = time.perf_counter()
        verify_signature(message, signature, wallet.public_key)
        verify_times.append(time.perf_counter() - t0)

    if isinstance(signature, str):
        signature_size = len(base64.b64decode(signature.encode("ascii")))
    elif isinstance(signature, list):
        signature_size = sum(len(chunk) for chunk in signature)
    else:
        signature_size = len(signature)

    return {
        "algorithm": "Dilithium",
        "key_size_bytes": len(base64.b64decode(wallet.public_key.encode("ascii"))),
        "signature_size_bytes": signature_size,
        "verify_time_ms": round(_avg_ms(verify_times), 6),
        "encryption_time_ms": None,
    }


def kyber_metrics() -> dict:
    encrypt_times = []
    private_key, public_key = generate_kem_keypair()
    payload = {"receiver": "bob", "amount": 42.5}

    sample_cipher = None
    for _ in range(RUNS):
        t0 = time.perf_counter()
        sample_cipher = encrypt_message(public_key, payload)
        encrypt_times.append(time.perf_counter() - t0)

    # Validate round-trip once for correctness in comparison output.
    decrypt_message(private_key, sample_cipher)

    return {
        "algorithm": "Kyber",
        "key_size_bytes": len(base64.b64decode(public_key.encode("ascii"))),
        "signature_size_bytes": None,
        "verify_time_ms": None,
        "encryption_time_ms": round(_avg_ms(encrypt_times), 6),
    }


def build_comparison() -> dict:
    rows = [ecdsa_metrics(), dilithium_metrics(), kyber_metrics()]
    return {
        "runs": RUNS,
        "rows": rows,
    }


def _fmt(value):
    return "N/A" if value is None else str(value)


def print_table(result: dict) -> None:
    print("Algorithm | Key Size | Signature Size | Verify Time (ms) | Encryption Time (ms)")
    print("---|---|---|---|---")
    for row in result["rows"]:
        print(
            f"{row['algorithm']} | "
            f"{_fmt(row['key_size_bytes'])} | "
            f"{_fmt(row['signature_size_bytes'])} | "
            f"{_fmt(row['verify_time_ms'])} | "
            f"{_fmt(row['encryption_time_ms'])}"
        )


def main() -> None:
    result = build_comparison()
    print(f"=== Crypto System Comparison ({result['runs']} runs) ===")
    print_table(result)
    print("\nInterpretation:")
    print("- ECDSA is efficient but vulnerable to Shor-style quantum attacks.")
    print("- Dilithium provides quantum-resistant signatures.")
    print("- Kyber provides quantum-resistant key encapsulation for encrypted payloads.")


if __name__ == "__main__":
    main()
