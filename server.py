from flask import Flask, request, jsonify
from blockchain import Blockchain
from transaction import Transaction
from wallet import Wallet
from ledger import Ledger
from models import (
    create_user,
    authenticate_user,
    create_profile,
    get_profile,
    get_balance,
    get_username_by_wallet,
    transfer_balance_atomic
)

from flask_cors import CORS
app = Flask(__name__)
CORS(app)


# ---------------- GLOBAL STATE ----------------
blockchain = Blockchain()
ledger = Ledger()
transaction_pool = []

# Load blockchain from disk
loaded_chain = ledger.load_blockchain()
if loaded_chain:
    blockchain.chain = loaded_chain

# Miner wallet (server-side)
miner_wallet = Wallet()


def _get_request_payload():
    """Return request payload from JSON first, then form-data as fallback."""
    return request.get_json(silent=True) or request.form.to_dict() or {}


def _extract_credentials(data):
    """Accept username/password and email/password (email maps to username)."""
    username = (data.get("username") or data.get("email") or "").strip()
    password = data.get("password") or ""
    return username, password


# ---------------- AUTH ROUTES ----------------

@app.route("/register", methods=["POST"])
def register():
    """Register a new user with username and password. Auto-generates wallet."""
    data = _get_request_payload()
    
    # Validate input
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    username, password = _extract_credentials(data)
    
    if not username or not password:
        return jsonify({"error": "Missing username/email or password"}), 400
    
    # Validate username and password length
    if len(username.strip()) < 3:
        return jsonify({"error": "Username must be at least 3 characters"}), 400
    
    if len(password) < 4:
        return jsonify({"error": "Password must be at least 4 characters"}), 400
    
    try:
        user_id = create_user(username, password)
        
        # Auto-generate wallet for new user
        wallet = Wallet()
        wallet_address = wallet.get_address()
        create_profile(user_id, wallet_address)
        
        return jsonify({
            "message": "User registered successfully",
            "user_id": user_id,
            "wallet_address": wallet_address
        }), 201
    except ValueError as e:
        # Username already exists
        return jsonify({"error": str(e)}), 409
    except Exception as e:
        # Other database errors
        return jsonify({"error": "Registration failed"}), 500


@app.route("/login", methods=["POST"])
def login():
    """Authenticate user and return user_id."""
    data = _get_request_payload()
    
    # Validate input
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    username, password = _extract_credentials(data)
    
    if not username or not password:
        return jsonify({"error": "Missing username/email or password"}), 400
    
    # Authenticate user
    user_id = authenticate_user(username, password)
    
    if user_id:
        return jsonify({
            "message": "Login successful",
            "user_id": user_id
        }), 200
    
    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/profile/<int:user_id>", methods=["GET"])
def profile(user_id):
    profile = get_profile(user_id)
    balance = get_balance(user_id)
    
    # If profile doesn't exist but user exists, create it
    if not profile and balance is not None:
        wallet = Wallet()
        wallet_address = wallet.get_address()
        create_profile(user_id, wallet_address)
        profile = get_profile(user_id)
    
    if profile:
        return jsonify({
            "wallet_address": profile[0],
            "created_at": profile[1],
            "balance": balance
        })
    return jsonify({"error": "User not found"}), 404


@app.route("/balance/<int:user_id>", methods=["GET"])
def get_user_balance(user_id):
    """Get current balance of user."""
    balance = get_balance(user_id)
    if balance is None:
        return jsonify({"error": "User not found"}), 404
    return jsonify({
        "user_id": user_id,
        "balance": balance
    }), 200


@app.route("/create_wallet/<int:user_id>", methods=["POST"])
def create_wallet_for_user(user_id):
    wallet = Wallet()
    create_profile(user_id, wallet.get_address())

    return jsonify({
        "message": "Wallet created",
        "wallet_address": wallet.get_address()
    })


# ---------------- BLOCKCHAIN ROUTES ----------------

