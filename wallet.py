import hashlib
from pqc_crypto import decrypt_message, generate_kem_keypair, generate_keypair, sign_message


class Wallet:
    def __init__(
        self,
        private_key=None,
        public_key=None,
        encryption_private_key=None,
        encryption_public_key=None,
    ):
        self.private_key = private_key
        self.public_key = public_key
        self.encryption_private_key = encryption_private_key
        self.encryption_public_key = encryption_public_key
        self.address = None

        if self.private_key and self.public_key and self.encryption_private_key and self.encryption_public_key:
            self.address = self._generate_address()
        else:
            self._generate_new_keys()

    def _generate_new_keys(self):
        """Generate reusable key pairs for signatures (Dilithium) and encryption (ML-KEM)."""
        self.private_key, self.public_key = generate_keypair()
        self.encryption_private_key, self.encryption_public_key = generate_kem_keypair()
        self.address = self._generate_address()

    def _generate_address(self):
        """Generate wallet address as SHA-256 hash of public key."""
        public_key_bytes = self.public_key.encode("utf-8")
        return hashlib.sha256(public_key_bytes).hexdigest()

    def sign(self, message: str):
        """Sign a message using Dilithium private key."""
        return sign_message(message, self.private_key)

    def get_encryption_public_key(self):
        """Return wallet public key for ML-KEM encryption."""
        return self.encryption_public_key

    def decrypt_payload(self, ciphertext):
        """Decrypt an encrypted payload using this wallet's ML-KEM private key."""
        return decrypt_message(self.encryption_private_key, ciphertext)

    def decrypt_transaction(self, tx):
        """
        Decrypt a private transaction payload and return cleartext fields.
        Returns None if transaction is not encrypted.
        """
        if not getattr(tx, "encrypted_payload", None):
            return None
        return self.decrypt_payload(tx.encrypted_payload)

    def get_address(self):
        """Return wallet address."""
        return self.address

    @classmethod
    def from_serialized_keys(
        cls,
        *,
        private_key,
        public_key,
        encryption_private_key,
        encryption_public_key,
    ):
        """Rebuild wallet identity from stored key material for server-side operations."""
        return cls(
            private_key=private_key,
            public_key=public_key,
            encryption_private_key=encryption_private_key,
            encryption_public_key=encryption_public_key,
        )


# ---------------- TEST WALLET ----------------
if __name__ == "__main__":
    wallet = Wallet()

    print("Wallet Address:")
    print(wallet.get_address())

    message = "Test Transaction"
    wallet.sign(message)

    print("Message signed successfully.")