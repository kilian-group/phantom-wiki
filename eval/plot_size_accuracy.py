"""Script for plotting the accuracy of the models versus the universe size.

Generates a plot for each metric (EM, precision, recall, f1) with the universe size on the x-axis and the
metric on the y-axis.
Saves the plots to the figures directory of the output directory.

Example:
    python eval/plot_size_accuracy.py -od out --method zeroshot
"""

# %%
import os

import matplotlib.pyplot as plt
import numpy as np

from phantom_eval import get_parser
from phantom_eval.evaluate_utils import (
    COLORS,
    LINESTYLES,
    MARKERS,
    get_evaluation_data,
    mean,
    pivot_mean_std,
    std,
)

parser = get_parser()
args = parser.parse_args()
output_dir = args.output_dir
method = args.method
dataset = args.dataset
# get evaluation data from the specified output directory and method subdirectory
df = get_evaluation_data(output_dir, method, dataset)

# %%
# group by model, size, data seed, and inference seed
grouped = df.groupby(["_model", "_size", "_data_seed", "_seed"])
# print the accuracy
acc = grouped[["EM", "precision", "recall", "f1"]].mean()
# add a column that counts the number of elements in the group
acc["count"] = grouped.size()

# %%
# get the mean and std of the accuracy for each model and split as follows:
# first compute the mean across inference generation seeds
acc_mean_std = acc.groupby(["_model", "_size", "_data_seed"]).agg("mean")
# second compute the mean and standard error across data generation seeds
acc_mean_std = acc_mean_std.groupby(["_model", "_size"]).agg([mean, std])
acc_mean_std = acc_mean_std.reset_index()

figures_dir = os.path.join(output_dir, "figures", method)
os.makedirs(figures_dir, exist_ok=True)

# %%
for metric in ["EM", "precision", "recall", "f1"]:
    df_mean, df_std = pivot_mean_std(acc_mean_std, metric, independent_variable="_size")

    plt.figure(figsize=(15, 8))
    # use log2 scale for the x-axis
    x = np.log2(df_mean.columns)
    for i, row in df_mean.iterrows():
        y = row
        yerr = df_std.loc[i]
        # plt.errorbar(x, y, yerr=yerr, label=i, marker='o')
        # use a line plot instead of errorbar
        plt.plot(x, y, label=i, marker=MARKERS[method], color=COLORS[i], linestyle=LINESTYLES[i])
        plt.fill_between(x, y - yerr, y + yerr, alpha=0.3, color=COLORS[i])

    plt.legend(title="Model", loc="upper right", fontsize=12)
    # format x-axis
    plt.xlabel("Size of universe")
    plt.xticks(x, df_mean.columns)
    plt.ylabel(metric)
    plt.ylim(0, 1)
    plt.tight_layout()
    fig_path = os.path.join(figures_dir, f"size-{metric}.pdf")
    print(f"Saving to {os.path.abspath(fig_path)}")
    plt.savefig(fig_path)
