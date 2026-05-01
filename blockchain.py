from block import Block
from wallet import Wallet
from transaction import Transaction
import requests
from statistics import mean


class Blockchain:
    def __init__(self, difficulty=3, mining_reward=50.0, reward_enabled=True):
        self.difficulty = difficulty
        self.mining_reward = float(mining_reward)
        self.reward_enabled = reward_enabled
        self.chain = []
        self.create_genesis_block()

    def set_demo_config(self, difficulty=None, mining_reward=None, reward_enabled=None):
        """Update runtime mining parameters for demo tuning."""
        if difficulty is not None:
            self.difficulty = int(difficulty)
        if mining_reward is not None:
            self.mining_reward = float(mining_reward)
        if reward_enabled is not None:
            self.reward_enabled = bool(reward_enabled)

    def create_genesis_block(self):
        """Create the first block in the blockchain."""
        genesis_wallet = Wallet()

        genesis_block = Block(
            index=0,
            transactions=[],
            previous_hash="0",
            nonce=0,
        )

        genesis_block.mine_block(self.difficulty)

        genesis_block.signature = genesis_wallet.sign(genesis_block.hash)
        genesis_block.public_key = genesis_wallet.public_key

        self.chain.append(genesis_block)

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, transactions, miner_wallet, miner_address=None, miner_node_id=None):
        """Mine and add a new PoW block to the chain."""
        previous_block = self.get_latest_block()

        tx_list = list(transactions)

        # Reward transaction is protocol-generated for educational demonstrations.
        if self.reward_enabled and miner_address:
            reward_tx = Transaction(
                sender="NETWORK",
                receiver=miner_address,
                amount=self.mining_reward,
                signature=None,
                public_key=None,
            )
            tx_list.append(reward_tx)

        new_block = Block(
            index=len(self.chain),
            transactions=tx_list,
            previous_hash=previous_block.hash,
            nonce=0,
            miner=miner_address,
            miner_node_id=miner_node_id,
        )

        new_block.mine_block(self.difficulty)

        # Sign block hash using miner wallet (PQC)
        new_block.signature = miner_wallet.sign(new_block.hash)
        new_block.public_key = miner_wallet.public_key

        self.chain.append(new_block)
        return new_block

    def add_external_block(self, block):
        """Append block received from peers if it extends local chain validly."""
        latest = self.get_latest_block()

        if block.index != latest.index + 1:
            return False

        if block.previous_hash != latest.hash:
            return False

        if not self._is_valid_new_block(block, latest):
            return False

        self.chain.append(block)
        return True

    def _is_valid_new_block(self, block, previous_block):
        if block.previous_hash != previous_block.hash:
            return False

        if block.hash != block.calculate_hash():
            return False

        if not self._has_valid_pow(block):
            return False

        if not block.verify_block_signature():
            return False

        for tx in block.transactions:
            if not tx.verify():
                return False

        return True

    def is_chain_valid(self):
        """Verify blockchain integrity and PQC signatures."""
        return self.validate_chain(self.chain)

    def validate_chain(self, candidate_chain):
        """Validate full chain structure, PoW, and Dilithium signatures."""
        if not candidate_chain:
            return False

        for i, current_block in enumerate(candidate_chain):
            if current_block.hash != current_block.calculate_hash():
                return False

            if not self._has_valid_pow(current_block):
                return False

            if i > 0:
                previous_block = candidate_chain[i - 1]
                if current_block.previous_hash != previous_block.hash:
                    return False

            if not current_block.verify_block_signature():
                return False

            for tx in current_block.transactions:
                if not tx.verify():
                    return False

        return True

    def _has_valid_pow(self, block):
        # Backward compatibility: chains created before PoW support had no nonce mining.
        if block.hash[: self.difficulty] == "0" * self.difficulty:
            return True
        return getattr(block, "nonce", None) is None

    def resolve_conflicts(self, peers, fetch_chain_fn=None):
        """Adopt the longest valid chain from peers."""
        replaced = False
        longest_chain = self.chain

        for peer in peers:
            try:
                if fetch_chain_fn is not None:
                    peer_chain_data = fetch_chain_fn(peer)
                else:
                    response = requests.get(f"{str(peer).rstrip('/')}/chain", timeout=5)
                    response.raise_for_status()
                    peer_chain_data = response.json()
            except Exception:
                continue

            if isinstance(peer_chain_data, dict) and "chain" in peer_chain_data:
                peer_chain_data = peer_chain_data["chain"]

            candidate_chain = self.deserialize_chain(peer_chain_data)
            if not candidate_chain:
                continue

            if len(candidate_chain) > len(longest_chain) and self.validate_chain(candidate_chain):
                longest_chain = candidate_chain
                replaced = True

        if replaced:
            self.chain = longest_chain

        return replaced

    def serialize_chain(self):
        return [self._serialize_block(block) for block in self.chain]

    def get_total_transactions(self):
        return sum(len(block.transactions) for block in self.chain)

    def get_total_blocks(self):
        return len(self.chain)

    def get_stats(self):
        return {
            "total_blocks": self.get_total_blocks(),
            "total_transactions": self.get_total_transactions(),
            "network_difficulty": self.difficulty,
            "average_block_time": self.get_average_block_time(),
        }

    def get_average_block_time(self):
        """Return average seconds between adjacent blocks for demo dashboards."""
        if len(self.chain) < 2:
            return 0.0

        deltas = []
        for idx in range(1, len(self.chain)):
            current_ts = float(self.chain[idx].timestamp)
            prev_ts = float(self.chain[idx - 1].timestamp)
            deltas.append(max(0.0, current_ts - prev_ts))

        return float(mean(deltas)) if deltas else 0.0

    def deserialize_chain(self, chain_data):
        if not isinstance(chain_data, list):
            return []
        parsed_chain = []
        for block_data in chain_data:
            try:
                parsed_chain.append(self._deserialize_block(block_data))
            except Exception:
                return []
        return parsed_chain

    @staticmethod
    def _serialize_signature(signature):
        if signature is None:
            return None
        if isinstance(signature, str):
            return signature
        if isinstance(signature, list):
            return [sig.hex() if isinstance(sig, bytes) else sig for sig in signature]
        if isinstance(signature, bytes):
            return signature.hex()
        return signature

    @staticmethod
    def _serialize_public_key(public_key):
        if public_key is None:
            return None
        if isinstance(public_key, str):
            return public_key
        if isinstance(public_key, list):
            serialized = []
            for pair in public_key:
                if (
                    isinstance(pair, (list, tuple))
                    and len(pair) == 2
                    and isinstance(pair[0], bytes)
                    and isinstance(pair[1], bytes)
                ):
                    serialized.append((pair[0].hex(), pair[1].hex()))
                else:
                    serialized.append(pair)
            return serialized
        if isinstance(public_key, bytes):
            return public_key.hex()
        return public_key

    @staticmethod
    def _deserialize_signature(signature_data):
        if signature_data is None:
            return None
        if isinstance(signature_data, str):
            return signature_data
        if isinstance(signature_data, list):
            return [bytes.fromhex(s) if isinstance(s, str) else s for s in signature_data]
        return signature_data

    @staticmethod
    def _deserialize_public_key(public_key_data):
        if public_key_data is None:
            return None
        if isinstance(public_key_data, str):
            return public_key_data
        if isinstance(public_key_data, list):
            parsed = []
            for pair in public_key_data:
                if isinstance(pair, (list, tuple)) and len(pair) == 2:
                    pk0, pk1 = pair
                    if isinstance(pk0, str) and isinstance(pk1, str):
                        parsed.append((bytes.fromhex(pk0), bytes.fromhex(pk1)))
                    else:
                        parsed.append((pk0, pk1))
                else:
                    parsed.append(pair)
            return parsed
        return public_key_data

    def _serialize_transaction(self, tx):
        return {
            "sender": tx.sender,
            "receiver": tx.receiver,
            "amount": tx.amount,
            "timestamp": tx.timestamp,
            "signature": self._serialize_signature(tx.signature),
            "public_key": self._serialize_public_key(tx.public_key),
            "encrypted_payload": getattr(tx, "encrypted_payload", None),
            "tx_hash": tx.calculate_hash(),
        }

    def _deserialize_transaction(self, tx_data):
        return Transaction(
            sender=tx_data["sender"],
            receiver=tx_data["receiver"],
            amount=tx_data["amount"],
            signature=self._deserialize_signature(tx_data.get("signature")),
            public_key=self._deserialize_public_key(tx_data.get("public_key")),
            timestamp=tx_data.get("timestamp"),
            encrypted_payload=tx_data.get("encrypted_payload"),
        )

    def _serialize_block(self, block):
        return {
            "index": block.index,
            "timestamp": block.timestamp,
            "previous_hash": block.previous_hash,
            "hash": block.hash,
            "nonce": block.nonce,
            "miner": getattr(block, "miner", None),
            "miner_node_id": getattr(block, "miner_node_id", None),
            "signature": self._serialize_signature(block.signature),
            "public_key": self._serialize_public_key(block.public_key),
            "transactions": [self._serialize_transaction(tx) for tx in block.transactions],
            "transactions_count": len(block.transactions),
        }

    def _deserialize_block(self, block_data):
        transactions = [
            self._deserialize_transaction(tx_data)
            for tx_data in block_data.get("transactions", [])
        ]
        block = Block(
            index=block_data["index"],
            transactions=transactions,
            previous_hash=block_data["previous_hash"],
            signature=self._deserialize_signature(block_data.get("signature")),
            public_key=self._deserialize_public_key(block_data.get("public_key")),
            timestamp=block_data.get("timestamp"),
            nonce=block_data.get("nonce"),
            miner=block_data.get("miner"),
            miner_node_id=block_data.get("miner_node_id"),
        )
        if "hash" in block_data:
            block.hash = block_data["hash"]
        return block
    



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