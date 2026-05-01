import base64
import os
import random
import time
from types import SimpleNamespace
from uuid import uuid4

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO

from blockchain import Blockchain
from ledger import Ledger
from models import authenticate_user, create_profile, create_user, get_profile, init_db
from network import NodeNetwork
from pqc_crypto import (
    DILITHIUM_LABEL,
    DILITHIUM_LEVEL,
    KEM_LABEL,
    decrypt_message,
    encrypt_message,
    sign_message,
)
from transaction import Transaction, create_private_transaction
from wallet import Wallet

app = Flask(__name__)
CORS(app)  # Allow all origins for REST routes (Phase 0 Fix #6)
socketio = SocketIO(app, cors_allowed_origins="*")

NODE_RUNTIME = {
    "host": "0.0.0.0",
    "port": 5000,
}

DEMO_CONFIG = {
    "difficulty": 3,
    "mining_reward": 50.0,
    "reward_enabled": True,
    "verbose": True,
    "teaching_mode": False,
    "presentation_mode": False,
    "auto_network_metrics": False,
    "simplified_responses": False,
}

blockchain = Blockchain(
    difficulty=DEMO_CONFIG["difficulty"],
    mining_reward=DEMO_CONFIG["mining_reward"],
    reward_enabled=DEMO_CONFIG["reward_enabled"],
)
ledger = Ledger()
transaction_pool = []
node_id = str(uuid4())

init_db()

loaded_chain = ledger.load_blockchain()
if loaded_chain:
    blockchain.chain = loaded_chain
    ledger.rebuild_from_chain(blockchain.chain)

miner_wallet = Wallet()
ledger.create_wallet(
    miner_wallet.get_address(),
    public_key=miner_wallet.public_key,
    private_key=miner_wallet.private_key,
    encryption_public_key=miner_wallet.encryption_public_key,
    encryption_private_key=miner_wallet.encryption_private_key,
    grant_initial=False,
)

network = NodeNetwork(node_id=node_id, socketio_client=socketio)


def configure_demo_mode(
    difficulty=None,
    reward_enabled=None,
    verbose=None,
    mining_reward=None,
    presentation_mode=None,
    teaching_mode=None,
):
    if difficulty is not None:
        DEMO_CONFIG["difficulty"] = int(difficulty)
    if reward_enabled is not None:
        DEMO_CONFIG["reward_enabled"] = bool(reward_enabled)
    if verbose is not None:
        DEMO_CONFIG["verbose"] = bool(verbose)
    if mining_reward is not None:
        DEMO_CONFIG["mining_reward"] = float(mining_reward)
    if presentation_mode is not None:
        DEMO_CONFIG["presentation_mode"] = bool(presentation_mode)
    if teaching_mode is not None:
        DEMO_CONFIG["teaching_mode"] = bool(teaching_mode)

    if DEMO_CONFIG["presentation_mode"]:
        # Presentation mode keeps responses concise and logs explicit for classroom narration.
        DEMO_CONFIG["auto_network_metrics"] = True
        DEMO_CONFIG["simplified_responses"] = True
        DEMO_CONFIG["verbose"] = True
    else:
        DEMO_CONFIG["auto_network_metrics"] = False
        DEMO_CONFIG["simplified_responses"] = False

    blockchain.set_demo_config(
        difficulty=DEMO_CONFIG["difficulty"],
        reward_enabled=DEMO_CONFIG["reward_enabled"],
        mining_reward=DEMO_CONFIG["mining_reward"],
    )


def configure_node_runtime(host=None, port=None):
    if host is not None:
        NODE_RUNTIME["host"] = host
    if port is not None:
        NODE_RUNTIME["port"] = int(port)


def _log(message, level="INFO"):
    if DEMO_CONFIG["verbose"]:
        print(f"[NODE {NODE_RUNTIME['port']}] {level} {message}")


def _log_warn(message):
    _log(message, level="WARN")


def _log_error(message):
    _log(message, level="ERROR")


def _teach(message):
    if DEMO_CONFIG["teaching_mode"]:
        _log(f"[TEACH] {message}")


def _parse_signature(signature_payload):
    if isinstance(signature_payload, list):
        return [bytes.fromhex(s) if isinstance(s, str) else s for s in signature_payload]
    return signature_payload


def _parse_public_key(public_key_payload):
    if isinstance(public_key_payload, list):
        parsed = []
        for pair in public_key_payload:
            if isinstance(pair, (list, tuple)) and len(pair) == 2:
                pk0, pk1 = pair
                if isinstance(pk0, str) and isinstance(pk1, str):
                    parsed.append((bytes.fromhex(pk0), bytes.fromhex(pk1)))
                else:
                    parsed.append((pk0, pk1))
            else:
                parsed.append(pair)
        return parsed
    return public_key_payload


