import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = "database/database.db"


def get_db():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # USERS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
    """)

    # PROFILES TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        user_id INTEGER PRIMARY KEY,
        wallet_address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()


def create_user(username, password):
    conn = get_db()
    cursor = conn.cursor()

    password_hash = generate_password_hash(password)

    cursor.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, password_hash)
    )

    conn.commit()
    conn.close()


def authenticate_user(username, password):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, password_hash FROM users WHERE username = ?",
        (username,)
    )
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[1], password):
        return user[0]
    return None


def create_profile(user_id, wallet_address):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR REPLACE INTO profiles (user_id, wallet_address) VALUES (?, ?)",
        (user_id, wallet_address)
    )

    conn.commit()
    conn.close()


def get_profile(user_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT wallet_address, created_at FROM profiles WHERE user_id = ?",
        (user_id,)
    )

    profile = cursor.fetchone()
    conn.close()
    return profile