@app.route("/send_transaction", methods=["POST"])
def send_transaction():
    """Simplified transaction endpoint - creates and signs transaction on backend."""
    data = request.json
    
    # Validate input
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    sender = data.get("sender")
    receiver = data.get("receiver")
    amount = data.get("amount")
    user_id = data.get("user_id")  # Get user_id to deduct balance
    
    if not sender or not receiver or not amount:
        return jsonify({"error": "Missing sender, receiver, or amount"}), 400
    
    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({"error": "Amount must be greater than 0"}), 400
    except ValueError:
        return jsonify({"error": "Invalid amount"}), 400
    
    if user_id is not None:
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid user_id"}), 400
    
    # Create a wallet for this transaction (temporary solution)
    # TODO: Store user wallets in database and retrieve them
    wallet = Wallet()
    
    # Create transaction data
    import time
    timestamp = time.time()
    
    temp_tx = Transaction(
        sender=sender,
        receiver=receiver,
        amount=amount,
        signature=None,
        public_key=None,
        timestamp=timestamp
    )
    
    # Sign the transaction
    tx_hash = temp_tx.calculate_hash()
    signature = wallet.sign(tx_hash)
    
    # Create final transaction
    tx = Transaction(
        sender=sender,
        receiver=receiver,
        amount=amount,
        signature=signature,
        public_key=wallet.public_key,
        timestamp=timestamp
    )
    
    # Verify transaction
    if not tx.verify():
        return jsonify({"error": "Transaction verification failed"}), 400
    
    new_balance = None

    # Apply sender debit + local receiver credit in one DB transaction.
    if user_id is not None:
        try:
            transfer_result = transfer_balance_atomic(user_id, receiver, amount)
            new_balance = transfer_result["sender_new_balance"]
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception:
            return jsonify({"error": "Failed to apply transfer"}), 500
    
    # Add to transaction pool
    transaction_pool.append(tx)
    
    return jsonify({
        "message": "Transaction created and added to pool",
        "transaction": {
            "sender": sender,
            "receiver": receiver,
            "amount": amount,
            "timestamp": timestamp
        },
        "new_balance": new_balance if user_id else None
    }), 200


@app.route("/add_transaction", methods=["POST"])
def add_transaction():
    """Advanced endpoint for pre-signed transactions."""
    data = request.json

    tx = Transaction(
        sender=data["sender"],
        receiver=data["receiver"],
        amount=data["amount"],
        signature=[bytes.fromhex(s) for s in data["signature"]],
        public_key=[
            (bytes.fromhex(pk0), bytes.fromhex(pk1))
            for pk0, pk1 in data["public_key"]
        ],
        timestamp=data["timestamp"]
    )

    if not tx.verify():
        return jsonify({"error": "Invalid transaction"}), 400

    transaction_pool.append(tx)
    return jsonify({"message": "Transaction added"}), 200


@app.route("/mine", methods=["POST"])
def mine():
    global transaction_pool

    if not transaction_pool:
        return jsonify({"error": "No transactions to mine"}), 400

    blockchain.add_block(transaction_pool, miner_wallet)
    ledger.save_blockchain(blockchain)
    
    # Get the latest block
    latest_block = blockchain.chain[-1]
    
    transaction_pool = []

    return jsonify({
        "message": "Block mined successfully",
        "block": {
            "index": latest_block.index,
            "hash": latest_block.hash,
            "transactions": len(latest_block.transactions)
        }
    }), 200


@app.route("/chain", methods=["GET"])
def get_chain():
    return jsonify([
        {
            "index": block.index,
            "timestamp": block.timestamp,
            "previous_hash": block.previous_hash,
            "hash": block.hash,
            "transactions": [
                {
                    "sender": get_username_by_wallet(tx.sender),
                    "sender_address": tx.sender,
                    "receiver": get_username_by_wallet(tx.receiver),
                    "receiver_address": tx.receiver,
                    "amount": tx.amount,
                    "timestamp": tx.timestamp
                }
                for tx in block.transactions
            ]
        }
        for block in blockchain.chain
    ])


@app.route("/verify", methods=["GET"])
def verify_chain():
    return jsonify({"valid": blockchain.is_chain_valid()})


@app.route("/status", methods=["GET"])
def status():
    return {
        "message": "Quantum-Resistant Blockchain Server Running",
        "blocks": len(blockchain.chain),
        "pending_transactions": len(transaction_pool)
    }


# ---------------- ADMIN ROUTES ----------------

@app.route("/admin/clear_database", methods=["POST"])
def admin_clear_database():
    """Clear all database and blockchain data. WARNING: This is irreversible!"""
    global blockchain, transaction_pool, ledger
    
    try:
        import sqlite3
        import os
        
        # Clear database
        conn = sqlite3.connect("database/database.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM profiles")
        cursor.execute("DELETE FROM users")
        cursor.execute("DELETE FROM sqlite_sequence")
        conn.commit()
        conn.close()
        
        # Clear blockchain files
        if os.path.exists("data/blockchain.json"):
            os.remove("data/blockchain.json")
        if os.path.exists("data/ledger.json"):
            os.remove("data/ledger.json")
        
        # Reset in-memory state
        blockchain = Blockchain()
        ledger = Ledger()
        transaction_pool = []
        
        return jsonify({
            "message": "✅ Database and blockchain cleared successfully!",
            "status": "cleared"
        }), 200
    
    except Exception as e:
        return jsonify({
            "error": f"Failed to clear database: {str(e)}",
            "status": "failed"
        }), 500


@app.route("/admin/status", methods=["GET"])
def admin_status():
    """Get database and blockchain statistics."""
    try:
        import sqlite3
        
        conn = sqlite3.connect("database/database.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM profiles")
        profile_count = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            "users": user_count,
            "profiles": profile_count,
            "blocks": len(blockchain.chain),
            "pending_transactions": len(transaction_pool)
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- START SERVER ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)