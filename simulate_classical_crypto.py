"""Classical crypto demonstration using ECDSA.

Educational purpose:
1. Generate a classical ECDSA keypair (secp256k1).
2. Sign a sample blockchain transaction message.
3. Verify the signature and report timing + signature size.
"""

import time
from hashlib import sha256

from ecdsa import SECP256k1, SigningKey


def main() -> None:
    message = b"sender=alice|receiver=bob|amount=25.0|nonce=42"

    print("=== Classical Blockchain Cryptography Demo (ECDSA) ===")
    print("Step 1: Generating ECDSA keypair on secp256k1...")
    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.verifying_key

    print(f"  Private key size: {len(sk.to_string())} bytes")
    print(f"  Public key size : {len(vk.to_string())} bytes")

    print("Step 2: Signing a transaction message hash with ECDSA...")
    digest = sha256(message).digest()
    t_sign_start = time.perf_counter()
    signature = sk.sign_digest(digest)
    sign_elapsed_ms = (time.perf_counter() - t_sign_start) * 1000

    print(f"  Signature size  : {len(signature)} bytes")
    print(f"  Signing time    : {sign_elapsed_ms:.6f} ms")

    print("Step 3: Verifying ECDSA signature...")
    t_verify_start = time.perf_counter()
    is_valid = vk.verify_digest(signature, digest)
    verify_elapsed_ms = (time.perf_counter() - t_verify_start) * 1000

    print(f"  Signature valid : {is_valid}")
    print(f"  Verification time: {verify_elapsed_ms:.6f} ms")

    print("\nSummary")
    print("- ECDSA works efficiently today, but depends on discrete logarithm hardness.")
    print("- A large-scale quantum computer running Shor's algorithm can break this assumption.")


if __name__ == "__main__":
    main()
