#!/usr/bin/env python3
"""entropy_test.py

Simple Shannon entropy test for dice roll datasets stored in the local
SQLite database created by the other roll_* scripts.

Usage:
    python entropy_test.py <table_name> [--db dice_fairness.db]

Example:
    python entropy_test.py large_fast_rolls

The script will:
1. Connect to the SQLite DB (default: dice_fairness.db).
2. Read every entry in the specified table, assuming a column `result` that
   contains comma-separated dice face integers (e.g. "4,2,6").
3. Flatten all dice faces into a single list and compute the Shannon entropy
   in bits.
4. Print an easy-to-read report comparing the measured entropy to the ideal
   entropy for a fair die (log2(6) ≈ 2.585 bits).

If the computed entropy is close to the ideal (within ~1-2%), the dataset can
be considered high-entropy with respect to uniform dice faces. Larger
relative deviation may indicate bias.
"""
import argparse
import math
import sqlite3
from collections import Counter
from pathlib import Path
from typing import List

IDEAL_ENTROPY_BITS = math.log2(6)  # ≈ 2.585


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Shannon entropy test for dice datasets.")
    parser.add_argument("table", help="SQLite table name containing roll data")
    parser.add_argument(
        "--db",
        default="dice_fairness.db",
        help="Path to SQLite database file (default: dice_fairness.db)",
    )
    return parser.parse_args()


def fetch_results(db_path: str, table: str) -> List[int]:
    """Fetch and flatten dice faces from the specified table."""
    if not Path(db_path).is_file():
        raise FileNotFoundError(f"Database file '{db_path}' does not exist.")

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(f"SELECT result FROM {table}")
        faces: List[int] = []
        for (result_str,) in cur:
            # Each result is comma-separated (e.g., "3,5,1")
            faces.extend(int(x) for x in result_str.split(",") if x)
        return faces
    finally:
        conn.close()


def shannon_entropy(values: List[int]) -> float:
    """Compute Shannon entropy in bits for discrete values."""
    count = Counter(values)
    total = len(values)
    if total == 0:
        raise ValueError("No data to compute entropy.")

    entropy = 0.0
    for freq in count.values():
        p = freq / total
        entropy -= p * math.log2(p)
    return entropy


def main() -> None:
    args = parse_args()
    values = fetch_results(args.db, args.table)

    entropy = shannon_entropy(values)
    deviation_pct = (entropy - IDEAL_ENTROPY_BITS) / IDEAL_ENTROPY_BITS * 100

    print("\nEntropy Analysis Report")
    print("=======================")
    print(f"Dataset table     : {args.table}")
    print(f"Total dice faces  : {len(values):,}")
    print(f"Unique faces      : {len(set(values))}")
    print(f"Shannon entropy   : {entropy:.4f} bits")
    print(f"Ideal entropy (d6): {IDEAL_ENTROPY_BITS:.4f} bits")
    print(f"Deviation         : {deviation_pct:+.2f}%")

    if abs(deviation_pct) <= 2:
        verdict = "PASS (entropy within ±2% of ideal)"
    elif abs(deviation_pct) <= 5:
        verdict = "WARNING (entropy moderately deviates)"
    else:
        verdict = "FAIL (entropy significantly deviates)"

    print(f"Verdict           : {verdict}\n")


if __name__ == "__main__":
    main()
