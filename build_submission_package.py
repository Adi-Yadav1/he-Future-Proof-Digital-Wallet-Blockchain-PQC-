"""Build a clean submission package.

Copies source code, tests, reports, README, and requirements.txt into a
submission/ directory, then compresses everything into:

    submission/pqc_blockchain_project.zip

Only reads project files; does NOT modify any existing source or data files.
"""

import shutil
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SUBMISSION_DIR = PROJECT_ROOT / "submission"
ZIP_PATH = SUBMISSION_DIR / "pqc_blockchain_project.zip"

# ── What to include ──────────────────────────────────────────────────────────

# Top-level file globs collected from PROJECT_ROOT
TOP_LEVEL_GLOBS = ["*.py", "*.md", "requirements.txt"]

# Subdirectories collected recursively
INCLUDE_DIRS = ["tests", "reports", "frontend"]

# Directory / file names to skip wherever they appear in the tree
EXCLUDE_NAMES = {
    "__pycache__",
    ".venv",
    ".git",
    ".idea",
    ".vscode",
    "submission",   # avoid recursion
    "node_modules",
    "dist",
    "build",
    ".pytest_cache",
    "*.pyc",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _should_exclude(rel_path: Path) -> bool:
    """Return True if any part of the relative path matches an exclusion name."""
    for part in rel_path.parts:
        if part in EXCLUDE_NAMES or part.startswith("."):
            return True
        # Handle glob-style exclusions (e.g. "*.pyc")
        for excl in EXCLUDE_NAMES:
            if "*" in excl:
                suffix = excl.lstrip("*")
                if part.endswith(suffix):
                    return True
    return False


def collect_files() -> list[Path]:
    files: list[Path] = []

    # Top-level files matching the given glob patterns
    for pattern in TOP_LEVEL_GLOBS:
        for p in PROJECT_ROOT.glob(pattern):
            if p.is_file():
                rel = p.relative_to(PROJECT_ROOT)
                if not _should_exclude(rel):
                    files.append(p)

    # Subdirectories (recursive)
    for dir_name in INCLUDE_DIRS:
        dir_path = PROJECT_ROOT / dir_name
        if dir_path.is_dir():
            for p in dir_path.rglob("*"):
                if p.is_file():
                    rel = p.relative_to(PROJECT_ROOT)
                    if not _should_exclude(rel):
                        files.append(p)

    return sorted(set(files))


# ---------------------------------------------------------------------------
# Package builder
# ---------------------------------------------------------------------------

def build_package() -> None:
    SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)

    files = collect_files()
    print(f"  Collecting {len(files)} file(s)…")

    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in files:
            arcname = file_path.relative_to(PROJECT_ROOT)
            zf.write(file_path, arcname)
            print(f"    + {arcname}")

    size_kb = ZIP_PATH.stat().st_size / 1024
    print(f"\n  Package created : {ZIP_PATH}")
    print(f"  Compressed size : {size_kb:.1f} KB")
    print(f"  Files included  : {len(files)}")
    print("Submission package build complete.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    build_package()


if __name__ == "__main__":
    main()
