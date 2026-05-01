"""Final educational demo narrative for academic presentation.

Demonstrates:
1. Classical crypto example (ECDSA)
2. Simulated quantum attack explanation
3. Dilithium verification
4. Kyber encryption
5. Blockchain transaction
6. Mining
7. Private transaction
"""

from blockchain import Blockchain
from transaction import Transaction, create_private_transaction
from wallet import Wallet

from pqc_crypto import decrypt_message, encrypt_message, verify_signature


def _say(step: int, title: str, detail: str) -> None:
    print(f"\nStep {step}: {title}")
    print(f"  {detail}")


def run_demo() -> None:
    print("=== Final Post-Quantum Blockchain Presentation Demo ===")
    print("This walkthrough explains why post-quantum cryptography is required.")

    _say(1, "Classical crypto example", "Run `simulate_classical_crypto.py` to show ECDSA signing/verification.")
    _say(2, "Quantum attack simulation", "Run `simulate_quantum_attack.py` to explain key-recovery risk from public keys.")

    alice = Wallet()
    bob = Wallet()

    _say(3, "Dilithium verification", "Signing a message with ML-DSA and verifying its authenticity.")
    msg = "academic-demo-message"
    sig = alice.sign(msg)
    print(f"  Dilithium verify result: {verify_signature(msg, sig, alice.public_key)}")

    _say(4, "Kyber encryption", "Encrypting private payload with ML-KEM + AES-GCM hybrid mode.")
    ciphertext = encrypt_message(bob.get_encryption_public_key(), {"receiver": bob.get_address(), "amount": 19.5})
    plaintext = decrypt_message(bob.encryption_private_key, ciphertext)
    print(f"  Decrypted payload: {plaintext}")

    chain = Blockchain(difficulty=1, reward_enabled=False)

    _say(5, "Blockchain transaction", "Creating and verifying a signed public transaction.")
    tx = Transaction(
        sender=alice.get_address(),
        receiver=bob.get_address(),
        amount=7.0,
        signature=None,
        public_key=None,
    )
    tx.signature = alice.sign(tx.calculate_hash())
    tx.public_key = alice.public_key
    print(f"  Transaction verify result: {tx.verify()}")

    _say(6, "Mining", "Mining a block to include the verified transaction.")
    mined = chain.add_block([tx], alice)
    print(f"  Mined block index={mined.index}, hash={mined.hash[:20]}...")

    _say(7, "Private transaction", "Creating encrypted transaction data while preserving public signature verification.")
    private_tx = create_private_transaction(alice, bob, amount=13.0)
    private_ok = private_tx.verify()
    decrypted = bob.decrypt_transaction(private_tx)
    print(f"  Private tx signature valid: {private_ok}")
    print(f"  Private tx decrypted payload: {decrypted}")

    print("\nConclusion:")
    print("- Classical signatures are efficient but quantum-vulnerable.")
    print("- Dilithium and Kyber preserve blockchain security under quantum threat models.")


if __name__ == "__main__":
    run_demo()
