"""Generate a system architecture diagram and save it to reports/architecture.png.

Uses the `graphviz` Python package (auto-installed if missing).  The Graphviz
executables (dot, etc.) must be on PATH; if they are not, the script prints
clear installation instructions and exits without error.

Only reads; does NOT modify any existing project files.
"""

import subprocess
import sys
from pathlib import Path

REPORTS_DIR = Path(__file__).resolve().parent / "reports"


# ---------------------------------------------------------------------------
# Ensure Python graphviz package is available
# ---------------------------------------------------------------------------

def _ensure_graphviz_package() -> bool:
    try:
        import graphviz  # noqa: F401
        return True
    except ImportError:
        print("  graphviz package not found — installing…")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "graphviz"],
            capture_output=True,
        )
        return result.returncode == 0


# ---------------------------------------------------------------------------
# Build the Digraph
# ---------------------------------------------------------------------------

def build_graph():
    import graphviz

    dot = graphviz.Digraph(
        name="PQC_Blockchain_Architecture",
        comment="Post-Quantum Blockchain System Architecture",
        format="png",
    )
    dot.attr(rankdir="TB", size="14,10", dpi="150", fontname="Helvetica", bgcolor="white")
    dot.attr("node", shape="box", style="filled,rounded", fontname="Helvetica", fontsize="11")
    dot.attr("edge", fontname="Helvetica", fontsize="9", color="#555555")

    # ── Frontend Layer ───────────────────────────────────────────────────────
    with dot.subgraph(name="cluster_frontend") as c:
        c.attr(label="Frontend Layer (React / Vite)",
               style="filled", fillcolor="#dce8f7", color="#3498db")
        c.node("React Dashboard",    fillcolor="#aed6f1")
        c.node("Transaction UI",     fillcolor="#aed6f1")
        c.node("Blockchain Explorer",fillcolor="#aed6f1")

    # ── API Layer ────────────────────────────────────────────────────────────
    with dot.subgraph(name="cluster_api") as c:
        c.attr(label="API Layer (Flask + SocketIO)",
               style="filled", fillcolor="#fdebd0", color="#e67e22")
        c.node("REST Endpoints",       fillcolor="#f9c784")
        c.node("WebSocket (SocketIO)", fillcolor="#f9c784")
        c.node("Auth Middleware",      fillcolor="#f9c784")

    # ── Blockchain Core ──────────────────────────────────────────────────────
    with dot.subgraph(name="cluster_blockchain") as c:
        c.attr(label="Blockchain Core",
               style="filled", fillcolor="#d5f5e3", color="#27ae60")
        c.node("Block / Chain",    fillcolor="#a9dfbf")
        c.node("PoW Consensus",    fillcolor="#a9dfbf")
        c.node("Transaction Pool", fillcolor="#a9dfbf")
        c.node("Ledger",           fillcolor="#a9dfbf")

    # ── PQC Crypto Layer ─────────────────────────────────────────────────────
    with dot.subgraph(name="cluster_pqc") as c:
        c.attr(label="PQC Crypto Layer (pqcrypto + cryptography)",
               style="filled", fillcolor="#e8daef", color="#8e44ad")
        c.node("ML-DSA (Dilithium)",  fillcolor="#d2b4de")
        c.node("ML-KEM (Kyber512)",   fillcolor="#d2b4de")
        c.node("AES-256-GCM (Hybrid)",fillcolor="#d2b4de")

    # ── Wallet Layer ─────────────────────────────────────────────────────────
    with dot.subgraph(name="cluster_wallet") as c:
        c.attr(label="Wallet Layer",
               style="filled", fillcolor="#fef9e7", color="#f1c40f")
        c.node("Key Generation",   fillcolor="#f9e79f")
        c.node("Sign / Verify",    fillcolor="#f9e79f")
        c.node("Encrypt / Decrypt",fillcolor="#f9e79f")

    # ── Network Layer ────────────────────────────────────────────────────────
    with dot.subgraph(name="cluster_network") as c:
        c.attr(label="Network Layer (P2P Nodes)",
               style="filled", fillcolor="#fadbd8", color="#e74c3c")
        c.node("Peer Discovery",   fillcolor="#f1948a")
        c.node("Block Propagation",fillcolor="#f1948a")
        c.node("Chain Sync",       fillcolor="#f1948a")

    # ── Edges ────────────────────────────────────────────────────────────────
    # Frontend → API
    dot.edge("React Dashboard",     "REST Endpoints")
    dot.edge("Transaction UI",      "REST Endpoints")
    dot.edge("Blockchain Explorer", "REST Endpoints")
    dot.edge("React Dashboard",     "WebSocket (SocketIO)")

    # API → Core
    dot.edge("Auth Middleware",      "REST Endpoints")
    dot.edge("REST Endpoints",       "Block / Chain")
    dot.edge("REST Endpoints",       "Transaction Pool")
    dot.edge("REST Endpoints",       "Ledger")
    dot.edge("WebSocket (SocketIO)", "Block / Chain")

    # Core internal
    dot.edge("Transaction Pool", "Block / Chain")
    dot.edge("Block / Chain",    "PoW Consensus")
    dot.edge("Block / Chain",    "Ledger")

    # Core → Network
    dot.edge("Block / Chain",    "Block Propagation")
    dot.edge("PoW Consensus",    "Block Propagation")
    dot.edge("Block Propagation","Peer Discovery")
    dot.edge("Chain Sync",       "Block / Chain")

    # API → Crypto
    dot.edge("REST Endpoints",    "ML-DSA (Dilithium)")
    dot.edge("REST Endpoints",    "ML-KEM (Kyber512)")
    dot.edge("ML-KEM (Kyber512)", "AES-256-GCM (Hybrid)")

    # Wallet → Crypto
    dot.edge("Key Generation",    "ML-DSA (Dilithium)")
    dot.edge("Key Generation",    "ML-KEM (Kyber512)")
    dot.edge("Sign / Verify",     "ML-DSA (Dilithium)")
    dot.edge("Encrypt / Decrypt", "ML-KEM (Kyber512)")
    dot.edge("Encrypt / Decrypt", "AES-256-GCM (Hybrid)")

    return dot