def _serialize_transaction(tx):
    return {
        "sender": tx.sender,
        "receiver": tx.receiver,
        "amount": tx.amount,
        "timestamp": tx.timestamp,
        "signature": blockchain._serialize_signature(tx.signature),
        "public_key": blockchain._serialize_public_key(tx.public_key),
        "encrypted_payload": getattr(tx, "encrypted_payload", None),
    }


def _transaction_exists(tx_hash):
    for pending in transaction_pool:
        if pending.calculate_hash() == tx_hash:
            return True

    for block in blockchain.chain:
        for tx in block.transactions:
            if tx.calculate_hash() == tx_hash:
                return True

    return False


def _remove_confirmed_transactions(confirmed_transactions=None):
    if confirmed_transactions is None:
        confirmed_hashes = {
            tx.calculate_hash() for block in blockchain.chain for tx in block.transactions
        }
    else:
        confirmed_hashes = {tx.calculate_hash() for tx in confirmed_transactions}

    remaining = [tx for tx in transaction_pool if tx.calculate_hash() not in confirmed_hashes]
    transaction_pool.clear()
    transaction_pool.extend(remaining)


def _resolve_wallet_address(wallet_address_or_user_id):
    candidate = str(wallet_address_or_user_id)
    if candidate.isdigit():
        profile = get_profile(int(candidate))
        if profile:
            return profile[0]
    return candidate


def _get_available_balance(address):
    balance = ledger.get_balance(address)
    for tx in transaction_pool:
        try:
            amount = float(tx.amount)
        except (TypeError, ValueError):
            # Private transactions keep cleartext amount hidden from global state.
            continue
        if tx.sender == address:
            balance -= amount
        if tx.receiver == address:
            balance += amount
    return float(balance)


def _build_wallet_from_ledger(address):
    bundle = ledger.get_wallet_bundle(address)
    required_keys = ["public_key", "private_key", "encryption_public_key", "encryption_private_key"]
    if not all(bundle.get(k) for k in required_keys):
        return None

    return Wallet.from_serialized_keys(
        public_key=bundle["public_key"],
        private_key=bundle["private_key"],
        encryption_public_key=bundle["encryption_public_key"],
        encryption_private_key=bundle["encryption_private_key"],
    )


def _find_transaction_by_hash(tx_hash):
    for tx in transaction_pool:
        if tx.calculate_hash() == tx_hash:
            return tx, None

    for block in blockchain.chain:
        for tx in block.transactions:
            if tx.calculate_hash() == tx_hash:
                return tx, block.index

    return None, None


def _build_miner_identity(miner_address):
    public_key, private_key = ledger.get_wallet_keys(miner_address)
    if public_key and private_key:
        return SimpleNamespace(
            public_key=public_key,
            private_key=private_key,
            sign=lambda message: sign_message(message, private_key),
        )
    return miner_wallet


def _compute_network_metrics():
    stats = blockchain.get_stats()
    return {
        "total_nodes": len(network.peers) + 1,
        "total_blocks": stats["total_blocks"],
        "total_transactions": stats["total_transactions"],
        "average_block_time": round(float(stats.get("average_block_time", 0.0)), 4),
        "difficulty": blockchain.difficulty,
    }


def _emit_network_metrics():
    if DEMO_CONFIG["auto_network_metrics"]:
        socketio.emit("network_metrics", _compute_network_metrics())


def _collect_signature_sizes(limit=25):
    sizes = []
    for block in reversed(blockchain.chain):
        for tx in block.transactions:
            if tx.signature is None:
                continue
            sig = tx.signature
            if isinstance(sig, str):
                try:
                    sizes.append(len(base64.b64decode(sig.encode("ascii"))))
                except Exception:
                    continue
            elif isinstance(sig, list):
                if sig and isinstance(sig[0], bytes):
                    sizes.append(sum(len(chunk) for chunk in sig))
                elif sig and isinstance(sig[0], str):
                    sizes.append(sum(len(bytes.fromhex(chunk)) for chunk in sig))

            if len(sizes) >= limit:
                return sizes
    return sizes


