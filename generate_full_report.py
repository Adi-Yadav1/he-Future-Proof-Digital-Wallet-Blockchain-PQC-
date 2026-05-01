"""Master report-generation script.

Runs the full validation and reporting pipeline in sequence:

    1.  pytest test suite
    2.  benchmark_performance.py          (display-only, no file output)
    3.  stress_test.py                    (display-only, no file output)
    4.  security_checks.py               (display-only, no file output)
    5.  export_benchmark_report.py        → reports/benchmark_results.{json,csv}
    6.  export_stress_report.py           → reports/stress_results.json
    7.  export_security_report.py         → reports/security_report.json
    8.  generate_architecture_diagram.py  → reports/architecture.png
    9.  generate_system_summary.py        → reports/system_summary.json

All outputs are placed under reports/.
Does NOT modify any existing source files or endpoints.
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
REPORTS_DIR  = PROJECT_ROOT / "reports"
PYTHON       = sys.executable

# ---------------------------------------------------------------------------
# Step definitions  (label, command-args)
# ---------------------------------------------------------------------------

STEPS = [
    ("pytest test suite",              [PYTHON, "-m", "pytest", "-q"]),
    ("benchmark_performance.py",       [PYTHON, "benchmark_performance.py"]),
    ("stress_test.py",                 [PYTHON, "stress_test.py"]),
    ("security_checks.py",             [PYTHON, "security_checks.py"]),
    ("export_benchmark_report.py",     [PYTHON, "export_benchmark_report.py"]),
    ("export_stress_report.py",        [PYTHON, "export_stress_report.py"]),
    ("export_security_report.py",      [PYTHON, "export_security_report.py"]),
    ("generate_architecture_diagram.py",[PYTHON, "generate_architecture_diagram.py"]),
    ("generate_system_summary.py",     [PYTHON, "generate_system_summary.py"]),
]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def _divider(char: str = "─", width: int = 62) -> str:
    return char * width


def run_step(label: str, args: list) -> bool:
    print(f"\n{_divider()}")
    print(f"  Step: {label}")
    print(_divider())

    result = subprocess.run(args, cwd=str(PROJECT_ROOT))
    ok = result.returncode == 0

    if ok:
        print(f"  → OK")
    else:
        print(f"  → FAILED (exit code {result.returncode})")
    return ok


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    print(_divider("="))
    print("  Post-Quantum Blockchain — Full Report Generation")
    print(_divider("="))

    outcomes: dict[str, bool] = {}
    for label, args in STEPS:
        outcomes[label] = run_step(label, args)

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"\n{_divider('=')}")
    print("  Pipeline Summary")
    print(_divider("="))
    all_ok = True
    for label, ok in outcomes.items():
        tag = "OK    " if ok else "FAILED"
        print(f"  [{tag}] {label}")
        if not ok:
            all_ok = False

    print(_divider("="))
    print(f"  All reports saved to: {REPORTS_DIR}")
    if all_ok:
        print("  All steps completed successfully.")
    else:
        print("  One or more steps failed — review the output above.")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
