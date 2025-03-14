# %%
"""Script for plotting accuracy contour curves on difficulty vs conversation length.

Generates a plot with the conversation length on the x-axis, difficulty on the y-axis,
and accuracy as the contour.  Saves the plots to the figures directory of the output
directory.

Example:
    python eval/plot_reasoning_convlen.py -od out
>>>
python eval/plot_reasoning_convlen.py -od out-v05-0222/ --filter_by_size 50 \
    --dataset kilian-group/phantom-wiki-v050 -m "meta-llama/llama-3.3-70b-instruct"
"""

import logging

# %%
import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import rc

from phantom_eval import get_parser, plotting_utils
from phantom_eval.evaluate_utils import get_evaluation_data, mean, std
from phantom_eval.utils import setup_logging

setup_logging(logging.INFO)

parser = get_parser()
parser.add_argument("--fmt_max_universe_size", type=int, default=10_000, help="Maximum universe size to plot")
parser.add_argument("--filter_by_size", type=int, default=50, help="Plot for universe size")
parser.add_argument(
    "--filter_by_metric_threshold", type=float, default=0.0, help="Filter by metric threshold"
)
args = parser.parse_args()
output_dir = args.output_dir
dataset = args.dataset
fmt_max_universe_size = args.fmt_max_universe_size
model = args.model_name
from_local = args.from_local
filter_by_size = args.filter_by_size
filter_by_metric_threshold = args.filter_by_metric_threshold
DIFFICULTY = "difficulty"
MAX_DIFFICULTY = 15
# ignore difficulty beyond 15
METRICS = [
    # 'EM',
    # 'precision',
    # 'recall',
    "f1",
]
TICK_FONT_SIZE = 8
TICK_LENGTH = 4
MINOR_TICK_LENGTH = 2
LABEL_FONT_SIZE = 10
rc("font", **{"size": TICK_FONT_SIZE})  # Set the default font size for LaTeX text

figures_dir = os.path.join(output_dir, "figures_reasoning")
os.makedirs(figures_dir, exist_ok=True)

