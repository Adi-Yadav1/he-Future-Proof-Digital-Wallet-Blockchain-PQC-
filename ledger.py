import json
import os
from block import Block
from transaction import Transaction


class Ledger:
    def __init__(self, filename="data/blockchain.json", ledger_filename="data/ledger.json"):
        self.filename = filename
        self.ledger_filename = ledger_filename
        self.initial_balance = 1000.0
        self._ensure_ledger_file()

    def _ensure_ledger_file(self):
        os.makedirs(os.path.dirname(self.ledger_filename), exist_ok=True)
        if not os.path.exists(self.ledger_filename) or os.path.getsize(self.ledger_filename) == 0:
            self.save_ledger_state(
                {
                    "balances": {},
                    "wallets": {},
                    "transactions": [],
                    "meta": {"initial_balance": self.initial_balance},
                }
            )

    def load_ledger_state(self):
        self._ensure_ledger_file()
        with open(self.ledger_filename, "r") as f:
            data = json.load(f)

        data.setdefault("balances", {})
        data.setdefault("wallets", {})
        data.setdefault("transactions", [])
        data.setdefault("meta", {"initial_balance": self.initial_balance})
        return data

    def save_ledger_state(self, data):
        with open(self.ledger_filename, "w") as f:
            json.dump(data, f, indent=4)

    def create_wallet(
        self,
        address,
        public_key=None,
        private_key=None,
        encryption_public_key=None,
        encryption_private_key=None,
        grant_initial=True,
    ):
        """
        Create demo wallet with initial balance and optional key material.
        This is used for user onboarding in live demonstrations.
        """
        state = self.load_ledger_state()

        if address not in state["balances"]:
            state["balances"][address] = float(self.initial_balance if grant_initial else 0.0)

        state["wallets"].setdefault(address, {})
        if public_key is not None:
            state["wallets"][address]["public_key"] = public_key
        if private_key is not None:
            state["wallets"][address]["private_key"] = private_key
        if encryption_public_key is not None:
            state["wallets"][address]["encryption_public_key"] = encryption_public_key
        if encryption_private_key is not None:
            state["wallets"][address]["encryption_private_key"] = encryption_private_key

        self.save_ledger_state(state)
        return state["balances"][address]

    def get_balance(self, address):
        state = self.load_ledger_state()
        return float(state["balances"].get(address, 0.0))

    def get_wallet_keys(self, address):
        state = self.load_ledger_state()
        wallet_data = state["wallets"].get(address, {})
        return wallet_data.get("public_key"), wallet_data.get("private_key")

    def get_wallet_bundle(self, address):
        """Return both signing and encryption keys for private transaction operations."""
        state = self.load_ledger_state()
        wallet_data = state["wallets"].get(address, {})
        return {
            "public_key": wallet_data.get("public_key"),
            "private_key": wallet_data.get("private_key"),
            "encryption_public_key": wallet_data.get("encryption_public_key"),
            "encryption_private_key": wallet_data.get("encryption_private_key"),
        }

    def get_total_wallets(self):
        state = self.load_ledger_state()
        return len(state["balances"])

    def get_total_coins(self):
        state = self.load_ledger_state()
        return float(sum(state["balances"].values()))

    def get_transactions_for_wallet(self, wallet_address):
        state = self.load_ledger_state()
        return [
            tx
            for tx in state["transactions"]
            if tx.get("sender") == wallet_address or tx.get("receiver") == wallet_address
        ]

    def rebuild_from_chain(self, chain):
        """Rebuild balances/history from authoritative chain after consensus sync."""
        state = self.load_ledger_state()
        balances = {}

        for address in state.get("wallets", {}).keys():
            balances[address] = float(state.get("balances", {}).get(address, self.initial_balance))

        rebuilt = {
            "balances": balances,
            "wallets": state.get("wallets", {}),
            "transactions": [],
            "meta": state.get("meta", {"initial_balance": self.initial_balance}),
        }

        self.save_ledger_state(rebuilt)

        for block in chain:
            self.apply_block_transactions(block)

    def apply_block_transactions(self, block):
        """
        Apply mined block transactions into ledger balances and history.
        This powers demo balance updates and explorer transaction views.
        """
        state = self.load_ledger_state()
        balances = state["balances"]
        known_hashes = {tx.get("tx_hash") for tx in state["transactions"]}

        for tx in block.transactions:
            tx_hash = tx.calculate_hash()
            if tx_hash in known_hashes:
                continue

            sender = tx.sender
            receiver = tx.receiver
            is_encrypted = bool(getattr(tx, "encrypted_payload", None))

            if is_encrypted:
                # Private transfers keep cleartext values off-chain, so balances are not auto-adjusted.
                amount = 0.0
            else:
                amount = float(tx.amount)

            if sender != "NETWORK":
                balances.setdefault(sender, float(self.initial_balance))
                balances[sender] = float(balances[sender]) - amount

            balances.setdefault(receiver, 0.0)
            balances[receiver] = float(balances[receiver]) + amount

            state["transactions"].append(
                {
                    "sender": sender,
                    "receiver": receiver,
                    "amount": amount,
                    "timestamp": tx.timestamp,
                    "block_index": block.index,
                    "tx_hash": tx_hash,
                    "encrypted_payload": getattr(tx, "encrypted_payload", None),
                }
            )
            known_hashes.add(tx_hash)

        self.save_ledger_state(state)

    def _serialize_signature(self, signature):
        if signature is None:
            return None
        if isinstance(signature, str):
            return signature
        if isinstance(signature, list):
            return [sig.hex() if isinstance(sig, bytes) else sig for sig in signature]
        if isinstance(signature, bytes):
            return signature.hex()
        return signature

    def _serialize_public_key(self, public_key):
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

    def _deserialize_signature(self, signature_data):
        if signature_data is None:
            return None
        if isinstance(signature_data, str):
            return signature_data
        if isinstance(signature_data, list):
            return [bytes.fromhex(s) if isinstance(s, str) else s for s in signature_data]
        return signature_data

    def _deserialize_public_key(self, public_key_data):
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

    def save_blockchain(self, blockchain):
        """Save blockchain to JSON file."""
        data = []

        for block in blockchain.chain:
            block_data = {
                "index": block.index,
                "timestamp": block.timestamp,
                "previous_hash": block.previous_hash,
                "hash": block.hash,
                "nonce": block.nonce,
                "miner": getattr(block, "miner", None),
                "miner_node_id": getattr(block, "miner_node_id", None),
                "signature": self._serialize_signature(block.signature),
                "public_key": self._serialize_public_key(block.public_key),
                "transactions": [
                    {
                        "sender": tx.sender,
                        "receiver": tx.receiver,
                        "amount": tx.amount,
                        "timestamp": tx.timestamp,
                        "signature": self._serialize_signature(tx.signature),
                        "public_key": self._serialize_public_key(tx.public_key),
                        "encrypted_payload": tx.encrypted_payload,
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
                    signature=self._deserialize_signature(tx_data.get("signature")),
                    public_key=self._deserialize_public_key(tx_data.get("public_key")),
                    timestamp=tx_data["timestamp"],
                    encrypted_payload=tx_data.get("encrypted_payload"),
                )
                transactions.append(tx)

            block = Block(
                index=block_data["index"],
                transactions=transactions,
                previous_hash=block_data["previous_hash"],
                signature=self._deserialize_signature(block_data.get("signature")),
                public_key=self._deserialize_public_key(block_data.get("public_key")),
                timestamp=block_data["timestamp"],
                nonce=block_data.get("nonce"),
                miner=block_data.get("miner"),
                miner_node_id=block_data.get("miner_node_id"),
            )

            if "hash" in block_data:
                block.hash = block_data["hash"]

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