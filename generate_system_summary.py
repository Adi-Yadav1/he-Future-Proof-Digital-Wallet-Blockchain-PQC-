"""Generate a system summary and export it to reports/system_summary.json.

Primary strategy: query the live node at http://127.0.0.1:5000 using the
/status and /crypto_info endpoints.

Fallback strategy: read data/blockchain.json and data/ledger.json directly
when the server is not running.

Only reads; does NOT modify any existing project files.
"""

import json
from pathlib import Path

REPORTS_DIR = Path(__file__).resolve().parent / "reports"
DATA_DIR    = Path(__file__).resolve().parent / "data"
BASE_URL    = "http://127.0.0.1:5000"


# ---------------------------------------------------------------------------
# Strategy 1: live API
# ---------------------------------------------------------------------------

def _try_api() -> dict | None:
    try:
        import requests

        status = requests.get(f"{BASE_URL}/status",      timeout=3).json()
        crypto = requests.get(f"{BASE_URL}/crypto_info", timeout=3).json()

        wallet_count = None
        wallets_resp = requests.get(f"{BASE_URL}/wallets", timeout=3)
        if wallets_resp.ok:
            try:
                wallet_count = len(wallets_resp.json())
            except (ValueError, TypeError):
                pass

        transactions_resp = requests.get(f"{BASE_URL}/transactions", timeout=3)
        tx_count = None
        if transactions_resp.ok:
            try:
                tx_count = len(transactions_resp.json())
            except (ValueError, TypeError):
                pass

        return {
            "block_count":          status.get("blocks"),
            "transaction_count":    tx_count,
            "wallet_count":         wallet_count,
            "network_nodes":        status.get("peers"),
            "difficulty":           status.get("difficulty"),
            "signature_algorithm":  crypto.get("signature_algorithm"),
            "encryption_algorithm": crypto.get("encryption_algorithm"),
            "quantum_resistant":    crypto.get("quantum_resistant", True),
            "source":               "live_api",
        }
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Strategy 2: offline data files
# ---------------------------------------------------------------------------

def _from_files() -> dict:
    summary: dict = {
        "block_count":          None,
        "transaction_count":    None,
        "wallet_count":         None,
        "network_nodes":        None,
        "difficulty":           None,
        "signature_algorithm":  "ML-DSA (Dilithium2)",
        "encryption_algorithm": "ML-KEM (Kyber512)",
        "quantum_resistant":    True,
        "source":               "data_files",
    }

    chain_path = DATA_DIR / "blockchain.json"
    if chain_path.exists():
        try:
            chain = json.loads(chain_path.read_text(encoding="utf-8"))
            if isinstance(chain, list):
                summary["block_count"] = len(chain)
                summary["transaction_count"] = sum(
                    len(b.get("transactions", []))
                    for b in chain
                    if isinstance(b, dict)
                )
                if chain and isinstance(chain[-1], dict):
                    summary["difficulty"] = chain[-1].get("difficulty")
        except (json.JSONDecodeError, OSError):
            pass

    ledger_path = DATA_DIR / "ledger.json"
    if ledger_path.exists():
        try:
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            if isinstance(ledger, dict):
                summary["wallet_count"] = len(ledger)
        except (json.JSONDecodeError, OSError):
            pass

    return summary


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> dict:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Attempting to query live node at", BASE_URL, "…")
    summary = _try_api()

    if summary:
        print("  Connected to live node.")
    else:
        print("  Node not reachable — reading from data files.")
        summary = _from_files()

    out = REPORTS_DIR / "system_summary.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"  Exported → {out}")
    print("System summary generated.")
    return summary


if __name__ == "__main__":
    main()
