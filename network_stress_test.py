import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests


PORT_A = 5100
PORT_B = 5101
BASE_A = f"http://127.0.0.1:{PORT_A}"
BASE_B = f"http://127.0.0.1:{PORT_B}"
PASSWORD = "Demo@123"
PROJECT_ROOT = Path(__file__).resolve().parent
MAIN_PATH = PROJECT_ROOT / "main.py"


def wait_ready(base_url, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            response = requests.get(f"{base_url}/status", timeout=2)
            if response.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(0.5)
    return False


def start_node(port, cwd):
    # Demo mode keeps mining feasible for stress synchronization checks.
    return subprocess.Popen(
        [sys.executable, str(MAIN_PATH), "--port", str(port), "--demo"],
        cwd=cwd,
    )


def register_user(base_url, username):
    response = requests.post(
        f"{base_url}/register",
        json={"username": username, "password": PASSWORD},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def mine(base_url, miner_address):
    response = requests.post(f"{base_url}/mine", json={"miner_address": miner_address}, timeout=60)
    response.raise_for_status()


def chain_height(base_url):
    response = requests.get(f"{base_url}/chain", timeout=10)
    response.raise_for_status()
    return len(response.json())


def main():
    processes = []
    with tempfile.TemporaryDirectory() as temp_dir:
        node_a_cwd = str(Path(temp_dir) / "node_a")
        node_b_cwd = str(Path(temp_dir) / "node_b")
        Path(node_a_cwd).mkdir(parents=True, exist_ok=True)
        Path(node_b_cwd).mkdir(parents=True, exist_ok=True)
        Path(node_a_cwd, "database").mkdir(parents=True, exist_ok=True)
        Path(node_b_cwd, "database").mkdir(parents=True, exist_ok=True)

        try:
            # Each node uses a dedicated temporary cwd so data/ and database/ remain isolated.
            processes.append(start_node(PORT_A, node_a_cwd))
            processes.append(start_node(PORT_B, node_b_cwd))

            if not wait_ready(BASE_A) or not wait_ready(BASE_B):
                raise RuntimeError("Nodes did not start in time")

            requests.post(f"{BASE_A}/nodes/register", json={"nodes": [BASE_B]}, timeout=10).raise_for_status()
            requests.post(f"{BASE_B}/nodes/register", json={"nodes": [BASE_A]}, timeout=10).raise_for_status()

            suffix = int(time.time())
            user_a = register_user(BASE_A, f"net_a_{suffix}")
            user_b = register_user(BASE_B, f"net_b_{suffix}")

            for i in range(20):
                requests.post(
                    f"{BASE_A}/send_transaction",
                    json={
                        "sender": user_a["wallet_address"],
                        "receiver": user_b["wallet_address"],
                        "amount": 1 + (i % 3),
                    },
                    timeout=10,
                ).raise_for_status()

            sync_start = time.perf_counter()
            for _ in range(3):
                mine(BASE_A, user_a["wallet_address"])

            # Poll until node B catches up to node A.
            for _ in range(40):
                if chain_height(BASE_B) >= chain_height(BASE_A):
                    break
                time.sleep(0.5)

            sync_elapsed = time.perf_counter() - sync_start
            height_a = chain_height(BASE_A)
            height_b = chain_height(BASE_B)

            print("=== Network Stress Test ===")
            print(f"Node A height: {height_a}")
            print(f"Node B height: {height_b}")
            print(f"Sync time: {sync_elapsed:.4f} sec")

        finally:
            for process in processes:
                if process.poll() is None:
                    process.terminate()
            for process in processes:
                if process.poll() is None:
                    process.wait(timeout=10)


if __name__ == "__main__":
    main()
