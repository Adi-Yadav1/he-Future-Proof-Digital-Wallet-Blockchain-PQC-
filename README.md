
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

## Multi-Node Network

This project now supports running multiple blockchain nodes with:

- peer registration and discovery
- transaction propagation
- block propagation
- Proof-of-Work mining
- longest-chain conflict resolution

### Start Multiple Nodes

Node 1:

```bash
python main.py --port 5000
```

Node 2:

```bash
python main.py --port 5001
```

### Register Peers

Register node 5001 on node 5000:

```bash
curl -X POST http://localhost:5000/nodes/register \
	-H "Content-Type: application/json" \
	-d "{\"nodes\":[\"http://localhost:5001\"]}"
```

Check known peers:

```bash
curl http://localhost:5000/nodes
```

### Mining Across Nodes

1. Submit transactions to any node using `POST /add_transaction`.
2. Mine a block using `POST /mine` on one node.
3. The mined block is broadcast to peers.
4. Peers validate PoW and Dilithium signatures before appending.
5. If chains diverge, nodes apply longest valid chain rule.

### Integration Test

Run the included network script:

```bash
python network_test.py
```

The script starts two nodes, registers peers, sends a signed transaction,
mines a block, and checks that chains are synchronized.

## Notes

- This project is intended for learning and experimentation, not production use.
- The PQC routines are abstracted in `pqc_crypto.py` so algorithms can be swapped without changing the rest of the code.

## Deployment and Local Run Guide

### Environment Variables

- Frontend (`PQC_frontend/.env.local`):
	- `VITE_API_BASE_URL=http://127.0.0.1:5000` for local dev
	- Use deployed backend URL in production

### Run Locally

1. Backend:
```bash
pip install -r requirements.txt
python main.py --port 5000 --presentation
```

2. Frontend:
```bash
cd PQC_frontend
npm install
npm run dev
```

3. Open frontend at `http://127.0.0.1:5173`.

### Frontend Production Deploy

```bash
cd PQC_frontend
npm run build
```

Deploy `PQC_frontend/dist/` to static hosting and configure SPA route fallback to `index.html`.

### Backend Production Deploy

- Deploy Python app with `requirements.txt`.
- Expose the same API contracts currently consumed by frontend.
- Configure CORS to allow frontend domain.

## Live Demo Instructions

This demo showcases post-quantum signatures with **ML-DSA (Dilithium2)** using the `pqcrypto` library.

1. Reset demo data:

```bash
python reset_demo.py
```

2. Start backend (demo mode):

```bash
python main.py --port 5000 --demo
```

3. Start frontend:

```bash
cd PQC_frontend
npm install
npm run dev
```

4. Register two users in the UI (each starts with 1000 PQC).

5. Send transaction from one wallet to another.

6. Mine a block to confirm transactions and issue miner reward (50 PQC).

7. Verify chain integrity:

```bash
curl http://localhost:5000/verify
```

8. Show cryptography proof endpoint:

```bash
curl http://localhost:5000/crypto_info
```

9. Optional scripted walkthrough:

```bash
python demo_flow.py
```

Useful demo endpoints:

- `GET /explorer`
- `GET /demo_stats`
- `GET /blocks`
- `GET /balance/<wallet_address>`
- `GET /transactions/<wallet_address>`
- `GET /crypto_info`

## Multi-Node Blockchain Demo

This flow is intended for classroom-style demonstrations where two nodes share one network and visibly synchronize.

1. Reset local state:

```bash
python reset_demo.py
```

2. Start two nodes and auto-register peers:

```bash
python start_nodes.py
```

3. In another terminal, run scripted network demo:

```bash
python network_demo.py
```

4. Verify node and network visibility endpoints:

```bash
curl http://127.0.0.1:5000/node_info
curl http://127.0.0.1:5000/network
curl http://127.0.0.1:5001/node_info
curl http://127.0.0.1:5001/network
```

5. Open frontend and navigate to the Network page to show:

- local node identity
- connected peers
- local block height
- latest block miner node attribution

6. Open Explorer page and show `Miner Node` column in block history.

## Presentation Mode

Use this mode for classroom delivery with standardized node logs, simplified demo responses, and auto metrics emission.

1. Start both backend nodes:

```bash
python start_nodes.py
```

2. Start frontend:

```bash
cd PQC_frontend
npm run dev
```

3. Open dashboard in the browser:

```text
http://127.0.0.1:5173/dashboard
```

4. Open Demo Control panel and run:

- Reset Network
- Simulate Transactions
- Mine Block
- Run Demo Script

5. Open Network page to show live node health, peer count, block height, and pending transactions.

6. Optional manual node startup:

```bash
python main.py --port 5000 --presentation
python main.py --port 5001 --presentation
```

## Private Transactions with Post-Quantum Encryption

This project now supports optional private transactions while keeping normal transactions as the default path.

- Dilithium (ML-DSA) is used to sign and verify transaction integrity.
- Kyber/ML-KEM (ML-KEM 512) is used to encrypt sensitive payload fields for the receiver.

