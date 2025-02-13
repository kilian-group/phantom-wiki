"""Script for plotting the precision and recall of the models.

Generates a plot with precision on the y-axis and recall on the x-axis.
Saves the plots to the figures directory of the output directory.

Example:
    python eval/plot_prec_recall_all_splits.py -od out --method zeroshot --depth 20
"""

# %%
import os

import matplotlib.lines as lines
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from phantom_eval import get_parser, plotting_utils
from phantom_eval.evaluate_utils import COLORS, LINESTYLES, get_evaluation_data, mean, pivot_mean_std, std

parser = get_parser()
parser.add_argument("--depth", type=int, default=20, help="Depth to plot metrics for")
args = parser.parse_args()
output_dir = args.output_dir
method = args.method
model_list = plotting_utils.DEFAULT_MODEL_LIST
dataset = args.dataset
depth = args.depth

# get evaluation data from the specified output directory and method subdirectory
df = get_evaluation_data(output_dir, method, dataset)
# filter by depth
df = df[(df["_depth"] == depth)]
# filter for questions that have >1 solutions
df = df[(df["solutions"] > 1) & (df["difficulty"] > 3)]

# %%
figures_dir = os.path.join(output_dir, "figures", method)
os.makedirs(figures_dir, exist_ok=True)

# %%
# get prec and recall by model, size, data_seed, and seed
COLS = ["_model", "_size", "_data_seed", "_seed"]
acc_by_type = df.groupby(COLS)[["precision", "recall"]].mean()

# %%
# get the mean and std of the accuracy for each model and split across seeds
# first compute the mean across inference generation seeds
acc_mean_std = acc_by_type.groupby(["_model", "_size", "_data_seed"]).agg(["mean"])
# second compute the mean and standard error across data generation seeds
acc_mean_std = acc_by_type.groupby(["_model", "_size"]).agg([mean, std])
acc_mean_std = acc_mean_std.reset_index()

# %%
# set figure size
plt.figure()

# # For each model and size, plot the precision and recall
# prec_df_mean, prec_df_std = pivot_mean_std(acc_mean_std, 'precision', independent_variable='_size')
# # Get model on rows and size on columns, numbers are recall
# rec_df_mean, rec_df_std = pivot_mean_std(acc_mean_std, 'recall', independent_variable='_size')

# Get sorted list of universe sizes
sizes_in_preds = sorted(acc_mean_std["_size"].unique().tolist())

model_name2labels: dict[str, mpatches.Patch] = {}

# Get model on rows and size on columns, numbers are precision and recall
for size in sizes_in_preds:
    acc_mean_std_size = acc_mean_std[acc_mean_std["_size"].astype(int) == size]
    prec_df_mean, prec_df_std = pivot_mean_std(acc_mean_std_size, "precision", independent_variable="_size")
    rec_df_mean, rec_df_std = pivot_mean_std(acc_mean_std_size, "recall", independent_variable="_size")

    for model_name, prec in prec_df_mean.iterrows():
        if model_name not in model_list:
            continue
        rec = rec_df_mean.loc[model_name]

        # use a line plot instead of errorbar
        # We can use the index of the size in the list to determine the color intensity
        # Higher index = higher universe size = darker color = higher alpha
        # +1 so that no intensity is 0 = transparent
        color_intensity_for_size = (sizes_in_preds.index(size) + 1) / len(sizes_in_preds)  # between 0 and 1
        # line_width_for_size = 3*((sizes_in_preds.index(size)+1) / len(sizes_in_preds))  # between 0 and 2

        # Only add label to the last plot
        plt.scatter(
            prec,
            rec,
            color=COLORS[model_name],
            alpha=color_intensity_for_size,
            s=100,
        )
        # plt.plot(
        #     x, y,
        #     color=COLORS[model_name],
        #     linestyle=LINESTYLES[model_name],
        #     alpha=color_intensity_for_size,
        #     linewidth=line_width_for_size,
        # )
        # NOTE: not plotting error bars for now because the figure looks crowded
        # yerr = df_std.loc[model_name]
        # # Change color intensity for fill to be between 0 and 0.25
        # color_intensity_for_fill = color_intensity_for_size / 4
        # plt.fill_between(x, y-yerr, y+yerr, alpha=color_intensity_for_fill, color=COLORS[model_name])

        # Add label for the model. [0], [0] are dummy values for the line
        # TODO change line to dot
        model_name2labels[model_name] = lines.Line2D(
            [0], [0], color=COLORS[model_name], label=model_name, linestyle=LINESTYLES[model_name]
        )

# Draw x=y line for reference
plt.plot([0, 1], [0, 1], color="black", linestyle=":", linewidth=2)

plt.legend(
    title="Model", loc="upper right", fontsize=12, handles=list(model_name2labels.values()), handlelength=4.0
)
# format x-axis
plt.xlim(0, 1)
plt.xlabel("Precision")
plt.xticks([0, 0.25, 0.5, 0.75, 1])

plt.ylim(0, 1)
plt.ylabel("Recall")
plt.yticks([0, 0.25, 0.5, 0.75, 1])

plt.title(f"{method}")

# plt.tight_layout()
fig_path = os.path.join(figures_dir, "precision-recall.pdf")
print(f"Saving to {os.path.abspath(fig_path)}")
plt.savefig(fig_path, bbox_inches="tight", dpi=300)
