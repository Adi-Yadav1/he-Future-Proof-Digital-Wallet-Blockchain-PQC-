#!/usr/bin/env python3
"""
Clear all data from the database
"""

import sqlite3
import os
from models import init_db

DB_PATH = "database/database.db"

def clear_database():
    """Delete all data from database tables."""
    print("\n" + "="*60)
    print("CLEARING DATABASE")
    print("="*60)
    
    if not os.path.exists(DB_PATH):
        print("❌ Database file not found!")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Delete all data from tables
        cursor.execute("DELETE FROM profiles")
        deleted_profiles = cursor.rowcount
        print(f"✓ Deleted {deleted_profiles} profiles")
        
        cursor.execute("DELETE FROM users")
        deleted_users = cursor.rowcount
        print(f"✓ Deleted {deleted_users} users")
        
        # Reset auto-increment counters
        cursor.execute("DELETE FROM sqlite_sequence")
        print("✓ Reset ID counters")
        
        conn.commit()
        print("\n✅ Database cleared successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

def delete_and_recreate_database():
    """Completely delete database file and recreate from scratch."""
    print("\n" + "="*60)
    print("DELETING AND RECREATING DATABASE")
    print("="*60)
    
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("✓ Deleted database file")
    
    init_db()
    print("✓ Created new database with fresh schema")
    print("\n✅ Database recreated successfully!")
    print("="*60)

if __name__ == "__main__":
    print("\nChoose an option:")
    print("1. Clear all data (keep database structure)")
    print("2. Delete and recreate database (complete reset)")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        clear_database()
    elif choice == "2":
        delete_and_recreate_database()
    else:
        print("Invalid choice!")
