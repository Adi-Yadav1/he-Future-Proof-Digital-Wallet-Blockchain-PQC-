from wallet import Wallet
from transaction import Transaction
from crypto_utils import sign_data, verify_signature

print("🔐 Post-Quantum Secure Wallet\n")

# Create wallet
wallet = Wallet()
print("Wallet Address:", wallet.address)

# Create transaction
tx = Transaction(wallet.address, "Bob_Address_123", 10)
tx_data = tx.to_string()

# Sign transaction
signature = sign_data(tx_data, wallet.private_key)
print("Transaction Signed.")

# Verify transaction
is_valid = verify_signature(tx_data, signature, wallet.public_key)
print("Transaction Valid:", is_valid)