# ---------------------------------------------------------------------------
# Matplotlib fallback renderer (no external Graphviz binaries required)
# ---------------------------------------------------------------------------

_LAYERS = [
    ("Frontend Layer",         ["React Dashboard", "Transaction UI", "Blockchain Explorer"], "#aed6f1"),
    ("API Layer",              ["REST Endpoints", "WebSocket (SocketIO)", "Auth Middleware"],  "#f9c784"),
    ("Blockchain Core",        ["Block / Chain", "PoW Consensus", "Transaction Pool", "Ledger"], "#a9dfbf"),
    ("PQC Crypto Layer",       ["ML-DSA (Dilithium)", "ML-KEM (Kyber512)", "AES-256-GCM (Hybrid)"], "#d2b4de"),
    ("Wallet Layer",           ["Key Generation", "Sign / Verify", "Encrypt / Decrypt"], "#f9e79f"),
    ("Network Layer",          ["Peer Discovery", "Block Propagation", "Chain Sync"], "#f1948a"),
]

_EDGES = [
    ("React Dashboard",       "REST Endpoints"),
    ("Transaction UI",        "REST Endpoints"),
    ("Blockchain Explorer",   "REST Endpoints"),
    ("REST Endpoints",        "Block / Chain"),
    ("REST Endpoints",        "Transaction Pool"),
    ("REST Endpoints",        "Ledger"),
    ("Block / Chain",         "PoW Consensus"),
    ("Transaction Pool",      "Block / Chain"),
    ("Block / Chain",         "Ledger"),
    ("Block / Chain",         "Block Propagation"),
    ("PoW Consensus",         "Block Propagation"),
    ("Block Propagation",     "Peer Discovery"),
    ("Chain Sync",            "Block / Chain"),
    ("REST Endpoints",        "ML-DSA (Dilithium)"),
    ("REST Endpoints",        "ML-KEM (Kyber512)"),
    ("ML-KEM (Kyber512)",     "AES-256-GCM (Hybrid)"),
    ("Key Generation",        "ML-DSA (Dilithium)"),
    ("Sign / Verify",         "ML-DSA (Dilithium)"),
    ("Encrypt / Decrypt",     "ML-KEM (Kyber512)"),
]


