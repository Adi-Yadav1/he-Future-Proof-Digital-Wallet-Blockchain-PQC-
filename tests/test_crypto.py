from pqc_crypto import (
    decrypt_message,
    encrypt_message,
    generate_kem_keypair,
    sign_message,
    verify_signature,
)


def test_dilithium_sign_verify(wallet_pair):
    sender, _ = wallet_pair
    message = "quantum-safe-message"
    signature = sign_message(message, sender.private_key)
    assert verify_signature(message, signature, sender.public_key)


def test_kyber_encrypt_decrypt():
    private_key, public_key = generate_kem_keypair()
    payload = {"receiver": "wallet-address", "amount": 42.0}
    encrypted = encrypt_message(public_key, payload)
    decrypted = decrypt_message(private_key, encrypted)
    assert decrypted == payload


def test_aes_gcm_payload_correctness():
    private_key, public_key = generate_kem_keypair()
    payload = "authenticated payload"
    encrypted = encrypt_message(public_key, payload)
    decrypted = decrypt_message(private_key, encrypted)
    assert decrypted == payload
