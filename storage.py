import json

def save_wallet(wallet):
    data = {
        "address": wallet.address,
        "public_key": wallet.public_key.hex(),
        "private_key": wallet.private_key.hex()
    }

    with open("wallet_data.json", "w") as f:
        json.dump(data, f)

def load_wallet():
    with open("wallet_data.json", "r") as f:
        data = json.load(f)
    return data
