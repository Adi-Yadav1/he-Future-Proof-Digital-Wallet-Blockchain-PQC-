from transaction import create_private_transaction


def test_private_transaction_encryption(wallet_pair):
    sender, receiver = wallet_pair
    tx = create_private_transaction(sender, receiver, 25.0)

    assert tx.verify()
    assert tx.receiver == "ENCRYPTED"
    assert tx.amount == "ENCRYPTED"
    assert isinstance(tx.encrypted_payload, dict)

    decrypted = receiver.decrypt_transaction(tx)
    assert decrypted["receiver"] == receiver.get_address()
    assert float(decrypted["amount"]) == 25.0
