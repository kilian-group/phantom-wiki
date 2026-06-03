"""Aggregate Harbor run results into PhantomWiki F1-vs-difficulty diagnostics.

After ``harbor run``, each PhantomWiki task writes ``/logs/verifier/result.json`` (one row
with the question's ``difficulty`` and ``type`` and its EM/precision/recall/F1). This
script collects those rows from a Harbor run output directory and produces:

  - ``summary.csv``               -- one row per question
  - ``metric_vs_difficulty.png``  -- EM/precision/recall/F1 vs difficulty
  - ``f1_by_type.png``            -- mean F1 per question type

The grouping mirrors ``eval/plot_difficulty_accuracy.py``. Point ``--run-dir`` at the
directory Harbor wrote the run's logs to (the script searches it recursively for
``result.json`` files).

Example:
    python harbor/diagnostics/plot_difficulty.py --run-dir ~/.harbor/runs/<run-id> \\
        --out-dir harbor/diagnostics/figures
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

METRICS = ["EM", "precision", "recall", "f1"]


def collect_results(run_dir: str | Path, filename: str = "result.json") -> pd.DataFrame:
    """Load every ``result.json`` under ``run_dir`` into a DataFrame."""
    rows = []
    for path in Path(run_dir).rglob(filename):
        try:
            rows.append(json.loads(path.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    if not rows:
        raise SystemExit(f"No {filename} files found under {run_dir}")
    df = pd.DataFrame(rows)
    return df.dropna(subset=["difficulty"])


def plot_metric_vs_difficulty(df: pd.DataFrame, out_dir: Path) -> Path:
    grouped = df.groupby("difficulty")[METRICS].agg(["mean", "sem"])
    x = grouped.index.values

    plt.figure(figsize=(9, 6))
    for metric in METRICS:
        y = grouped[(metric, "mean")].to_numpy()
        yerr = grouped[(metric, "sem")].fillna(0).to_numpy()
        plt.errorbar(x, y, yerr=yerr, marker="o", capsize=3, label=metric)
    plt.xlabel("Question difficulty")
    plt.ylabel("Score")
    plt.ylim(0, 1.02)
    plt.title("PhantomWiki: accuracy vs difficulty")
    plt.legend(title="Metric")
    plt.grid(alpha=0.3)
    plt.tight_layout()

    path = out_dir / "metric_vs_difficulty.png"
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def plot_f1_by_type(df: pd.DataFrame, out_dir: Path) -> Path | None:
    if "type" not in df.columns or df["type"].isna().all():
        return None
    by_type = df.groupby("type")["f1"].mean().sort_index()

    plt.figure(figsize=(10, 5))
    plt.bar(by_type.index.astype(str), by_type.to_numpy())
    plt.xlabel("Question type")
    plt.ylabel("Mean F1")
    plt.ylim(0, 1.02)
    plt.title("PhantomWiki: mean F1 by question type")
    plt.tight_layout()

    path = out_dir / "f1_by_type.png"
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Plot PhantomWiki F1-vs-difficulty diagnostics.")
    parser.add_argument("--run-dir", required=True, help="Harbor run output directory to search.")
    parser.add_argument("--out-dir", default="harbor/diagnostics/figures", help="Where to write outputs.")
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = collect_results(args.run_dir)
    csv_path = out_dir / "summary.csv"
    df.to_csv(csv_path, index=False)

    overall = df["f1"].mean()
    print(f"Collected {len(df)} graded questions. Mean F1 = {overall:.3f}")
    print(f"  wrote {csv_path}")
    print(f"  wrote {plot_metric_vs_difficulty(df, out_dir)}")
    type_plot = plot_f1_by_type(df, out_dir)
    if type_plot is not None:
        print(f"  wrote {type_plot}")


if __name__ == "__main__":
    main()
