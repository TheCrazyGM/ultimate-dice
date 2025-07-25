import dataset
import matplotlib.pyplot as plt
import numpy as np

DB_URL = "sqlite:///dice_fairness.db"
TABLES = [
    ("fast_rolls", "Fast Rolls"),
    ("slow_rolls", "Slow Rolls"),
    ("large_fast_rolls", "Large Fast Rolls"),
]

def extract_results(table):
    results = []
    for row in table.all():
        # 'result' is a comma-separated string of ints (e.g., "4" or "3,6")
        if row.get("result"):
            nums = [int(x) for x in str(row["result"]).split(",") if x.strip().isdigit()]
            # If multiple dice, sum for total; else just value
            results.append(sum(nums))
    return results

def plot_histogram(results, label, filename):
    if not results:
        print(f"No data for {label}")
        return
    # Theoretical 3d6 distribution (sum of 3d6, values 3-18)
    theoretical_counts = {
        3: 1, 4: 3, 5: 6, 6: 10, 7: 15, 8: 21, 9: 25, 10: 27, 11: 27, 12: 25, 13: 21, 14: 15, 15: 10, 16: 6, 17: 3, 18: 1
    }
    total_permutations = 6 ** 3  # 216
    theoretical_probs = {k: v / total_permutations for k, v in theoretical_counts.items()}
    xs = np.arange(3, 19)
    # Empirical histogram
    plt.figure(figsize=(10, 6))
    n, bins, patches = plt.hist(results, bins=np.arange(2.5, 19.5, 1), edgecolor='black', alpha=0.7, label='Empirical')
    # Theoretical curve (scaled to match sample size)
    sample_size = len(results)
    theoretical_freqs = [theoretical_probs.get(x, 0) * sample_size for x in xs]
    plt.plot(xs, theoretical_freqs, 'o-', color='red', label='Theoretical 3d6', linewidth=2)
    plt.title(f"Dice Roll Distribution: {label}")
    plt.xlabel("Total Roll Value (3d6)")
    plt.ylabel("Frequency")
    plt.grid(axis='y', alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    print(f"Saved plot: {filename}")

def main():
    db = dataset.connect(DB_URL)
    for table_name, label in TABLES:
        table = db[table_name]
        results = extract_results(table)
        plot_histogram(results, label, f"{table_name}_hist.png")

if __name__ == "__main__":
    main()