def _append_verified_transaction(tx, propagated_by=None):
    tx_hash = tx.calculate_hash()

    if _transaction_exists(tx_hash):
        _log_warn(f"Duplicate transaction ignored: {tx_hash[:16]}...")
        return {"message": "Duplicate transaction ignored", "tx_hash": tx_hash}, 200

    if tx.sender != "NETWORK":
        if getattr(tx, "encrypted_payload", None):
            _log("Private transaction accepted with encrypted amount/receiver")
        else:
            if _get_available_balance(tx.sender) < float(tx.amount):
                return {"error": "Insufficient balance"}, 400

    transaction_pool.append(tx)
    _log(f"Transaction created: {tx.sender} -> {tx.receiver} ({tx.amount})")
    _teach("Nodes verify digital signatures before accepting a transaction into the mempool.")

    if propagated_by != node_id:
        _log(f"Broadcasting transaction to {len(network.peers)} peers")
        network.broadcast_transaction(_serialize_transaction(tx))
        _teach("Mempool gossip spreads verified transactions across peer nodes.")

    _emit_network_metrics()

    # Phase 8 — real-time push to connected frontend clients.
    socketio.emit("new_transaction", {
        "sender": tx.sender,
        "receiver": getattr(tx, "encrypted_payload", None) and "ENCRYPTED" or tx.receiver,
        "amount": "ENCRYPTED" if getattr(tx, "encrypted_payload", None) else tx.amount,
        "encrypted": bool(getattr(tx, "encrypted_payload", None)),
        "tx_hash": tx_hash,
    })

    return {"message": "Transaction added", "tx_hash": tx_hash}, 200


@socketio.on("connect")
def on_socket_connect():
    socketio.emit("node_connected", {"node_id": node_id})


@socketio.on("register_node")
def on_register_node(data):
    peer_url = data.get("peer_url") if isinstance(data, dict) else None
    if peer_url:
        if network.has_peer(peer_url):
            _log_warn(f"Duplicate peer registration ignored via socket: {peer_url}")
            return
        network.register_peer(peer_url)
        _log(f"Peer registered via socket: {peer_url}")
        socketio.emit("peer_registered", {"peer": peer_url, "node_id": node_id})


@app.route("/register", methods=["POST"])
def register():
    data = request.json or {}
    try:
        user_id = create_user(data["username"], data["password"])

        user_wallet = Wallet()
        create_profile(user_id, user_wallet.get_address())
        ledger.create_wallet(
            user_wallet.get_address(),
            public_key=user_wallet.public_key,
            private_key=user_wallet.private_key,
            encryption_public_key=user_wallet.encryption_public_key,
            encryption_private_key=user_wallet.encryption_private_key,
        )

        _log(f"New user registered: {data['username']} ({user_wallet.get_address()[:12]}...)")
        return (
            jsonify(
                {
                    "message": "User created",
                    "user_id": user_id,
                    "wallet_address": user_wallet.get_address(),
                    "balance": ledger.get_balance(user_wallet.get_address()),
                    "initial_balance": ledger.get_balance(user_wallet.get_address()),
                }
            ),
            201,
        )
    except Exception:
        return jsonify({"error": "Username already exists"}), 400


@app.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    user_id = authenticate_user(data.get("username"), data.get("password"))
    if user_id:
        return jsonify({"message": "Login successful", "user_id": user_id})
    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/profile/<int:user_id>", methods=["GET"])
def profile(user_id):
    profile_row = get_profile(user_id)
    if profile_row:
        return jsonify(
            {
                "wallet_address": profile_row[0],
                "created_at": profile_row[1],
                "balance": ledger.get_balance(profile_row[0]),
            }
        )
    return jsonify({"message": "Profile not found"}), 404


@app.route("/create_wallet/<int:user_id>", methods=["POST"])
def create_wallet_for_user(user_id):
    wallet = Wallet()
    create_profile(user_id, wallet.get_address())
    ledger.create_wallet(
        wallet.get_address(),
        public_key=wallet.public_key,
        private_key=wallet.private_key,
        encryption_public_key=wallet.encryption_public_key,
        encryption_private_key=wallet.encryption_private_key,
    )

    return jsonify(
        {
            "message": "Wallet created",
            "wallet_address": wallet.get_address(),
            "balance": ledger.get_balance(wallet.get_address()),
        }
    )


@app.route("/add_transaction", methods=["POST"])
def add_transaction():
    data = request.json or {}
    required = ["sender", "receiver", "amount", "timestamp", "signature", "public_key"]
    missing = [field for field in required if field not in data]
    if missing:
        return jsonify({"error": f"Missing transaction fields: {', '.join(missing)}"}), 400

    tx = Transaction(
        sender=data["sender"],
        receiver=data["receiver"],
        amount=data["amount"],
        signature=_parse_signature(data.get("signature")),
        public_key=_parse_public_key(data.get("public_key")),
        timestamp=data["timestamp"],
        encrypted_payload=data.get("encrypted_payload"),
    )

    if not tx.verify():
        return jsonify({"error": "Invalid transaction"}), 400

    _log("Transaction verified via Dilithium signature")
    _teach("Dilithium verification confirms authenticity without using classical ECDSA.")

    response, status = _append_verified_transaction(tx, propagated_by=data.get("propagated_by"))
    return jsonify(response), status


