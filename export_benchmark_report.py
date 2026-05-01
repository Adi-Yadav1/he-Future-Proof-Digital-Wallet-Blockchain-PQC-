"""Export benchmark results to reports/benchmark_results.json and reports/benchmark_results.csv.

Imports benchmark functions directly from benchmark_performance.py, so no subprocess
or output-parsing is required.  Only reads; does NOT modify any existing files.
"""

import csv
import json
from pathlib import Path

REPORTS_DIR = Path(__file__).resolve().parent / "reports"


# ---------------------------------------------------------------------------
# Run benchmarks
# ---------------------------------------------------------------------------

def run_benchmarks() -> dict:
    from benchmark_performance import (
        benchmark_blockchain,
        benchmark_dilithium,
        benchmark_kyber,
    )

    results: dict = {}
    results.update(benchmark_dilithium())
    results.update(benchmark_kyber())
    results.update(benchmark_blockchain())
    return results


# ---------------------------------------------------------------------------
# Reshape raw results into the canonical export schema
# ---------------------------------------------------------------------------

def flatten_for_export(results: dict) -> dict:
    dil = results.get("Dilithium", {})
    kyber = results.get("Kyber", {})
    bc = results.get("Blockchain", {})

    return {
        "Dilithium": {
            "keygen_ms":  round(dil.get("Key Generation", 0.0), 4),
            "sign_ms":    round(dil.get("Signing",        0.0), 4),
            "verify_ms":  round(dil.get("Verification",   0.0), 4),
        },
        "Kyber": {
            "encapsulation_ms": round(kyber.get("Encapsulation", 0.0), 4),
            "decapsulation_ms": round(kyber.get("Decapsulation", 0.0), 4),
            "encrypt_ms":       round(kyber.get("Encryption",    0.0), 4),
            "decrypt_ms":       round(kyber.get("Decryption",    0.0), 4),
        },
        "Blockchain": {
            "block_mining_ms":      round(bc.get("Block Mining",          0.0), 4),
            "tx_verify_avg_ms":     round(bc.get("Tx Verify Avg",         0.0), 4),
            "tx_verify_throughput": round(bc.get("Tx Verify Throughput",  0.0), 2),
        },
    }


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def export_json(data: dict, path: Path) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"  Exported JSON → {path}")


def export_csv(data: dict, path: Path) -> None:
    rows = [
        {"algorithm": algo, "metric": metric, "value": value}
        for algo, metrics in data.items()
        for metric, value in metrics.items()
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["algorithm", "metric", "value"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Exported CSV  → {path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> dict:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Running benchmarks (100 iterations each)…")
    raw = run_benchmarks()
    flat = flatten_for_export(raw)

    export_json(flat, REPORTS_DIR / "benchmark_results.json")
    export_csv(flat,  REPORTS_DIR / "benchmark_results.csv")

    print("Benchmark export complete.")
    return flat


if __name__ == "__main__":
    main()
