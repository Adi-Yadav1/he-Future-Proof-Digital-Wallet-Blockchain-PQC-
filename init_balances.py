#!/usr/bin/env python3
"""
Script to initialize/update balance for all users (1000 tokens each)
Run this once to give all registered users starting balance
"""

import sqlite3

DB_PATH = "database/database.db"

def init_user_balances():
    """Give 1000 tokens to all users who don't have a balance set."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if balance column exists
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'balance' not in columns:
        print("❌ Balance column doesn't exist. Run init_db.py first.")
        conn.close()
        return

    # Get all users
    cursor.execute("SELECT id, username, balance FROM users")
    users = cursor.fetchall()

    print(f"Found {len(users)} users")
    print("-" * 50)

    for user_id, username, current_balance in users:
        # Update balance to 1000 for all users
        cursor.execute(
            "UPDATE users SET balance = 1000 WHERE id = ?",
            (user_id,)
        )
        print(f"✓ {username:20} -> Balance: 1000 PKC")

    conn.commit()
    conn.close()

    print("-" * 50)
    print(f"✅ All {len(users)} users now have 1000 PKC balance!")


if __name__ == "__main__":
    init_user_balances()
