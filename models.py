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
    """Create a new user with hashed password.
    
    Args:
        username: Username string
        password: Plain text password
    
    Returns:
        user_id: The ID of the newly created user
    
    Raises:
        ValueError: If username already exists
    """
    conn = get_db()
    cursor = conn.cursor()

    try:
        # Hash the password using werkzeug (pbkdf2:sha256 by default)
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')

        # Insert user into database
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )

        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        return user_id
        
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError("Username already exists")


def authenticate_user(username, password):
    """Authenticate user by username and password.
    
    Args:
        username: Username string
        password: Plain text password to verify
    
    Returns:
        user_id if authentication successful, None otherwise
    """
    conn = get_db()
    cursor = conn.cursor()

    # Fetch user by username
    cursor.execute(
        "SELECT id, password_hash FROM users WHERE username = ?",
        (username,)
    )
    user = cursor.fetchone()
    conn.close()

    # If user not found
    if not user:
        return None
    
    user_id = user[0]
    stored_hash = user[1]

    # Verify password using werkzeug check_password_hash
    # check_password_hash(pwhash, password) - pwhash first, password second
    if check_password_hash(stored_hash, password):
        return user_id
    
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