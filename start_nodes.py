import subprocess
import sys
import time

import requests


NODES = [
    {"port": 5000, "peers": [5001]},
    {"port": 5001, "peers": [5000]},
]


def start_node(port):
    # Presentation mode enables standardized logs and demo-friendly responses.
    return subprocess.Popen([sys.executable, "main.py", "--port", str(port), "--presentation"])


def wait_for_node(port, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            response = requests.get(f"http://127.0.0.1:{port}/status", timeout=2)
            if response.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(0.5)
    return False


def register_peers(port, peers):
    payload = {"nodes": [f"http://127.0.0.1:{peer}" for peer in peers]}
    response = requests.post(
        f"http://127.0.0.1:{port}/nodes/register",
        json=payload,
        timeout=5,
    )
    response.raise_for_status()


def main():
    processes = []

    try:
        print("[START] Launching nodes 5000 and 5001 in demo mode...")
        for node in NODES:
            processes.append(start_node(node["port"]))

        for node in NODES:
            if not wait_for_node(node["port"]):
                raise RuntimeError(f"Node on port {node['port']} did not become ready")
            print(f"[READY] Node {node['port']} is up")

        for node in NODES:
            register_peers(node["port"], node["peers"])
            print(f"[PEERS] Node {node['port']} registered peers {node['peers']}")

        print("[OK] Multi-node network is running")
        print("[INFO] Press Ctrl+C to stop all nodes")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[STOP] Stopping nodes...")
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            if process.poll() is None:
                process.wait(timeout=10)
        print("[DONE] Nodes stopped")


if __name__ == "__main__":
    main()
