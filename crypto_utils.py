import os
import hashlib

HASH_SIZE = 32  # 256-bit hashes

def generate_keys():
    private_key = [(os.urandom(HASH_SIZE), os.urandom(HASH_SIZE)) for _ in range(256)]
    public_key = [
        (hashlib.sha256(k0).digest(), hashlib.sha256(k1).digest())
        for k0, k1 in private_key
    ]
    return public_key, private_key

def sign_data(message, private_key):
    message_hash = hashlib.sha256(message.encode()).digest()
    signature = []

    for i, bit in enumerate(message_hash):
        for j in range(8):
            bit_value = (bit >> j) & 1
            signature.append(private_key[i * 8 + j][bit_value])

    return signature

def verify_signature(message, signature, public_key):
    message_hash = hashlib.sha256(message.encode()).digest()
    index = 0

    for i, bit in enumerate(message_hash):
        for j in range(8):
            bit_value = (bit >> j) & 1
            expected_hash = public_key[i * 8 + j][bit_value]
            if hashlib.sha256(signature[index]).digest() != expected_hash:
                return False
            index += 1

    return True
