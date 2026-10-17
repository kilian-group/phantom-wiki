"""Plot sampling method complexity from benchmark results.

Usage:
    python scripts/benchmark_sampling_methods.py --sizes 50,500,5000 --output scripts/benchmark_results.csv
    python scripts/plot_sampling_complexity.py

Reads: scripts/benchmark_results.csv
Outputs: scripts/sampling_complexity.png
"""

import argparse
import csv
import os
import sys
from collections import defaultdict

try:
    import matplotlib.pyplot as plt
except ImportError:
    print("matplotlib required: pip install matplotlib")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Plot sampling complexity")
    parser.add_argument("--input", type=str, default="scripts/benchmark_results.csv",
                        help="Input CSV from benchmark script")
    parser.add_argument("--output", type=str, default="scripts/sampling_complexity.png",
                        help="Output plot path")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Benchmark results not found at {args.input}")
        print("Run: python scripts/benchmark_sampling_methods.py first")
        sys.exit(1)

    data = defaultdict(lambda: {"n": [], "per_q_ms": []})
    with open(args.input) as f:
        reader = csv.DictReader(f)
        for row in reader:
            method = row["method"]
            data[method]["n"].append(int(row["n"]))
            data[method]["per_q_ms"].append(float(row["per_q_ms"]))

    fig, ax = plt.subplots(figsize=(8, 5))

    markers = {"backward": "o", "bidirectional_prolog": "s"}
    colors = {"backward": "#2196F3", "bidirectional_prolog": "#FF5722"}

    for method, vals in sorted(data.items()):
        ax.plot(
            vals["n"], vals["per_q_ms"],
            marker=markers.get(method, "^"),
            color=colors.get(method, "#666"),
            label=method,
            linewidth=2,
            markersize=8,
        )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Universe size (n)", fontsize=12)
    ax.set_ylabel("Per-question time (ms)", fontsize=12)
    ax.set_title("Sampling Method Scaling", fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(args.output, dpi=150)
    print(f"Plot saved to {args.output}")


if __name__ == "__main__":
    main()
