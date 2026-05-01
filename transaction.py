import time
import json
import hashlib
from pqc_crypto import encrypt_message, verify_signature


class Transaction:
    def __init__(
        self,
        sender,
        receiver,
        amount,
        signature,
        public_key,
        timestamp=None,
        encrypted_payload=None,
    ):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.timestamp = timestamp or time.time()
        self.signature = signature
        self.public_key = public_key
        self.encrypted_payload = encrypted_payload

    def calculate_hash(self):
        tx_data = {
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "encrypted_payload": self.encrypted_payload,
        }
        tx_string = json.dumps(tx_data, sort_keys=True)
        return hashlib.sha256(tx_string.encode()).hexdigest()

    def verify(self):
        # Reward transactions are protocol-generated and not user-signed.
        if self.sender == "NETWORK":
            return self.amount >= 0

        if self.signature is None or self.public_key is None:
            return False

        if self.encrypted_payload is not None and not isinstance(self.encrypted_payload, dict):
            return False

        message = self.calculate_hash()
        return verify_signature(message, self.signature, self.public_key)


def create_private_transaction(sender_wallet, receiver_wallet, amount):
    """
    Build a private transaction where receiver and amount are encrypted for the recipient.

    The chain stores only ciphertext while Dilithium still signs transaction integrity.
    """
    timestamp = time.time()

    plaintext_payload = {
        "receiver": receiver_wallet.get_address(),
        "amount": float(amount),
    }
    encrypted_payload = encrypt_message(receiver_wallet.get_encryption_public_key(), plaintext_payload)

    tx = Transaction(
        sender=sender_wallet.get_address(),
        receiver="ENCRYPTED",
        amount="ENCRYPTED",
        signature=None,
        public_key=sender_wallet.public_key,
        timestamp=timestamp,
        encrypted_payload=encrypted_payload,
    )

    tx.signature = sender_wallet.sign(tx.calculate_hash())
    return tx


if __name__ == "__main__":
    from wallet import Wallet

    sender_wallet = Wallet()
    receiver_wallet = Wallet()

    # Create transaction data first
    temp_tx = Transaction(
        sender=sender_wallet.get_address(),
        receiver=receiver_wallet.get_address(),
        amount=10,
        signature=None,
        public_key=None
    )

    # Sign the TRANSACTION HASH
    tx_hash = temp_tx.calculate_hash()
    signature = sender_wallet.sign(tx_hash)

    # Final transaction
    tx = Transaction(
        sender=sender_wallet.get_address(),
        receiver=receiver_wallet.get_address(),
        amount=10,
        signature=signature,
        public_key=sender_wallet.public_key,
        timestamp=temp_tx.timestamp
    )

    print("Transaction valid:", tx.verify())