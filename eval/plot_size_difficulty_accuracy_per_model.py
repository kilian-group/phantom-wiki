# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     custom_cell_magics: kql
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.11.2
#   kernelspec:
#     display_name: dataset
#     language: python
#     name: python3
# ---

# %%
"""Script for plotting accuracy contour curves on difficulty vs universe size.

Generates a plot with the universe size on the x-axis, difficulty on the y-axis, and accuracy as the contour.
Saves the plots to the figures directory of the output directory.

Example:
    python eval/plot_size_difficulty_accuracy_per_model.py -od out  --method react
"""

import logging

# %%
import os

import matplotlib.pyplot as plt
import numpy as np

from phantom_eval import get_parser
from phantom_eval.evaluate_utils import get_evaluation_data, mean, std
from phantom_eval.utils import setup_logging

setup_logging(logging.INFO)

parser = get_parser()
parser.add_argument("--fmt_max_universe_size", type=int, default=10_000, help="Maximum universe size to plot")
args = parser.parse_args()
output_dir = args.output_dir
method = args.method
dataset = args.dataset
fmt_max_universe_size = args.fmt_max_universe_size
# get evaluation data from the specified output directory and method subdirectory
df = get_evaluation_data(output_dir, method, dataset)
DIFFICULTY = "difficulty"
MAX_DIFFICULTY = 15
# ignore difficulty beyond 15
df = df[df[DIFFICULTY] <= MAX_DIFFICULTY]
METRICS = [
    # 'EM',
    # 'precision',
    # 'recall',
    "f1",
]

# %%
# group by model, size, data seed, and seed
grouped = df.groupby(["_model", "_size", "_data_seed", "_seed", "difficulty"])
# logging.info the accuracy
acc = grouped[METRICS].mean()
# add a column that counts the number of elements in the group
acc["count"] = grouped.size()

# %%
# get the mean and std of the accuracy for each model and split
# first compute the mean across inference generation seeds
acc_mean_std = acc.groupby(["_model", "_size", "_data_seed", "difficulty"]).agg("mean")
# second compute the mean and standard error across data generation seeds
acc_mean_std = acc_mean_std.groupby(["_model", "_size", "difficulty"]).agg([mean, std])
acc_mean_std = acc_mean_std.reset_index()
# get all unique models
models = acc_mean_std["_model"].unique()
logging.info(f"Models: {models}")

figures_dir = os.path.join(output_dir, "figures", method)
os.makedirs(figures_dir, exist_ok=True)

# %%
for metric in METRICS:
    for model in models:
        # create a new figure for each data seed, metric, and model
        fig, ax = plt.subplots(figsize=(15, 8))
        acc_mean_std_data_seed = acc_mean_std[acc_mean_std["_model"] == model]
        if len(acc_mean_std_data_seed) == 0:
            logging.warning(f"No data for model {model}")
            continue

        # get the distinct x values
        x = acc_mean_std_data_seed["_size"].astype(int).values
        # get the distinct y values
        y = acc_mean_std_data_seed["difficulty"].values
        # get the accuracy values
        z = acc_mean_std_data_seed[(metric, "mean")].values
        # get x and y labels
        xlabels = sorted([*np.unique(x), fmt_max_universe_size])
        xticks = np.log2(xlabels)
        yticks = ylabels = np.unique(y)

        # add dummy entries to plot the out-of-context region
        X, Y = np.meshgrid(np.linspace(max(x) + 1, fmt_max_universe_size, 100), yticks)
        Z = np.zeros_like(X)
        # extend the x values to the right
        x = np.append(x, X.flatten())
        y = np.append(y, Y.flatten())
        z = np.append(z, Z.flatten())

        # plot tricontourf
        contour = ax.tricontourf(np.log2(x), y, z, levels=20, cmap="viridis")
        contour.set_clim(0, 1)
        # add colorbar with min=0 and max=1
        cbar = fig.colorbar(contour)
        cbar.set_label(metric)

        # format x-axis
        ax.set_xlabel("Universe size")
        ax.set_xticks(xticks)
        ax.set_xticklabels(xlabels)
        # format y-axis
        ax.set_ylabel("Difficulty")
        ax.set_yticks(yticks)
        ax.set_yticklabels(ylabels)
        fig.tight_layout()
        fig_path = os.path.join(figures_dir, f"size-difficulty-{metric}-{model.replace('/', '--')}.pdf")
        logging.info(f"Saving to {os.path.abspath(fig_path)}")
        fig.savefig(fig_path)
        # plt.show()

# %%
