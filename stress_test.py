import tempfile
import time

from blockchain import Blockchain
from ledger import Ledger
from transaction import Transaction, create_private_transaction
from wallet import Wallet


def build_signed_transaction(sender_wallet, receiver_wallet, amount):
    tx = Transaction(
        sender=sender_wallet.get_address(),
        receiver=receiver_wallet.get_address(),
        amount=amount,
        signature=None,
        public_key=None,
    )
    tx.signature = sender_wallet.sign(tx.calculate_hash())
    tx.public_key = sender_wallet.public_key
    return tx


def main():
    with tempfile.TemporaryDirectory() as temp_dir:
        ledger = Ledger(
            filename=f"{temp_dir}/blockchain.json",
            ledger_filename=f"{temp_dir}/ledger.json",
        )
        chain = Blockchain(difficulty=1, reward_enabled=False)

        wallets = [Wallet() for _ in range(10)]
        for wallet in wallets:
            ledger.create_wallet(
                wallet.get_address(),
                public_key=wallet.public_key,
                private_key=wallet.private_key,
                encryption_public_key=wallet.encryption_public_key,
                encryption_private_key=wallet.encryption_private_key,
            )

        pending = []
        for i in range(95):
            sender = wallets[i % len(wallets)]
            receiver = wallets[(i + 1) % len(wallets)]
            pending.append(build_signed_transaction(sender, receiver, amount=1 + (i % 7)))

        for i in range(5):
            sender = wallets[i]
            receiver = wallets[(i + 3) % len(wallets)]
            pending.append(create_private_transaction(sender, receiver, amount=5 + i))

        total_start = time.perf_counter()
        validation_time = 0.0
        ledger_update_time = 0.0

        for block_idx in range(10):
            chunk = pending[block_idx * 10 : (block_idx + 1) * 10]
            block = chain.add_block(chunk, wallets[0])

            t0 = time.perf_counter()
            ledger.apply_block_transactions(block)
            ledger_update_time += time.perf_counter() - t0

            t1 = time.perf_counter()
            chain.is_chain_valid()
            validation_time += time.perf_counter() - t1

        total_elapsed = time.perf_counter() - total_start

        print("=== Blockchain Stress Test Summary ===")
        print("Transactions simulated: 100")
        print("Private transactions simulated: 5")
        print("Blocks mined: 10")
        print(f"Total execution time: {total_elapsed:.4f} sec")
        print(f"Block validation time: {validation_time:.4f} sec")
        print(f"Ledger update time: {ledger_update_time:.4f} sec")


if __name__ == "__main__":
    main()