@app.route("/send_transaction", methods=["POST"])
def send_transaction():
    data = request.json or {}

    user_id = data.get("user_id") or request.headers.get("X-User-ID")
    sender = data.get("sender")
    receiver = data.get("receiver")
    amount = float(data.get("amount", 0))

    if not sender or not receiver or amount <= 0:
        return jsonify({"error": "Invalid transaction payload"}), 400

    if user_id:
        owner_address = _resolve_wallet_address(user_id)
        if owner_address and owner_address != sender:
            return jsonify({"error": "Sender address does not belong to authenticated user"}), 403

    public_key, private_key = ledger.get_wallet_keys(sender)
    if not public_key or not private_key:
        return jsonify({"error": "Wallet keys unavailable for sender"}), 400

    temp_tx = Transaction(
        sender=sender,
        receiver=receiver,
        amount=amount,
        signature=None,
        public_key=None,
    )
    tx_hash = temp_tx.calculate_hash()
    signature = sign_message(tx_hash, private_key)

    tx = Transaction(
        sender=sender,
        receiver=receiver,
        amount=amount,
        signature=signature,
        public_key=public_key,
        timestamp=temp_tx.timestamp,
    )

    if not tx.verify():
        return jsonify({"error": "Transaction signature verification failed"}), 400

    _log("Transaction verified via Dilithium signature")
    _teach("A valid Dilithium signature proves sender authorization for this transaction.")
    response, status = _append_verified_transaction(tx)
    response["new_balance"] = _get_available_balance(sender)
    return jsonify(response), status


