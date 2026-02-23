import json
import os
from block import Block
from transaction import Transaction


class Ledger:
    def __init__(self, filename="data/blockchain.json"):
        self.filename = filename

    def save_blockchain(self, blockchain):
        """Save blockchain to JSON file."""
        data = []

        for block in blockchain.chain:
            block_data = {
                "index": block.index,
                "timestamp": block.timestamp,
                "previous_hash": block.previous_hash,
                "hash": block.hash,
                "signature": [sig.hex() for sig in block.signature],
                "public_key": [
                    (pk0.hex(), pk1.hex()) for pk0, pk1 in block.public_key
                ],
                "transactions": [
                    {
                        "sender": tx.sender,
                        "receiver": tx.receiver,
                        "amount": tx.amount,
                        "timestamp": tx.timestamp,
                        "signature": [sig.hex() for sig in tx.signature],
                        "public_key": [
                            (pk0.hex(), pk1.hex()) for pk0, pk1 in tx.public_key
                        ]
                    }
                    for tx in block.transactions
                ]
            }
            data.append(block_data)

        with open(self.filename, "w") as f:
            json.dump(data, f, indent=4)

    def load_blockchain(self):
        """Load blockchain from JSON file."""
        if not os.path.exists(self.filename):
            return None

        with open(self.filename, "r") as f:
            data = json.load(f)

        chain = []

        for block_data in data:
            transactions = []
            for tx_data in block_data["transactions"]:
                tx = Transaction(
                    sender=tx_data["sender"],
                    receiver=tx_data["receiver"],
                    amount=tx_data["amount"],
                    signature=[bytes.fromhex(s) for s in tx_data["signature"]],
                    public_key=[
                        (bytes.fromhex(pk0), bytes.fromhex(pk1))
                        for pk0, pk1 in tx_data["public_key"]
                    ],
                    timestamp=tx_data["timestamp"]
                )
                transactions.append(tx)

            block = Block(
                index=block_data["index"],
                transactions=transactions,
                previous_hash=block_data["previous_hash"],
                signature=[bytes.fromhex(s) for s in block_data["signature"]],
                public_key=[
                    (bytes.fromhex(pk0), bytes.fromhex(pk1))
                    for pk0, pk1 in block_data["public_key"]
                ],
                timestamp=block_data["timestamp"]
            )

            chain.append(block)

        return chain
    


    # ---------------- TEST LEDGER ----------------
if __name__ == "__main__":
    from blockchain import Blockchain
    from wallet import Wallet
    from transaction import Transaction

    blockchain = Blockchain()
    ledger = Ledger()
    miner_wallet = Wallet()

    temp_tx = Transaction(
        sender="Alice",
        receiver="Bob",
        amount=50,
        signature=None,
        public_key=None
    )

    tx_hash = temp_tx.calculate_hash()
    tx_signature = miner_wallet.sign(tx_hash)

    tx = Transaction(
        sender="Alice",
        receiver="Bob",
        amount=50,
        signature=tx_signature,
        public_key=miner_wallet.public_key,
        timestamp=temp_tx.timestamp
    )

    blockchain.add_block([tx], miner_wallet)

    ledger.save_blockchain(blockchain)
    print("Blockchain saved to file.")

    loaded_chain = ledger.load_blockchain()
    print("Blocks loaded from file:", len(loaded_chain))