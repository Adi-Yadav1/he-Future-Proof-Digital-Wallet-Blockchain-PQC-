"""Run stress_test.py and network_stress_test.py, parse their stdout, and export
reports/stress_results.json.  Only reads; does NOT modify any existing files.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

REPORTS_DIR = Path(__file__).resolve().parent / "reports"
PROJECT_ROOT = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# Subprocess runner
# ---------------------------------------------------------------------------

def _run_script(script_name: str) -> str:
    """Run a project script and return the combined stdout+stderr string."""
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / script_name)],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    return result.stdout + result.stderr


# ---------------------------------------------------------------------------
# Output parsers
# ---------------------------------------------------------------------------

def _parse_local_stress(output: str) -> dict:
    def _int(pattern: str):
        m = re.search(pattern, output)
        return int(m.group(1)) if m else None

    def _float(pattern: str):
        m = re.search(pattern, output)
        return float(m.group(1)) if m else None

    return {
        "transactions_processed":   _int(r"Transactions simulated:\s*(\d+)"),
        "private_transactions":     _int(r"Private transactions simulated:\s*(\d+)"),
        "blocks_mined":             _int(r"Blocks mined:\s*(\d+)"),
        "total_execution_time_s":   _float(r"Total execution time:\s*([\d.]+)"),
        "block_validation_time_s":  _float(r"Block validation time:\s*([\d.]+)"),
        "ledger_update_time_s":     _float(r"Ledger update time:\s*([\d.]+)"),
    }


def _parse_network_stress(output: str) -> dict:
    def _int(pattern: str):
        m = re.search(pattern, output)
        return int(m.group(1)) if m else None

    def _float(pattern: str):
        m = re.search(pattern, output)
        return float(m.group(1)) if m else None

    return {
        "node_a_height":        _int(r"Node A height:\s*(\d+)"),
        "node_b_height":        _int(r"Node B height:\s*(\d+)"),
        "network_sync_time_s":  _float(r"Sync time:\s*([\d.]+)"),
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> dict:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Running stress_test.py…")
    local_output = _run_script("stress_test.py")
    print(local_output.strip())
    local_data = _parse_local_stress(local_output)

    print("\nRunning network_stress_test.py (starts temporary nodes — may take ~30 s)…")
    network_output = _run_script("network_stress_test.py")
    print(network_output.strip())
    network_data = _parse_network_stress(network_output)

    report = {
        "local_stress":   local_data,
        "network_stress": network_data,
    }

    out = REPORTS_DIR / "stress_results.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\n  Exported → {out}")
    print("Stress report export complete.")
    return report


if __name__ == "__main__":
    main()
