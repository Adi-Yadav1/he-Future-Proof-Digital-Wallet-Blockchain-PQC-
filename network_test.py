import subprocess
import sys
import time

import requests

from transaction import Transaction
from wallet import Wallet


def start_node(port):
    # Start each node as its own process with independent networking state.
    return subprocess.Popen([sys.executable, "main.py", "--port", str(port)])


def wait_for_node(port, timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"http://localhost:{port}/status", timeout=2)
            if r.status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(0.5)
    raise RuntimeError(f"Node on port {port} did not become ready")


def register_peers(base_port, peers):
    payload = {"nodes": [f"http://localhost:{p}" for p in peers]}
    r = requests.post(f"http://localhost:{base_port}/nodes/register", json=payload, timeout=5)
    r.raise_for_status()


def send_transaction(port, sender_wallet, receiver_wallet, amount):
    temp_tx = Transaction(
        sender=sender_wallet.get_address(),
        receiver=receiver_wallet.get_address(),
        amount=amount,
        signature=None,
        public_key=None,
    )
    tx_hash = temp_tx.calculate_hash()
    signature = sender_wallet.sign(tx_hash)

    payload = {
        "sender": sender_wallet.get_address(),
        "receiver": receiver_wallet.get_address(),
        "amount": amount,
        "timestamp": temp_tx.timestamp,
        "signature": signature,
        "public_key": sender_wallet.public_key,
    }
    r = requests.post(f"http://localhost:{port}/add_transaction", json=payload, timeout=5)
    r.raise_for_status()


def mine_block(port):
    r = requests.post(f"http://localhost:{port}/mine", timeout=30)
    r.raise_for_status()


def fetch_chain(port):
    r = requests.get(f"http://localhost:{port}/chain", timeout=10)
    r.raise_for_status()
    return r.json()


def chains_match(ports):
    chains = [fetch_chain(port) for port in ports]
    first = chains[0]
    return all(chain == first for chain in chains)


def main():
    ports = [5000, 5001]
    processes = []

    try:
        for port in ports:
            processes.append(start_node(port))

        for port in ports:
            wait_for_node(port)

        register_peers(5000, [5001])
        register_peers(5001, [5000])

        sender_wallet = Wallet()
        receiver_wallet = Wallet()
        send_transaction(5000, sender_wallet, receiver_wallet, 7)

        # Give peers time to receive propagated transaction.
        time.sleep(1.5)

        mine_block(5000)

        # Give peers time to receive propagated block.
        time.sleep(2)

        if chains_match(ports):
            print("[PASS] Chains are synchronized across nodes")
        else:
            print("[FAIL] Chains are not synchronized")

    finally:
        for process in processes:
            process.terminate()
        for process in processes:
            process.wait(timeout=10)


if __name__ == "__main__":
    main()
