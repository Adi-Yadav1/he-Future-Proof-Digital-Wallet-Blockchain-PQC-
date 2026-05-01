import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests


PORT = 5110
BASE_URL = f"http://127.0.0.1:{PORT}"
PASSWORD = "Demo@123"
PROJECT_ROOT = Path(__file__).resolve().parent
MAIN_PATH = PROJECT_ROOT / "main.py"


def assert_ok(condition, message):
    if not condition:
        raise RuntimeError(message)


def post(path, payload):
    response = requests.post(f"{BASE_URL}{path}", json=payload, timeout=20)
    response.raise_for_status()
    return response.json()


def get(path):
    response = requests.get(f"{BASE_URL}{path}", timeout=20)
    response.raise_for_status()
    return response.json()


def wait_ready(timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            response = requests.get(f"{BASE_URL}/status", timeout=2)
            if response.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(0.5)
    return False


def main():
    with tempfile.TemporaryDirectory() as temp_dir:
        node_cwd = str(Path(temp_dir) / "validation_node")
        Path(node_cwd).mkdir(parents=True, exist_ok=True)
        Path(node_cwd, "database").mkdir(parents=True, exist_ok=True)

        process = subprocess.Popen(
            [sys.executable, str(MAIN_PATH), "--port", str(PORT), "--demo"],
            cwd=node_cwd,
        )

        try:
            assert_ok(wait_ready(), "Validation node failed to start")

            suffix = int(time.time())

            user_a = post("/register", {"username": f"val_a_{suffix}", "password": PASSWORD})
            user_b = post("/register", {"username": f"val_b_{suffix}", "password": PASSWORD})
            assert_ok("wallet_address" in user_a and "wallet_address" in user_b, "Wallet registration failed")

            tx = post(
                "/send_transaction",
                {
                    "sender": user_a["wallet_address"],
                    "receiver": user_b["wallet_address"],
                    "amount": 10,
                },
            )
            assert_ok(tx.get("message") in {"Transaction added", "Duplicate transaction ignored"}, "Transaction failed")

            ptx = post(
                "/private_transaction",
                {
                    "sender_wallet": user_a["wallet_address"],
                    "receiver_wallet": user_b["wallet_address"],
                    "amount": 7,
                },
            )
            assert_ok(ptx.get("encrypted") is True, "Private transaction encryption failed")

            mined = post("/mine", {"miner_address": user_a["wallet_address"]})
            assert_ok("block" in mined, "Mining did not return block")

            verify = get("/verify")
            assert_ok(bool(verify.get("valid")), "Blockchain verification failed")

            print("Demo system status: OK")
        finally:
            if process.poll() is None:
                process.terminate()
            if process.poll() is None:
                process.wait(timeout=10)


if __name__ == "__main__":
    main()
