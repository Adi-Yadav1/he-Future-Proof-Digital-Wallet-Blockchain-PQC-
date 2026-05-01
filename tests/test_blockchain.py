import requests

from network import NodeNetwork
from transaction import Transaction


class DummyResponse:
    def raise_for_status(self):
        return None


def _signed_tx(sender_wallet, receiver_wallet, amount):
    draft = Transaction(
        sender=sender_wallet.get_address(),
        receiver=receiver_wallet.get_address(),
        amount=amount,
        signature=None,
        public_key=None,
    )
    signature = sender_wallet.sign(draft.calculate_hash())
    return Transaction(
        sender=draft.sender,
        receiver=draft.receiver,
        amount=draft.amount,
        signature=signature,
        public_key=sender_wallet.public_key,
        timestamp=draft.timestamp,
    )


def test_block_creation(temp_blockchain, wallet_pair):
    sender, receiver = wallet_pair
    tx = _signed_tx(sender, receiver, 10)
    block = temp_blockchain.add_block([tx], sender)
    assert block.index == 1
    assert block.transactions


def test_proof_of_work_validation(temp_blockchain, wallet_pair):
    sender, receiver = wallet_pair
    tx = _signed_tx(sender, receiver, 10)
    block = temp_blockchain.add_block([tx], sender)
    assert block.hash.startswith("0" * temp_blockchain.difficulty)


def test_chain_verification(temp_blockchain, wallet_pair):
    sender, receiver = wallet_pair
    tx = _signed_tx(sender, receiver, 10)
    temp_blockchain.add_block([tx], sender)
    assert temp_blockchain.is_chain_valid()


def test_peer_registration():
    network = NodeNetwork("node-a")
    network.register_peer("http://127.0.0.1:5001")
    assert network.has_peer("http://127.0.0.1:5001")


def test_block_propagation_logic_mocked(monkeypatch):
    posted_urls = []

    def fake_post(url, json, timeout):
        posted_urls.append(url)
        return DummyResponse()

    monkeypatch.setattr(requests, "post", fake_post)

    network = NodeNetwork("node-a")
    network.register_peer("http://127.0.0.1:5001")
    network.broadcast_block({"index": 1, "hash": "abc"})

    assert posted_urls == ["http://127.0.0.1:5001/nodes/receive_block"]
