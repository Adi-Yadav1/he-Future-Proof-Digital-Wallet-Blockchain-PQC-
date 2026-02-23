import time
import json
import hashlib
from pqc_crypto import verify_signature


class Block:
    def __init__(
        self,
        index,
        transactions,
        previous_hash,
        signature=None,
        public_key=None,
        timestamp=None
    ):
        self.index = index
        self.timestamp = timestamp or time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.signature = signature
        self.public_key = public_key
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        """Calculate SHA-256 hash of the block."""
        block_data = {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": [
                tx.calculate_hash() for tx in self.transactions
            ],
            "previous_hash": self.previous_hash
        }
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def verify_block_signature(self):
        """Verify PQC signature of the block."""
        if self.signature is None or self.public_key is None:
            return False
        return verify_signature(self.hash, self.signature, self.public_key)


# ---------------- TEST BLOCK ----------------
if __name__ == "__main__":
    from wallet import Wallet
    from transaction import Transaction

    miner_wallet = Wallet()

    # Step 1: Create unsigned transaction
    temp_tx = Transaction(
        sender="Alice",
        receiver="Bob",
        amount=5,
        signature=None,
        public_key=None
    )

    # Step 2: Sign transaction hash
    tx_hash = temp_tx.calculate_hash()
    tx_signature = miner_wallet.sign(tx_hash)

    # Step 3: Create signed transaction
    tx = Transaction(
        sender="Alice",
        receiver="Bob",
        amount=5,
        signature=tx_signature,
        public_key=miner_wallet.public_key,
        timestamp=temp_tx.timestamp
    )

    # Step 4: Create block
    block = Block(
        index=1,
        transactions=[tx],
        previous_hash="0000"
    )

    # Step 5: Sign block hash
    block.signature = miner_wallet.sign(block.hash)
    block.public_key = miner_wallet.public_key

    print("Block hash:", block.hash)
    print("Block signature valid:", block.verify_block_signature())