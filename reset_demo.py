import os

from init_db import init_db


FILES_TO_DELETE = [
    "data/blockchain.json",
    "data/ledger.json",
    "database/database.db",
]


def main():
    # Clean previous demo artifacts so each run starts from known state.
    for file_path in FILES_TO_DELETE:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"[RESET] Removed {file_path}")
        else:
            print(f"[RESET] Not found (skipped): {file_path}")

    os.makedirs("data", exist_ok=True)
    os.makedirs("database", exist_ok=True)

    # Recreate SQLite schema for authentication/profile operations.
    init_db()
    print("[RESET] Demo environment initialized successfully")


if __name__ == "__main__":
    main()
