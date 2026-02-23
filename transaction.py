import time
import json
import hashlib
from pqc_crypto import verify_signature


class Transaction:
    def __init__(self, sender, receiver, amount, signature, public_key, timestamp=None):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.timestamp = timestamp or time.time()
        self.signature = signature
        self.public_key = public_key

    def calculate_hash(self):
        tx_data = {
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
            "timestamp": self.timestamp
        }
        tx_string = json.dumps(tx_data, sort_keys=True)
        return hashlib.sha256(tx_string.encode()).hexdigest()

    def verify(self):
        message = self.calculate_hash()
        return verify_signature(message, self.signature, self.public_key)


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