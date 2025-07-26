#!/usr/bin/env python3
"""plot_entropy_arc.py

Visualise entropy for dice face probabilities.

This script produces a figure with two panels:
1. Empirical probability mass function (PMF) of the dice faces from the
   specified SQLite table (bar chart).
2. The classic binary entropy curve H(p) = -p log2 p - (1-p) log2 (1-p)
   (an "arc"), with vertical markers for each empirical probability p_i of
   a single face vs "not that face". This mirrors the arc image shown on
   Wikipedia's entropy page.

Usage:
    python plot_entropy_arc.py <table_name> [--db dice_fairness.db]

Dependencies: matplotlib, sqlite3, numpy.
"""

import argparse
import sqlite3
from collections import Counter
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import numpy as np

# --------------------------- util functions ---------------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Plot entropy arc for dice dataset")
    p.add_argument("table", help="SQLite table containing roll data")
    p.add_argument("--db", default="dice_fairness.db", help="SQLite database path")
    p.add_argument(
        "--outfile",
        default="entropy_arc.png",
        help="Output image file (default: entropy_arc.png)",
    )
    return p.parse_args()


def fetch_faces(db_path: str, table: str) -> List[int]:
    if not Path(db_path).is_file():
        raise FileNotFoundError(db_path)
    conn = sqlite3.connect(db_path)
    try:
        faces: List[int] = []
        for (result_str,) in conn.execute(f"SELECT result FROM {table}"):
            faces.extend(int(x) for x in result_str.split(",") if x)
    finally:
        conn.close()
    return faces


# ------------------------------ plotting ------------------------------------


def binary_entropy(p: np.ndarray) -> np.ndarray:
    """Vectorised binary entropy in bits."""
    with np.errstate(divide="ignore", invalid="ignore"):
        h = -(p * np.log2(p) + (1 - p) * np.log2(1 - p))
    h[np.isnan(h)] = 0.0  # handle p=0 or 1
    return h


def main() -> None:
    args = parse_args()
    faces = fetch_faces(args.db, args.table)

    # Compute empirical PMF
    total = len(faces)
    counts = Counter(faces)
    faces_sorted = sorted(counts.keys())
    probs = np.array([counts[f] / total for f in faces_sorted])

    # ----------------- create figure -----------------
    fig, (ax_pmf, ax_arc) = plt.subplots(1, 2, figsize=(10, 4))

    # Bar chart PMF
    ax_pmf.bar(faces_sorted, probs, color="skyblue")
    ax_pmf.set_xlabel("Face value")
    ax_pmf.set_ylabel("Probability")
    ax_pmf.set_title("Empirical PMF")
    ax_pmf.set_xticks(faces_sorted)
    ax_pmf.set_ylim(0, probs.max() * 1.2)

    # Binary entropy arc
    x = np.linspace(0.0, 1.0, 400)
    ax_arc.plot(x, binary_entropy(x), color="darkorange", label="H(p)")
    # Overlay markers for each p_i as binary entropy of event "face = i"
    for p in probs:
        h_val = binary_entropy(np.array([p]))[0]
        ax_arc.vlines(p, 0, h_val, colors="gray", linestyles="dotted", linewidth=1)
        ax_arc.scatter(p, h_val, color="royalblue")

    ax_arc.set_xlabel("p (success probability)")
    ax_arc.set_ylabel("Binary entropy H(p) [bits]")
    ax_arc.set_title("Binary Entropy Curve with Empirical p_i")
    ax_arc.set_xlim(0, 1)
    ax_arc.set_ylim(0, 1.1)
    ax_arc.legend()

    fig.suptitle(f"Entropy visualisation for table '{args.table}'")
    fig.tight_layout()
    fig.savefig(args.outfile, dpi=150)
    print(f"Saved plot to {args.outfile}")


if __name__ == "__main__":
    main()
