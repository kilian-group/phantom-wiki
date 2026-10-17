import argparse
import glob
import json
import random
import textwrap

import matplotlib.pyplot as plt

HOPS_VALUES = [0, 1, 2, 3, 4, 5, 6]
CONSTR_VALUES = [0, 1, 2, 3]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("data_dir", help="Dataset directory containing questions/*.json")
    p.add_argument("--out", default=None, help="Output PNG path (default: <data_dir>/question_grid.png)")
    p.add_argument("--seed", type=int, default=0, help="Random seed for per-cell sampling")
    args = p.parse_args()

    out_path = args.out or f"{args.data_dir}/question_grid.png"
    rng = random.Random(args.seed)

    all_by_cell = {}
    for f in sorted(glob.glob(f"{args.data_dir}/questions/*.json")):
        for q in json.load(open(f)):
            if q.get("is_aggregation_question"):
                continue
            key = (q["difficulty"]["hops"], q["difficulty"]["constraints"])
            if key[0] in HOPS_VALUES and key[1] in CONSTR_VALUES:
                all_by_cell.setdefault(key, []).append(q)

    examples = {key: rng.choice(qs) for key, qs in all_by_cell.items()}

    n_rows = len(HOPS_VALUES)
    n_cols = len(CONSTR_VALUES)
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(4 * n_cols, 2.3 * n_rows))

    for i, h in enumerate(HOPS_VALUES):
        for j, c in enumerate(CONSTR_VALUES):
            ax = axes[i][j]
            ax.set_xticks([])
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_edgecolor("#888")
            q = examples.get((h, c))
            if q is None:
                ax.text(0.5, 0.5, "(no example)", ha="center", va="center",
                        fontsize=11, color="#aaa", style="italic",
                        transform=ax.transAxes)
                ax.set_facecolor("#f6f6f6")
            else:
                wrapped = "\n".join(textwrap.wrap(q["question"], width=40))
                ax.text(0.5, 0.55, wrapped, ha="center", va="center",
                        fontsize=10, transform=ax.transAxes)
                n_ans = len(q["answer"])
                n_cell = len(all_by_cell.get((h, c), []))
                ax.text(0.5, 0.12, f"count: {n_cell}   answers: {n_ans}   type: {q['type']}",
                        ha="center", va="center", fontsize=8, color="#666",
                        transform=ax.transAxes)
            if i == 0:
                ax.set_title(f"{c} constraint{'s' if c != 1 else ''}",
                             fontsize=12, pad=8)
            if j == 0:
                ax.set_ylabel(f"{h} hop{'s' if h != 1 else ''}",
                              fontsize=12, rotation=90, labelpad=10)

    fig.suptitle(f"Question examples by (hops × constraints) — {args.data_dir}",
                 fontsize=13, y=0.995)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    print("wrote", out_path)


if __name__ == "__main__":
    main()
