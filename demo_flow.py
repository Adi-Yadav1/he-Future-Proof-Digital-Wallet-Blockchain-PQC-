import time

import requests


BASE_URL = "http://127.0.0.1:5000"


def register_user(username, password):
    response = requests.post(
        f"{BASE_URL}/register",
        json={"username": username, "password": password},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def send_transaction(sender, receiver, amount, user_id):
    response = requests.post(
        f"{BASE_URL}/send_transaction",
        json={
            "sender": sender,
            "receiver": receiver,
            "amount": amount,
            "user_id": user_id,
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def send_private_transaction(sender, receiver, amount):
    response = requests.post(
        f"{BASE_URL}/private_transaction",
        json={
            "sender_wallet": sender,
            "receiver_wallet": receiver,
            "amount": amount,
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def mine_block(user_id):
    response = requests.post(
        f"{BASE_URL}/mine",
        json={"user_id": user_id},
        headers={"X-User-ID": str(user_id)},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def get_balance(address):
    response = requests.get(f"{BASE_URL}/balance/{address}", timeout=10)
    response.raise_for_status()
    return response.json()["balance"]


def main():
    suffix = int(time.time())
    user1 = f"alice_{suffix}@demo.com"
    user2 = f"bob_{suffix}@demo.com"
    password = "Demo@123"

    print("\n=== PQC Blockchain Demo Flow ===")
    print("1) Registering users...")
    reg1 = register_user(user1, password)
    reg2 = register_user(user2, password)
    print(f"   - User1 wallet: {reg1['wallet_address']}")
    print(f"   - User2 wallet: {reg2['wallet_address']}")

    print("2) Sending transaction (120 PQC from user1 to user2)...")
    tx_result = send_transaction(
        sender=reg1["wallet_address"],
        receiver=reg2["wallet_address"],
        amount=120,
        user_id=reg1["user_id"],
    )
    print(f"   - Transaction status: {tx_result['message']}")

    print("3) Creating private transaction (35 PQC, encrypted payload)...")
    private_result = send_private_transaction(
        sender=reg1["wallet_address"],
        receiver=reg2["wallet_address"],
        amount=35,
    )
    print("   - Encrypted transaction stored on blockchain.")
    print(f"   - Private tx hash: {private_result.get('tx_hash', 'N/A')}")

    print("4) Mining block with user1 as miner...")
    mine_result = mine_block(reg1["user_id"])
    print(f"   - Block mined: {mine_result['hash'][:16]}...")

    print("5) Verifying blockchain...")
    verify = requests.get(f"{BASE_URL}/verify", timeout=10)
    verify.raise_for_status()
    verify_json = verify.json()
    print(f"   - Validation: {verify_json.get('message')} (valid={verify_json.get('valid')})")

    print("6) Fetching balances...")
    balance1 = get_balance(reg1["wallet_address"])
    balance2 = get_balance(reg2["wallet_address"])
    print(f"   - User1 balance: {balance1}")
    print(f"   - User2 balance: {balance2}")

    print("\nDemo complete.")


if __name__ == "__main__":
    main()
