import hashlib
import secrets

# Number of bits for message hash (SHA-256 = 256 bits)
HASH_BITS = 256


def sha256(data: bytes) -> bytes:
    """Return SHA-256 hash of input data."""
    return hashlib.sha256(data).digest()


def generate_lamport_keypair():
    """
    Generate a Lamport key pair.
    Private key: 256 pairs of random values
    Public key: Hash of private key values
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


def sign_message(message: str, private_key):
    """
    Sign a message using Lamport private key.
    """
    message_hash = sha256(message.encode())
    signature = []

    for i, bit in enumerate(message_hash):
        for j in range(8):
            bit_value = (bit >> (7 - j)) & 1
            signature.append(private_key[i * 8 + j][bit_value])

    return signature


def verify_signature(message: str, signature, public_key):
    """
    Verify Lamport signature using public key.
    """
    message_hash = sha256(message.encode())
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
    priv, pub = generate_lamport_keypair()
    msg = "Hello Quantum World"

    sig = sign_message(msg, priv)
    result = verify_signature(msg, sig, pub)

    print("Signature valid:", result)