### How It Works

1. Sender prepares private payload containing `receiver` and `amount`.
2. Payload is encrypted with receiver ML-KEM public key + AES-GCM hybrid encryption.
3. Blockchain stores masked transaction fields (`receiver`, `amount`) and encrypted payload.
4. Dilithium signature still verifies transaction authenticity.
5. Receiver can decrypt payload using their ML-KEM private key via:

```bash
curl "http://127.0.0.1:5000/decrypt_transaction/<tx_hash>?receiver_wallet=<wallet_address>"
```

### Private Transaction Endpoint

```bash
curl -X POST http://127.0.0.1:5000/private_transaction \
	-H "Content-Type: application/json" \
	-d "{\"sender_wallet\":\"<sender>\",\"receiver_wallet\":\"<receiver>\",\"amount\":25}"
```

The response includes confirmation and transaction hash, while explorer views show encrypted receiver/amount fields.

## Testing and Validation

Use these commands to validate correctness, stress behavior, and benchmark performance without altering core API behavior.

Run automated tests:

```bash
pytest
```

Optional coverage report:

```bash
pytest --cov=.
```

Run performance benchmark suite:

```bash
python benchmark_performance.py
```

Run local blockchain stress test:

```bash
python stress_test.py
```

Run network synchronization stress test:

```bash
python network_stress_test.py
```

This script launches temporary isolated nodes and does not modify the persistent demo chain files.

Run security validation checks:

```bash
python security_checks.py
```

Run end-to-end demo validator (requires backend running on port 5000):

```bash
python validate_demo.py
```

This validator starts an isolated temporary node automatically and prints `Demo system status: OK` on success.

## Why Post-Quantum Cryptography?

Traditional blockchain systems often rely on ECDSA signatures. ECDSA security depends on
the hardness of the discrete logarithm problem. A sufficiently capable quantum computer
running Shor's algorithm can solve that problem efficiently, which means exposed public keys
can eventually lead to private-key recovery and forged transactions.

### Classical Blockchain Risk

- Public keys are visible on-chain and over the network.
- If private keys are derived from those public keys, signatures can be forged.
- Forged signatures undermine wallet ownership and transaction integrity.

### Quantum Computing Threat

- Shor's algorithm threatens RSA and ECC-based cryptography.
- ECDSA is ECC-based, so long-term blockchain signatures become vulnerable.
- This is a systemic risk for public ledgers with long-lived data and assets.

### How Dilithium and Kyber Help

- **Dilithium (ML-DSA)** replaces ECDSA for digital signatures using lattice-based hardness.
- **Kyber (ML-KEM)** enables quantum-resistant key encapsulation for encrypted private transactions.
- Together, they preserve authenticity and confidentiality under known quantum threat models.

### Educational Demonstration Commands

```bash
python simulate_classical_crypto.py
python simulate_quantum_attack.py
python compare_crypto_systems.py
python final_demo_presentation.py
```

To enable narrated educational logs in the running node:

```bash
python main.py --demo --teaching
```

## Generating Research Reports

A research reporting toolkit generates experiment results, architecture artifacts, and a
submission-ready PDF for academic documentation and presentation.

### Run the full pipeline at once

```bash
python generate_full_report.py
```

This runs pytest, all benchmarks, stress tests, security checks, and every export
script, saving all outputs under `reports/`.

### Generate the PDF report

```bash
python generate_report_pdf.py
```

Requires `reportlab` (auto-installed if missing).  Reads the JSON files in `reports/`
and produces `reports/project_report.pdf` with sections covering introduction,
system architecture, cryptography, blockchain implementation, benchmark results,
stress test results, security validation, and conclusion.

### Build the submission ZIP

```bash
python build_submission_package.py
```

Creates `submission/pqc_blockchain_project.zip` containing source code, tests,
reports, README, and `requirements.txt`.

### Run individual export scripts

| Script | Output |
|--------|--------|
| `python export_benchmark_report.py` | `reports/benchmark_results.json`, `reports/benchmark_results.csv` |
| `python export_stress_report.py` | `reports/stress_results.json` |
| `python export_security_report.py` | `reports/security_report.json` |
| `python generate_architecture_diagram.py` | `reports/architecture.png` |
| `python generate_system_summary.py` | `reports/system_summary.json` |

> **Note:** `generate_architecture_diagram.py` requires the Graphviz executables on
> PATH in addition to the `graphviz` Python package.  Install with:
>
> - Windows: `winget install graphviz` or `choco install graphviz`
> - Debian/Ubuntu: `sudo apt install graphviz`
>
> If Graphviz executables are not found, a `.dot` source file is saved to `reports/`
> instead so you can render it manually.

> **Note:** `generate_system_summary.py` first attempts to query the live node at
> `http://127.0.0.1:5000`.  If the server is not running it falls back to reading
> `data/blockchain.json` and `data/ledger.json` directly.

## License

Add your preferred license here.
