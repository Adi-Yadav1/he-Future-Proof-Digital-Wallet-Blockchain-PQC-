import hashlib
from crypto_utils import generate_keys

class Wallet:
    def __init__(self):
        self.public_key, self.private_key = generate_keys()
        self.address = self.create_address()

    def create_address(self):
        # Convert Lamport public key (list of tuples) into bytes
        pk_bytes = b"".join(pk0 + pk1 for pk0, pk1 in self.public_key)
        return hashlib.sha256(pk_bytes).hexdigest()
