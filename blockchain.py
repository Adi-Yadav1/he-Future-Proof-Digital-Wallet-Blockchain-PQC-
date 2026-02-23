from block import Block
from wallet import Wallet


class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        """Create the first block in the blockchain."""
        genesis_wallet = Wallet()

        genesis_block = Block(
            index=0,
            transactions=[],
            previous_hash="0"
        )

        genesis_block.signature = genesis_wallet.sign(genesis_block.hash)
        genesis_block.public_key = genesis_wallet.public_key

        self.chain.append(genesis_block)

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, transactions, miner_wallet):
        """Add a new block to the chain."""
        previous_block = self.get_latest_block()

        new_block = Block(
            index=len(self.chain),
            transactions=transactions,
            previous_hash=previous_block.hash
        )

        # Sign block hash using miner wallet (PQC)
        new_block.signature = miner_wallet.sign(new_block.hash)
        new_block.public_key = miner_wallet.public_key

        self.chain.append(new_block)

    def is_chain_valid(self):
        """Verify blockchain integrity and PQC signatures."""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            # Verify block hash
            if current_block.hash != current_block.calculate_hash():
                print("[!] Block hash mismatch at index", i)
                return False

            # Verify previous hash link
            if current_block.previous_hash != previous_block.hash:
                print("[!] Chain broken at index", i)
                return False

            # Verify PQC signature
            if not current_block.verify_block_signature():
                print("[!] Invalid block signature at index", i)
                return False

        return True
    



    # ---------------- TEST BLOCKCHAIN ----------------
if __name__ == "__main__":
    from transaction import Transaction

    blockchain = Blockchain()
    miner_wallet = Wallet()

    # Create and sign a transaction
    temp_tx = Transaction(
        sender="Alice",
        receiver="Bob",
        amount=25,
        signature=None,
        public_key=None
    )

    tx_hash = temp_tx.calculate_hash()
    tx_signature = miner_wallet.sign(tx_hash)

    tx = Transaction(
        sender="Alice",
        receiver="Bob",
        amount=25,
        signature=tx_signature,
        public_key=miner_wallet.public_key,
        timestamp=temp_tx.timestamp
    )

    blockchain.add_block([tx], miner_wallet)

    print("Blockchain valid:", blockchain.is_chain_valid())