def _render_with_matplotlib(out_path: Path) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.patches as mpatches
        import matplotlib.pyplot as plt
    except ImportError:
        print("  matplotlib not available — skipping PNG fallback")
        return

    fig, ax = plt.subplots(figsize=(18, 10))
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 10)
    ax.axis("off")
    ax.set_facecolor("#f8f9fa")
    fig.patch.set_facecolor("#f8f9fa")

    # Build node-name → (cx, cy) map by placing layers in columns
    positions: dict[str, tuple[float, float]] = {}
    col_x = [1.5, 4.5, 7.5, 10.5, 13.5, 16.5]
    layer_colors = [row[2] for row in _LAYERS]

    for col_idx, (layer_label, nodes, color) in enumerate(_LAYERS):
        cx = col_x[col_idx]
        # Draw layer label
        ax.text(cx, 9.5, layer_label, ha="center", va="center", fontsize=7.5,
                fontweight="bold", color="#2c3e50")
        n = len(nodes)
        row_gap = min(1.8, 7.0 / max(n, 1))
        top_y = 8.5
        for node_idx, node_name in enumerate(nodes):
            cy = top_y - node_idx * row_gap
            positions[node_name] = (cx, cy)
            rect = mpatches.FancyBboxPatch(
                (cx - 1.1, cy - 0.28), 2.2, 0.56,
                boxstyle="round,pad=0.05",
                linewidth=0.8, edgecolor="#555", facecolor=color,
            )
            ax.add_patch(rect)
            ax.text(cx, cy, node_name, ha="center", va="center", fontsize=6.5,
                    color="#1a1a1a", wrap=True)

    # Draw edges as arrows
    for src, dst in _EDGES:
        if src not in positions or dst not in positions:
            continue
        x0, y0 = positions[src]
        x1, y1 = positions[dst]
        ax.annotate(
            "",
            xy=(x1, y1), xytext=(x0, y0),
            arrowprops=dict(
                arrowstyle="-|>",
                color="#888888",
                lw=0.6,
                connectionstyle="arc3,rad=0.08",
            ),
        )

    ax.set_title(
        "Post-Quantum Blockchain Wallet — System Architecture",
        fontsize=13, fontweight="bold", color="#2c3e50", pad=10,
    )

    plt.tight_layout()
    plt.savefig(str(out_path), dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  Architecture diagram (matplotlib) → {out_path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    if not _ensure_graphviz_package():
        print("ERROR: Could not install the graphviz Python package.")
        return 1

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        dot = build_graph()
        out_base = str(REPORTS_DIR / "architecture")
        dot.render(out_base, cleanup=True)
        print(f"  Architecture diagram → {out_base}.png")
        print("Architecture diagram generated.")
        return 0
    except Exception as exc:
        # Graphviz executables (dot) may not be on PATH on all machines.
        if "ExecutableNotFound" in type(exc).__name__ or "not found" in str(exc).lower():
            print(
                "\n  WARNING: Graphviz executables not found.\n"
                "  Install them from https://graphviz.org/download/ and ensure 'dot' is on PATH.\n"
                "  On Windows: winget install graphviz  OR  choco install graphviz\n"
                "  On Debian/Ubuntu: sudo apt install graphviz\n"
                "  Falling back to matplotlib renderer…"
            )
            # Save the .dot source so the user can render it manually later.
            dot_path = REPORTS_DIR / "architecture.dot"
            build_graph().save(str(dot_path))
            print(f"  DOT source saved → {dot_path}")
            # Attempt matplotlib fallback (no external binaries required)
            _render_with_matplotlib(REPORTS_DIR / "architecture.png")
            return 0
        raise


if __name__ == "__main__":
    sys.exit(main())
