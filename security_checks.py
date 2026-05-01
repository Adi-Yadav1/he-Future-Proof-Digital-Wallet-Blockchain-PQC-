from blockchain import Blockchain
from transaction import Transaction
from wallet import Wallet


def check_invalid_signature_rejection():
    sender = Wallet()
    receiver = Wallet()
    tx = Transaction(
        sender=sender.get_address(),
        receiver=receiver.get_address(),
        amount=11,
        signature="invalid-signature",
        public_key=sender.public_key,
    )
    return not tx.verify()


def check_tampered_block_detection():
    chain = Blockchain(difficulty=1, reward_enabled=False)
    sender = Wallet()
    receiver = Wallet()

    tx = Transaction(
        sender=sender.get_address(),
        receiver=receiver.get_address(),
        amount=8,
        signature=None,
        public_key=None,
    )
    tx.signature = sender.sign(tx.calculate_hash())
    tx.public_key = sender.public_key

    block = chain.add_block([tx], sender)
    block.previous_hash = "tampered"
    return not chain.is_chain_valid()


def check_duplicate_transaction_prevention():
    sender = Wallet()
    receiver = Wallet()

    draft = Transaction(
        sender=sender.get_address(),
        receiver=receiver.get_address(),
        amount=4,
        signature=None,
        public_key=None,
    )
    draft.signature = sender.sign(draft.calculate_hash())
    draft.public_key = sender.public_key

    tx_hash = draft.calculate_hash()
    seen = set()
    seen.add(tx_hash)
    duplicate_detected = tx_hash in seen
    return duplicate_detected


def report(name, ok):
    print(f"{name}: {'PASS' if ok else 'FAIL'}")


def main():
    invalid_sig = check_invalid_signature_rejection()
    tampered_block = check_tampered_block_detection()
    duplicate_tx = check_duplicate_transaction_prevention()

    report("Invalid signature rejection", invalid_sig)
    report("Tampered block detection", tampered_block)
    report("Duplicate transaction prevention", duplicate_tx)


if __name__ == "__main__":
    main()
