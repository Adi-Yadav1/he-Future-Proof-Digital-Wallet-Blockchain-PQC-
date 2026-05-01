from wallet import Wallet


def test_wallet_keypair_generation():
    wallet = Wallet()
    assert wallet.private_key
    assert wallet.public_key


def test_wallet_address_generation():
    wallet = Wallet()
    assert isinstance(wallet.get_address(), str)
    assert len(wallet.get_address()) == 64


def test_wallet_encryption_key_availability():
    wallet = Wallet()
    assert wallet.encryption_private_key
    assert wallet.get_encryption_public_key()
