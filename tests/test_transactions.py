from transaction import Transaction


def _build_signed_transaction(sender_wallet, receiver_wallet, amount):
    draft = Transaction(
        sender=sender_wallet.get_address(),
        receiver=receiver_wallet.get_address(),
        amount=amount,
        signature=None,
        public_key=None,
    )
    tx_hash = draft.calculate_hash()
    signature = sender_wallet.sign(tx_hash)
    return Transaction(
        sender=draft.sender,
        receiver=draft.receiver,
        amount=draft.amount,
        signature=signature,
        public_key=sender_wallet.public_key,
        timestamp=draft.timestamp,
    )


def test_valid_transaction_verification(wallet_pair):
    sender, receiver = wallet_pair
    tx = _build_signed_transaction(sender, receiver, 12.5)
    assert tx.verify()


def test_invalid_signature_rejection(wallet_pair):
    sender, receiver = wallet_pair
    tx = _build_signed_transaction(sender, receiver, 12.5)
    tx.signature = "corrupted-signature"
    assert not tx.verify()