@app.route("/private_transaction", methods=["POST"])
def private_transaction():
    data = request.json or {}
    sender_address = _resolve_wallet_address(data.get("sender_wallet"))
    receiver_address = _resolve_wallet_address(data.get("receiver_wallet"))

    try:
        amount = float(data.get("amount", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid amount"}), 400

    if not sender_address or not receiver_address or amount <= 0:
        return jsonify({"error": "Invalid private transaction payload"}), 400

    if _get_available_balance(sender_address) < amount:
        return jsonify({"error": "Insufficient balance"}), 400

    sender_wallet = _build_wallet_from_ledger(sender_address)
    receiver_wallet = _build_wallet_from_ledger(receiver_address)
    if not sender_wallet or not receiver_wallet:
        return jsonify({"error": "Sender or receiver key material unavailable"}), 400

    # Educational flow: encrypt receiver+amount with ML-KEM, then sign tx hash with Dilithium.
    tx = create_private_transaction(sender_wallet, receiver_wallet, amount)
    _teach("Private transaction metadata is encrypted with Kyber (ML-KEM) before broadcast.")

    if not tx.verify():
        return jsonify({"error": "Private transaction signature verification failed"}), 400

    response, status = _append_verified_transaction(tx)
    if status != 200:
        return jsonify(response), status

    return jsonify({"message": "Private transaction created", "encrypted": True, "tx_hash": tx.calculate_hash()})


@app.route("/mine", methods=["POST"])
def mine():
    data = request.json or {}

    if not transaction_pool and not blockchain.reward_enabled:
        return jsonify({"error": "No transactions to mine"}), 400

    miner_hint = data.get("miner_address") or request.headers.get("X-User-ID")
    miner_address = (
        _resolve_wallet_address(miner_hint) if miner_hint is not None else miner_wallet.get_address()
    )
    miner_identity = _build_miner_identity(miner_address)

    mined_block = blockchain.add_block(
        list(transaction_pool),
        miner_identity,
        miner_address=miner_address,
        miner_node_id=node_id,
    )
    _teach("Mining packages verified transactions into an immutable, hash-linked block.")

    ledger.apply_block_transactions(mined_block)
    ledger.save_blockchain(blockchain)

    _remove_confirmed_transactions(mined_block.transactions)
    _log(f"Broadcasting block #{mined_block.index} to peers")
    network.broadcast_block(blockchain._serialize_block(mined_block))
    _emit_network_metrics()

    _log(f"Block mined: #{mined_block.index} hash={mined_block.hash[:16]}...")
    _log(f"Mining reward issued: {blockchain.mining_reward} -> {miner_address}")
    _teach("Proof-of-Work raises the cost of rewriting history and secures distributed consensus.")

    # Phase 8 — broadcast new block to all connected frontend clients via WebSocket.
    block_payload = blockchain._serialize_block(mined_block)
    socketio.emit("new_block", block_payload)
    socketio.emit("network_update", _compute_network_metrics())

    return (
        jsonify(
            {
                "message": "Block mined successfully",
                "hash": mined_block.hash,
                "block": block_payload,
            }
        ),
        200,
    )


@app.route("/chain", methods=["GET"])
def get_chain():
    return jsonify(blockchain.serialize_chain())


@app.route("/blocks", methods=["GET"])
def get_blocks():
    blocks = []
    for block in blockchain.chain:
        transaction_summaries = []
        for tx in block.transactions:
            is_private = bool(getattr(tx, "encrypted_payload", None))
            transaction_summaries.append(
                {
                    "tx_hash": tx.calculate_hash(),
                    "block_index": block.index,
                    "sender": tx.sender,
                    "receiver": "ENCRYPTED" if is_private else tx.receiver,
                    "amount": "ENCRYPTED" if is_private else tx.amount,
                    "encrypted": is_private,
                }
            )

        blocks.append(
            {
                "index": block.index,
                "timestamp": block.timestamp,
                "hash": block.hash,
                "previous_hash": block.previous_hash,
                "transactions_count": len(block.transactions),
                "miner": getattr(block, "miner", None),
                "miner_node_id": getattr(block, "miner_node_id", None),  # standardized key
                "transactions": transaction_summaries,
            }
        )
    return jsonify(blocks)


@app.route("/explorer", methods=["GET"])
def explorer():
    stats = blockchain.get_stats()
    return jsonify(
        {
            "total_blocks": stats["total_blocks"],
            "total_transactions": stats["total_transactions"],
            "pending_transactions": len(transaction_pool),
            "total_wallets": ledger.get_total_wallets(),
            "network_difficulty": stats["network_difficulty"],
        }
    )


@app.route("/demo_stats", methods=["GET"])
def demo_stats():
    stats = blockchain.get_stats()
    return jsonify(
        {
            "total_blocks": stats["total_blocks"],
            "total_transactions": stats["total_transactions"],
            "total_wallets": ledger.get_total_wallets(),
            "total_coins": ledger.get_total_coins(),
            "pending_transactions": len(transaction_pool),
        }
    )


@app.route("/health", methods=["GET"])
def health():
    # Lightweight health payload used by the classroom control panel.
    return jsonify(
        {
            "status": "ok",
            "node_id": node_id,
            "block_height": len(blockchain.chain),
            "pending_transactions": len(transaction_pool),
            "peer_count": len(network.peers),
        }
    )


@app.route("/balance/<wallet_address>", methods=["GET"])
def get_balance(wallet_address):
    resolved = _resolve_wallet_address(wallet_address)
    return jsonify({"address": resolved, "balance": _get_available_balance(resolved)})


@app.route("/transactions/<wallet_address>", methods=["GET"])
def get_transactions(wallet_address):
    resolved = _resolve_wallet_address(wallet_address)
    txs = ledger.get_transactions_for_wallet(resolved)
    sanitized = []
    for tx in txs:
        tx_view = dict(tx)
        if tx_view.get("encrypted_payload") is not None:
            tx_view["receiver"] = "ENCRYPTED"
            tx_view["amount"] = "ENCRYPTED"
            tx_view["encrypted"] = True
        else:
            tx_view["encrypted"] = False
        sanitized.append(tx_view)

    return jsonify(sanitized)


@app.route("/decrypt_transaction/<tx_id>", methods=["GET"])
def decrypt_transaction(tx_id):
    receiver_wallet_address = _resolve_wallet_address(
        request.args.get("receiver_wallet") or request.headers.get("X-User-ID")
    )

    if not receiver_wallet_address:
        return jsonify({"error": "receiver_wallet is required"}), 400

    tx, _ = _find_transaction_by_hash(tx_id)
    if tx is None:
        return jsonify({"error": "Transaction not found"}), 404

    if not getattr(tx, "encrypted_payload", None):
        return jsonify({"error": "Transaction is not encrypted"}), 400

    receiver_wallet = _build_wallet_from_ledger(receiver_wallet_address)
    if receiver_wallet is None:
        return jsonify({"error": "Receiver wallet key material unavailable"}), 400

    try:
        plaintext = receiver_wallet.decrypt_transaction(tx)
    except Exception as exc:
        _log_warn(f"Failed to decrypt transaction {tx_id[:16]}...: {exc}")
        return jsonify({"error": "Unable to decrypt payload with provided wallet"}), 403

    if not isinstance(plaintext, dict):
        return jsonify({"error": "Decrypted payload format invalid"}), 400

    return jsonify(
        {
            "receiver": plaintext.get("receiver"),
            "amount": plaintext.get("amount"),
        }
    )


@app.route("/crypto_info", methods=["GET"])
def crypto_info():
    sizes = _collect_signature_sizes()
    avg_size = (sum(sizes) / len(sizes)) if sizes else 0
    return jsonify(
        {
            "signature_algorithm": DILITHIUM_LABEL,
            "dilithium_level": DILITHIUM_LEVEL,
            "encryption_algorithm": KEM_LABEL,
            "aes_mode": "AES-256-GCM",
            "library": "pqcrypto",
            "signature_size_bytes": round(avg_size, 2),
            "quantum_resistant": True,
        }
    )


@app.route("/system_info", methods=["GET"])
def system_info():
    """Educational endpoint exposing architecture choices and known limitations."""
    return jsonify(
        {
            "signature_scheme": DILITHIUM_LABEL,
            "dilithium_level": DILITHIUM_LEVEL,
            "kem_scheme": KEM_LABEL,
            "aes_mode": "AES-256-GCM",
            "consensus": "Proof-of-Work (Nakamoto longest-chain)",
            "quantum_resistant": True,
            "known_limitations": {
                "private_tx_balance": (
                    "Private transactions store amounts in encrypted_payload. "
                    "The on-chain ledger does NOT auto-adjust balances after mining because "
                    "the amount is hidden. Senders are balance-checked at submission time, "
                    "but the deduction is not applied post-mining. "
                    "This is an intentional educational trade-off."
                ),
                "auth": (
                    "Authentication uses user_id header/body — no JWT or session expiry. "
                    "Suitable for demo/educational use only."
                ),
            },
        }
    )


@app.route("/crypto_comparison", methods=["GET"])
def crypto_comparison():
    # Live educational endpoint for frontend dashboards and classroom demos.
    try:
        import compare_crypto_systems as compare_module
    except Exception as exc:
        return jsonify({"error": f"Unable to load comparison module: {exc}"}), 500

    runs = request.args.get("runs", default=None, type=int)
    if runs is not None and runs > 0:
        previous = compare_module.RUNS
        compare_module.RUNS = min(runs, 200)
        try:
            result = compare_module.build_comparison()
        finally:
            compare_module.RUNS = previous
        return jsonify(result)

    return jsonify(compare_module.build_comparison())


@app.route("/benchmark", methods=["GET"])
def benchmark():
    # Lightweight cryptographic timings are exposed for live demo observability.
    sample_wallet = Wallet()
    peer_wallet = Wallet()
    message = "benchmark-payload"
    runs = 5

    sign_times = []
    verify_times = []
    encrypt_times = []
    decrypt_times = []

    for _ in range(runs):
        t0 = time.perf_counter()
        signature = sample_wallet.sign(message)
        sign_times.append(time.perf_counter() - t0)

        t1 = time.perf_counter()
        from pqc_crypto import verify_signature

        verify_signature(message, signature, sample_wallet.public_key)
        verify_times.append(time.perf_counter() - t1)

        t2 = time.perf_counter()
        encrypted = encrypt_message(peer_wallet.get_encryption_public_key(), {"msg": message})
        encrypt_times.append(time.perf_counter() - t2)

        t3 = time.perf_counter()
        decrypt_message(peer_wallet.encryption_private_key, encrypted)
        decrypt_times.append(time.perf_counter() - t3)

    to_ms = lambda values: round((sum(values) / len(values)) * 1000, 4)
    return jsonify(
        {
            "dilithium_sign_ms": to_ms(sign_times),
            "dilithium_verify_ms": to_ms(verify_times),
            "kyber_encrypt_ms": to_ms(encrypt_times),
            "kyber_decrypt_ms": to_ms(decrypt_times),
        }
    )


@app.route("/run_demo", methods=["POST"])
def run_demo():
    suffix = int(time.time())
    user1 = f"alice_{suffix}@demo.com"
    user2 = f"bob_{suffix}@demo.com"
    password = "Demo@123"

    steps = []

    try:
        user1_id = create_user(user1, password)
        wallet1 = Wallet()
        create_profile(user1_id, wallet1.get_address())
        ledger.create_wallet(
            wallet1.get_address(),
            public_key=wallet1.public_key,
            private_key=wallet1.private_key,
            encryption_public_key=wallet1.encryption_public_key,
            encryption_private_key=wallet1.encryption_private_key,
        )
        steps.append({"step": "register_user_1", "status": "ok", "wallet": wallet1.get_address()})

        user2_id = create_user(user2, password)
        wallet2 = Wallet()
        create_profile(user2_id, wallet2.get_address())
        ledger.create_wallet(
            wallet2.get_address(),
            public_key=wallet2.public_key,
            private_key=wallet2.private_key,
            encryption_public_key=wallet2.encryption_public_key,
            encryption_private_key=wallet2.encryption_private_key,
        )
        steps.append({"step": "register_user_2", "status": "ok", "wallet": wallet2.get_address()})

        temp_tx = Transaction(
            sender=wallet1.get_address(),
            receiver=wallet2.get_address(),
            amount=120,
            signature=None,
            public_key=None,
        )
        tx_hash = temp_tx.calculate_hash()
        tx_signature = sign_message(tx_hash, wallet1.private_key)

        tx = Transaction(
            sender=wallet1.get_address(),
            receiver=wallet2.get_address(),
            amount=120,
            signature=tx_signature,
            public_key=wallet1.public_key,
            timestamp=temp_tx.timestamp,
        )

        response, status = _append_verified_transaction(tx)
        if status != 200:
            return jsonify({"error": response.get("error", "Demo transaction failed"), "steps": steps}), 400
        steps.append({"step": "send_transaction", "status": "ok", "tx_hash": response.get("tx_hash")})

        mined_block = blockchain.add_block(
            list(transaction_pool),
            _build_miner_identity(wallet1.get_address()),
            miner_address=wallet1.get_address(),
            miner_node_id=node_id,
        )
        ledger.apply_block_transactions(mined_block)
        ledger.save_blockchain(blockchain)
        _remove_confirmed_transactions(mined_block.transactions)
        _log(f"Broadcasting block #{mined_block.index} to peers")
        network.broadcast_block(blockchain._serialize_block(mined_block))
        _emit_network_metrics()
        steps.append({"step": "mine_block", "status": "ok", "index": mined_block.index, "hash": mined_block.hash})

        valid = blockchain.is_chain_valid()
        steps.append({"step": "verify_chain", "status": "ok" if valid else "failed", "valid": valid})

        return jsonify(
            {
                "message": "Demo flow completed",
                "steps": steps,
                "block_hash": mined_block.hash,
                "balances": {
                    wallet1.get_address(): ledger.get_balance(wallet1.get_address()),
                    wallet2.get_address(): ledger.get_balance(wallet2.get_address()),
                },
            }
        )
    except Exception as exc:
        _log_error(f"Demo flow failed: {exc}")
        return jsonify({"error": f"Demo flow failed: {exc}", "steps": steps}), 500


@app.route("/simulate_transactions", methods=["POST"])
def simulate_transactions():
    data = request.json or {}
    count = max(1, int(data.get("count", 5)))

    wallets = list(ledger.load_ledger_state().get("wallets", {}).keys())
    if len(wallets) < 2:
        return jsonify({"error": "Need at least two wallets to simulate transactions"}), 400

    created = 0
    attempts = 0
    max_attempts = count * 5

    # Simulated traffic helps populate blocks quickly during live demos.
    while created < count and attempts < max_attempts:
        attempts += 1
        sender, receiver = random.sample(wallets, 2)
        available = _get_available_balance(sender)
        if available <= 1:
            continue

        amount = round(random.uniform(0.5, min(available * 0.2, 50.0)), 2)
        public_key, private_key = ledger.get_wallet_keys(sender)
        if not public_key or not private_key:
            _log_warn(f"Skipping simulation sender without keys: {sender[:12]}...")
            continue

        temp_tx = Transaction(sender=sender, receiver=receiver, amount=amount, signature=None, public_key=None)
        signature = sign_message(temp_tx.calculate_hash(), private_key)
        tx = Transaction(
            sender=sender,
            receiver=receiver,
            amount=amount,
            signature=signature,
            public_key=public_key,
            timestamp=temp_tx.timestamp,
        )

        if not tx.verify():
            _log_warn("Ignoring simulated transaction that failed verification")
            continue

        result, status = _append_verified_transaction(tx)
        if status == 200 and result.get("message") == "Transaction added":
            created += 1

    return jsonify({"message": "Simulation completed", "requested": count, "created": created})


@app.route("/mine_now", methods=["POST"])
def mine_now():
    # Force-mining endpoint is used by presenters to demonstrate block creation on demand.
    data = request.json or {}
    miner_hint = data.get("miner_address") or request.headers.get("X-User-ID")
    miner_address = _resolve_wallet_address(miner_hint) if miner_hint is not None else miner_wallet.get_address()
    miner_identity = _build_miner_identity(miner_address)

    mined_block = blockchain.add_block(
        list(transaction_pool),
        miner_identity,
        miner_address=miner_address,
        miner_node_id=node_id,
    )

    ledger.apply_block_transactions(mined_block)
    ledger.save_blockchain(blockchain)
    _remove_confirmed_transactions(mined_block.transactions)
    network.broadcast_block(blockchain._serialize_block(mined_block))
    _emit_network_metrics()

    if DEMO_CONFIG["simplified_responses"]:
        return jsonify({"message": "Mining started", "difficulty": blockchain.difficulty})

    return jsonify(
        {
            "message": "Mining started",
            "difficulty": blockchain.difficulty,
            "block": blockchain._serialize_block(mined_block),
        }
    )


@app.route("/network_metrics", methods=["GET"])
def network_metrics():
    # Aggregated metrics power the dashboard panel without extra client-side computation.
    return jsonify(_compute_network_metrics())


@app.route("/nodes/register", methods=["POST"])
def register_nodes():
    data = request.json or {}
    nodes = data.get("nodes", [])

    if not isinstance(nodes, list):
        return jsonify({"error": "Please supply a valid list of nodes"}), 400

    added = 0
    for node in nodes:
        if network.has_peer(node):
            _log_warn(f"Duplicate peer registration ignored: {node}")
            continue
        network.register_peer(node)
        added += 1
        _log(f"Peer registered: {node}")

    return (
        jsonify(
            {
                "message": "New nodes have been added",
                "total_nodes": sorted(network.peers),
                "node_id": node_id,
                "added": added,
            }
        ),
        201,
    )


@app.route("/nodes", methods=["GET"])
def get_nodes():
    return jsonify({"node_id": node_id, "peers": sorted(network.peers)})


@app.route("/node_info", methods=["GET"])
def node_info():
    return jsonify(
        {
            "node_id": node_id,
            "host": NODE_RUNTIME["host"],
            "port": NODE_RUNTIME["port"],
            "peers": sorted(network.peers),
            "block_height": len(blockchain.chain),
            "pending_transactions": len(transaction_pool),
        }
    )


@app.route("/network", methods=["GET"])
def network_status():
    peers = sorted(network.peers)
    return jsonify(
        {
            "node_id": node_id,
            "peer_count": len(peers),
            "peers": peers,
            "connected_nodes": len(peers) + 1,
        }
    )


@app.route("/nodes/receive_block", methods=["POST"])
def receive_block():
    data = request.json or {}
    block_data = data.get("block")

    if not isinstance(block_data, dict):
        return jsonify({"error": "Missing block payload"}), 400

    block_hash = block_data.get("hash")
    if block_hash and any(existing.hash == block_hash for existing in blockchain.chain):
        _log_warn(f"Duplicate block ignored: {block_hash[:16]}...")
        return jsonify({"message": "Block already exists"}), 200

    candidate_chain = blockchain.deserialize_chain([block_data])
    if not candidate_chain:
        return jsonify({"error": "Invalid block format"}), 400

    incoming_block = candidate_chain[0]
    _log(f"Received block #{incoming_block.index} from peer")

    if blockchain.add_external_block(incoming_block):
        ledger.apply_block_transactions(incoming_block)
        _remove_confirmed_transactions(incoming_block.transactions)
        ledger.save_blockchain(blockchain)
        _emit_network_metrics()
        return jsonify({"message": "Block accepted"}), 200

    if blockchain.resolve_conflicts(network.peers, fetch_chain_fn=network.sync_chain):
        ledger.save_blockchain(blockchain)
        ledger.rebuild_from_chain(blockchain.chain)
        _remove_confirmed_transactions()
        _log("Chain synchronization completed using longest valid chain")
        _emit_network_metrics()
        return jsonify({"message": "Chain replaced via consensus"}), 200

    return jsonify({"error": "Block rejected"}), 409


@app.route("/verify", methods=["GET"])
def verify_chain():
    valid = blockchain.is_chain_valid()
    message = "Blockchain is valid" if valid else "Blockchain is invalid"
    _log("Chain validated" if valid else "Chain validation failed")
    return jsonify({"valid": valid, "message": message})


@app.route("/status", methods=["GET"])
def status():
    return {
        "message": "Quantum-Resistant Blockchain Server Running",
        "node_id": node_id,
        "blocks": len(blockchain.chain),
        "pending_transactions": len(transaction_pool),
        "peers": len(network.peers),
        "difficulty": blockchain.difficulty,
        "reward_enabled": blockchain.reward_enabled,
        "mining_reward": blockchain.mining_reward,
        "teaching_mode": DEMO_CONFIG["teaching_mode"],
        "presentation_mode": DEMO_CONFIG["presentation_mode"],
    }


@app.route("/ping", methods=["POST"])
def ping():
    data = request.json or {}
    peer_node_id = data.get("node_id", "unknown")
    _log(f"Received ping from peer node {peer_node_id}")
    return jsonify({"message": "pong", "node_id": node_id})


@app.route("/reset_network", methods=["POST"])
def reset_network():
    # Full in-place reset keeps the server process alive for presentation continuity.
    for path, empty_payload in ((ledger.filename, "[]"), (ledger.ledger_filename, "{}")):
        try:
            if os.path.exists(path):
                with open(path, "w", encoding="utf-8") as file_obj:
                    file_obj.write(empty_payload)
        except Exception as exc:
            _log_error(f"Failed resetting data file {path}: {exc}")

    transaction_pool.clear()

    blockchain.chain.clear()
    blockchain.create_genesis_block()
    ledger._ensure_ledger_file()
    ledger.save_blockchain(blockchain)
    ledger.rebuild_from_chain(blockchain.chain)
    _emit_network_metrics()
    _log("Network state reset and genesis block regenerated")

    return jsonify({"message": "Network reset successfully"})


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
