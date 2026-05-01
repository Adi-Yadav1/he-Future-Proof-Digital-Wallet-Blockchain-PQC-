import time

import requests


BASE_A = "http://127.0.0.1:5000"
BASE_B = "http://127.0.0.1:5001"
PASSWORD = "Demo@123"


def register_user(base_url, username):
    response = requests.post(
        f"{base_url}/register",
        json={"username": username, "password": PASSWORD},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def send_transaction(base_url, sender, receiver, amount):
    response = requests.post(
        f"{base_url}/send_transaction",
        json={"sender": sender, "receiver": receiver, "amount": amount},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def mine(base_url, miner_address):
    response = requests.post(
        f"{base_url}/mine",
        json={"miner_address": miner_address},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def get_chain(base_url):
    response = requests.get(f"{base_url}/chain", timeout=10)
    response.raise_for_status()
    return response.json()


def get_balance(base_url, wallet):
    response = requests.get(f"{base_url}/balance/{wallet}", timeout=10)
    response.raise_for_status()
    return response.json().get("balance")


def main():
    suffix = int(time.time())
    user_a = register_user(BASE_A, f"nodeA_user_{suffix}")
    user_b = register_user(BASE_B, f"nodeB_user_{suffix}")

    wallet_a = user_a["wallet_address"]
    wallet_b = user_b["wallet_address"]

    print(f"[USER] Node A wallet: {wallet_a}")
    print(f"[USER] Node B wallet: {wallet_b}")

    tx_result = send_transaction(BASE_A, wallet_a, wallet_b, 125)
    print(f"[TX] Transaction hash: {tx_result.get('tx_hash')}")

    mined = mine(BASE_A, wallet_a)
    block = mined.get("block", {})
    print(f"[MINE] Block #{block.get('index')} mined on node 5000")
    print(f"[MINE] Miner node id: {block.get('miner_node_id')}")

    time.sleep(2)

    chain_a = get_chain(BASE_A)
    chain_b = get_chain(BASE_B)
    synced = chain_a == chain_b
    print(f"[SYNC] Chain synchronized across nodes: {synced}")
    print(f"[SYNC] Node 5000 height: {len(chain_a)}")
    print(f"[SYNC] Node 5001 height: {len(chain_b)}")

    balance_a = get_balance(BASE_A, wallet_a)
    balance_b = get_balance(BASE_B, wallet_b)
    print(f"[BALANCE] Wallet A: {balance_a}")
    print(f"[BALANCE] Wallet B: {balance_b}")


if __name__ == "__main__":
    main()
