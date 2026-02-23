from wallet import Wallet
from transaction import Transaction
from blockchain import Blockchain
from ledger import Ledger


def print_menu():
    print("\n=== Quantum-Resistant Blockchain Wallet ===")
    print("1. Create Wallet")
    print("2. Show Wallet Address")
    print("3. Create Transaction")
    print("4. Mine Block")
    print("5. View Blockchain")
    print("6. Verify Blockchain")
    print("7. Exit")


def main():
    ledger = Ledger()
    blockchain = Blockchain()

    # Load blockchain from file if exists
    loaded_chain = ledger.load_blockchain()
    if loaded_chain:
        blockchain.chain = loaded_chain
        print("[+] Blockchain loaded from disk.")

    wallet = None
    pending_transactions = []

    while True:
        print_menu()
        choice = input("Enter choice: ")

        if choice == "1":
            wallet = Wallet()
            print("[+] Wallet created successfully.")

        elif choice == "2":
            if wallet:
                print("Wallet Address:")
                print(wallet.get_address())
            else:
                print("[!] Create a wallet first.")

        elif choice == "3":
            if not wallet:
                print("[!] Create a wallet first.")
                continue

            receiver = input("Enter receiver address: ")
            amount = float(input("Enter amount: "))

            # Create unsigned transaction
            temp_tx = Transaction(
                sender=wallet.get_address(),
                receiver=receiver,
                amount=amount,
                signature=None,
                public_key=None
            )

            # Sign transaction hash
            tx_hash = temp_tx.calculate_hash()
            signature = wallet.sign(tx_hash)

            tx = Transaction(
                sender=wallet.get_address(),
                receiver=receiver,
                amount=amount,
                signature=signature,
                public_key=wallet.public_key,
                timestamp=temp_tx.timestamp
            )

            pending_transactions.append(tx)
            print("[+] Transaction added to pool.")

        elif choice == "4":
            if not wallet:
                print("[!] Create a wallet first.")
                continue

            if not pending_transactions:
                print("[!] No transactions to mine.")
                continue

            blockchain.add_block(pending_transactions, wallet)
            ledger.save_blockchain(blockchain)

            pending_transactions = []
            print("[+] Block mined and saved to blockchain.")

        elif choice == "5":
            for block in blockchain.chain:
                print("\n-------------------------------")
                print(f"Block Index: {block.index}")
                print(f"Timestamp: {block.timestamp}")
                print(f"Previous Hash: {block.previous_hash}")
                print(f"Block Hash: {block.hash}")
                print(f"Transactions: {len(block.transactions)}")

        elif choice == "6":
            if blockchain.is_chain_valid():
                print("[✓] Blockchain is valid.")
            else:
                print("[✗] Blockchain is NOT valid.")

        elif choice == "7":
            print("Exiting...")
            break

        else:
            print("[!] Invalid choice.")


if __name__ == "__main__":
    main()