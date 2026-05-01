"""Run security checks and export results to reports/security_report.json.

Imports check functions directly from security_checks.py — no subprocess required.
Only reads system state; does NOT modify any existing files.
"""

import json
from pathlib import Path

REPORTS_DIR = Path(__file__).resolve().parent / "reports"


def main() -> dict:
    from security_checks import (
        check_duplicate_transaction_prevention,
        check_invalid_signature_rejection,
        check_tampered_block_detection,
    )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    checks = {
        "invalid_signature_test":  check_invalid_signature_rejection(),
        "tampered_block_test":     check_tampered_block_detection(),
        "duplicate_tx_test":       check_duplicate_transaction_prevention(),
    }

    report = {name: "PASS" if result else "FAIL" for name, result in checks.items()}
    report["overall"] = "PASS" if all(checks.values()) else "FAIL"

    for name, status in report.items():
        print(f"  {name}: {status}")

    out = REPORTS_DIR / "security_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"  Exported → {out}")
    print("Security report export complete.")
    return report


if __name__ == "__main__":
    main()
