import hashlib
from pqc_crypto import generate_lamport_keypair, sign_message

# Maximum number of signatures allowed per Lamport key
MAX_KEY_USAGE = 1   # Lamport is a one-time signature scheme


class Wallet:
    def __init__(self):
        self.private_key = None
        self.public_key = None
        self.address = None
        self.usage_count = 0
        self._generate_new_keys()

    def _generate_new_keys(self):
        """Generate a new Lamport key pair and reset usage counter."""
        self.private_key, self.public_key = generate_lamport_keypair()
        self.address = self._generate_address()
        self.usage_count = 0

    def _generate_address(self):
        """Generate wallet address as SHA-256 hash of public key."""
        public_key_bytes = b''.join(
            pk0 + pk1 for pk0, pk1 in self.public_key
        )
        return hashlib.sha256(public_key_bytes).hexdigest()

    def sign(self, message: str):
        """
        Sign a message using Lamport private key.
        Automatically regenerates keys if usage limit is exceeded.
        """
        if self.usage_count >= MAX_KEY_USAGE:
            print("[!] Key usage limit reached. Generating new wallet keys...")
            self._generate_new_keys()

        signature = sign_message(message, self.private_key)
        self.usage_count += 1
        return signature

    def get_address(self):
        """Return wallet address."""
        return self.address


# ---------------- TEST WALLET ----------------
if __name__ == "__main__":
    wallet = Wallet()

    print("Wallet Address:")
    print(wallet.get_address())

    message = "Test Transaction"
    wallet.sign(message)

    print("Message signed successfully.")