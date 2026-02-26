from flask import Flask, request, jsonify
from blockchain import Blockchain
from transaction import Transaction
from wallet import Wallet
from ledger import Ledger
from models import (
    create_user,
    authenticate_user,
    create_profile,
    get_profile
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


# ---------------- AUTH ROUTES ----------------

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    try:
        create_user(data["username"], data["password"])
        return jsonify({"message": "User registered successfully"}), 201
    except Exception:
        return jsonify({"error": "Username already exists"}), 400


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user_id = authenticate_user(data["username"], data["password"])
    if user_id:
        return jsonify({"message": "Login successful", "user_id": user_id})
    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/profile/<int:user_id>", methods=["GET"])
def profile(user_id):
    profile = get_profile(user_id)
    if profile:
        return jsonify({
            "wallet_address": profile[0],
            "created_at": profile[1]
        })
    return jsonify({"message": "Profile not found"}), 404


@app.route("/create_wallet/<int:user_id>", methods=["POST"])
def create_wallet_for_user(user_id):
    wallet = Wallet()
    create_profile(user_id, wallet.get_address())

    return jsonify({
        "message": "Wallet created",
        "wallet_address": wallet.get_address()
    })


# ---------------- BLOCKCHAIN ROUTES ----------------

@app.route("/add_transaction", methods=["POST"])
def add_transaction():
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
    transaction_pool = []

    return jsonify({"message": "Block mined successfully"}), 200


@app.route("/chain", methods=["GET"])
def get_chain():
    return jsonify([
        {
            "index": block.index,
            "timestamp": block.timestamp,
            "previous_hash": block.previous_hash,
            "hash": block.hash,
            "transactions": len(block.transactions)
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


# ---------------- START SERVER ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)