# utils for plotting
plt.rcParams.update(
    {
        # "font.family": "serif",
        # "font.serif": ["Times New Roman"],
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)

# %%
methods = [("cot", "CoT"), ("react", "ReAct")]
for metric in METRICS:
    fig, axs = plt.subplots(1, len(methods), figsize=(10, 4))

    for i, (method, method_name) in enumerate(methods):
        if method == "cot":
            CONV_LEN = "num_tokens"
        elif method == "react":
            CONV_LEN = "num_turns"
        else:
            raise ValueError(f"Unknown method {method}")

        # get evaluation data from the specified output directory and method subdirectory
        df = get_evaluation_data(output_dir, method, dataset, from_local)
        df = df[df[DIFFICULTY] <= MAX_DIFFICULTY]
        df = df[df["_size"] == filter_by_size]

        df = df[df[metric] >= filter_by_metric_threshold]

        # Collapse num_tokens into buckets of 100
        df["num_tokens"] = df["num_tokens"].apply(lambda x: 100 * (x // 100))

        # group by model, size, data seed, and seed
        grouped = df.groupby(["_model", "_size", "_data_seed", "_seed", "difficulty", CONV_LEN])
        # logging.info the accuracy
        acc = grouped[METRICS].mean()
        # add a column that counts the number of elements in the group
        acc["count"] = grouped.size()

        # get the mean and std of the accuracy for each model and split
        # first compute the mean across inference generation seeds
        acc_mean_std = acc.groupby(["_model", "_size", "_data_seed", "difficulty", CONV_LEN]).agg("mean")
        # second compute the mean and standard error across data generation seeds
        acc_mean_std = acc_mean_std.groupby(["_model", "_size", "difficulty", CONV_LEN]).agg([mean, std])
        acc_mean_std = acc_mean_std.reset_index()

        acc_mean_std = acc_mean_std[acc_mean_std["_model"] == model]
        if len(acc_mean_std) == 0:
            logging.warning(f"No data for model {model}")
            continue

        # get the distinct x values
        x = acc_mean_std["difficulty"].values
        # get the distinct y values
        y = acc_mean_std[CONV_LEN].astype(int).values

        # get the accuracy values
        z = acc_mean_std[(metric, "mean")].values
        # get x and y labels
        xlabels = xticks = sorted(np.unique(x))
        yticks = ylabels = sorted(np.unique(y))

        # Make a scatter plot of difficulty vs conversation length with accuracy as the color
        # scatter plot of conversation length vs difficulty with accuracy as color
        scatter = axs[i].scatter(
            acc_mean_std["difficulty"],
            acc_mean_std[CONV_LEN].astype(int),
            c=acc_mean_std[(metric, "mean")],
            cmap="viridis",
            vmin=0,
            vmax=1,
            alpha=0.5,
            marker="o",
        )

        # Add a colorbar to the last subplot
        if i == len(methods) - 1:
            # add colorbar with min=0 and max=1
            cbar = fig.colorbar(scatter, ax=axs, shrink=0.2, aspect=20, ticks=[0, 0.975])
            cbar.set_label("F1 Score", labelpad=0.5)
            cbar.ax.set_yticklabels(["0", "1"])
            cbar.ax.set_position([0.9, 0.3, 0.05, 0.55])  # [x, y, width, height]

        # format x-axis
        xticks = [1, 5, 10, 15]
        axs[i].set_xticks(xticks)

        axs[i].tick_params(axis="x", which="major", length=TICK_LENGTH)
        axs[i].tick_params(axis="x", which="minor", length=MINOR_TICK_LENGTH)
        axs[i].set_xticks(range(1, MAX_DIFFICULTY + 1), minor=True)
        axs[i].tick_params(axis="x", which="major", labelsize=TICK_FONT_SIZE)
        axs[i].tick_params(axis="x", which="minor", labelsize=MINOR_TICK_LENGTH)
        axs[i].set_xlim(0, MAX_DIFFICULTY + 1)
        axs[i].set_xticklabels(xticks, fontsize=TICK_FONT_SIZE)
        # set xlabel
        axs[i].set_xlabel("Reasoning steps", fontsize=LABEL_FONT_SIZE)

        # format y-axis
        # Find the right spacing for y-ticks: get the 10^y values that are closest to the min and max of y
        # React has a maximum of 150 turns (50 max react steps * 3 thought+action+observation per step)
        # CoT has a maximum of 4000 tokens enforced by the generation config
        y_range = 150 if method == "react" else 4000
        axs[i].set_ylim(0, y_range)
        y_spacing = 10 ** np.ceil(np.log10(y_range / 4))
        major_yticks = np.arange(0, y_range + 1, y_spacing)
        minor_yticks = np.arange(0, y_range + 1, y_spacing / 2)
        # major_yticks = [y for y in yticks if y % y_spacing == 0]
        # minor_yticks = [y for y in yticks if not (y % y_spacing == 0)]
        axs[i].set_yticks(major_yticks)
        axs[i].tick_params(axis="y", which="major", length=TICK_LENGTH)
        axs[i].tick_params(axis="y", which="minor", length=MINOR_TICK_LENGTH)
        axs[i].set_yticks(minor_yticks, minor=True)
        # Set major tick labels
        axs[i].set_yticklabels(
            major_yticks,
            fontsize=TICK_FONT_SIZE,
        )
        if method == "cot":
            axs[i].set_ylabel("Number of tokens", fontsize=LABEL_FONT_SIZE)
        elif method == "react":
            axs[i].set_ylabel("Number of convo turns", fontsize=LABEL_FONT_SIZE)

        # set title
        axs[i].set_title(f"{method_name} size={filter_by_size}", fontsize=LABEL_FONT_SIZE)

        axs[i].spines["bottom"].set_position(("outward", plotting_utils.OUTWARD))  # Move x-axis outward
        axs[i].spines["left"].set_position(("outward", plotting_utils.OUTWARD))  # Move y-axis outward

    fig.tight_layout()
    fig.subplots_adjust(
        left=0.15,
        right=0.85,
        top=0.85,
        bottom=0.3,
        wspace=0.2,  # Adjust horizontal space between subplots and reduce padding to the left and right
    )
    # add label to the x-axis of the figure
    fig.text(
        0.5,
        0.04,
        f"Length of conversation, metric {metric} >= {filter_by_metric_threshold:0.2f}",
        ha="center",
        fontsize=LABEL_FONT_SIZE,
    )

    fig_path = os.path.join(
        figures_dir,
        f"convlen-difficulty-{metric}>={filter_by_metric_threshold:0.2f}"
        f"-size{filter_by_size}-{model.replace('/', '--')}.pdf",
    )
    logging.info(f"Saving to {os.path.abspath(fig_path)}")
    fig.savefig(fig_path)

# %%
