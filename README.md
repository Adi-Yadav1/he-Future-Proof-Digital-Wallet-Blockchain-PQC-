
# PQC Blockchain Wallet

Future-Proof Digital Wallet is a Python project that demonstrates a simple blockchain-backed wallet with post-quantum cryptography (PQC) primitives. It includes modules for wallets, transactions, blocks, a blockchain ledger, and basic analysis. The goal is educational: to show how a wallet, ledger, and chain can work together while swapping in PQC-friendly signing and verification.

## Features

- Wallet creation and key handling with PQC-ready interfaces
- Transaction creation, signing, and verification
- Block and blockchain assembly with persistent JSON storage
- Ledger abstraction for tracking balances and history
- Simple analysis utilities for inspecting the chain

## Project Structure

```
pqc_blockchain_wallet/
|
|-- main.py
|-- wallet.py
|-- pqc_crypto.py
|-- transaction.py
|-- block.py
|-- blockchain.py
|-- ledger.py
|-- analysis.py
|
|-- data/
|   |-- ledger.json
|   |-- blockchain.json
|
|-- README.md
|-- requirements.txt
```

## Requirements

- Python 3.9+ (recommended)
- Dependencies listed in `requirements.txt`

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Start the project from the main entry point:

```bash
python main.py
```

Depending on how `main.py` is implemented, you can create wallets, send transactions, and inspect the blockchain state. Check module docstrings and in-file comments for specific usage details.

## Data Files

- `data/ledger.json`: Stores wallet balances and transaction history.
- `data/blockchain.json`: Stores the serialized blockchain.

These files can be deleted to reset the demo state.

## Notes

- This project is intended for learning and experimentation, not production use.
- The PQC routines are abstracted in `pqc_crypto.py` so algorithms can be swapped without changing the rest of the code.

## License

Add your preferred license here.
