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
from matplotlib import rc

from phantom_eval import get_parser, plotting_utils
from phantom_eval.evaluate_utils import get_evaluation_data, mean, std
from phantom_eval.utils import setup_logging

setup_logging(logging.INFO)
import scipy.interpolate as interp

parser = get_parser()
parser.add_argument("--fmt_max_universe_size", type=int, default=10_000, help="Maximum universe size to plot")
args = parser.parse_args()
output_dir = args.output_dir
dataset = args.dataset
fmt_max_universe_size = args.fmt_max_universe_size
model = args.model_name
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
rc('font', **{'size': TICK_FONT_SIZE})  # Set the default font size for LaTeX text

figures_dir = os.path.join(output_dir, "figures")
figures_dir = os.path.join(output_dir, "figures")
os.makedirs(figures_dir, exist_ok=True)

# utils for plotting
plt.rcParams.update({
    'font.family': 'serif',
    # 'font.family': 'Times New Roman',
    'font.serif': ['Times New Roman'],
    # 'mathtext.fontset': 'stix',
    'axes.spines.top': False,
    'axes.spines.right': False,
    # set major tick length
    # 'xtick.major.size': 6,
    # 'ytick.major.size': 6,
    # set minor tick length
    # 'xtick.minor.size': 3,
    # 'ytick.minor.size': 3,
})

# %%
for metric in METRICS:
    fig, axs = plt.subplots(1, 3, figsize=(3.25, 1.5))

    for i, (method, method_name) in enumerate(
        [("cot", "In-Context"), ("cot-rag", "RAG"), ("react", "Agentic")]
    ):
    for i, (method, method_name) in enumerate(
        [("cot", "In-Context"), ("cot-rag", "RAG"), ("react", "Agentic")]
    ):
        # get evaluation data from the specified output directory and method subdirectory
        df = get_evaluation_data(output_dir, method, dataset)
        # import pdb; pdb.set_trace()
        df = df[df[DIFFICULTY] <= MAX_DIFFICULTY]
        print(method)
        print(df[df['_model'] == model].groupby(['_size'])['_data_seed'].agg(lambda x: list(set(x))))

        # group by model, size, data seed, and seed
        grouped = df.groupby(["_model", "_size", "_data_seed", "_seed", "difficulty"])
        grouped = df.groupby(["_model", "_size", "_data_seed", "_seed", "difficulty"])
        # logging.info the accuracy
        acc = grouped[METRICS].mean()
        # add a column that counts the number of elements in the group
        acc["count"] = grouped.size()
        acc["count"] = grouped.size()

        # get the mean and std of the accuracy for each model and split
        # first compute the mean across inference generation seeds
        acc_mean_std = acc.groupby(["_model", "_size", "_data_seed", "difficulty"]).agg("mean")
        acc_mean_std = acc.groupby(["_model", "_size", "_data_seed", "difficulty"]).agg("mean")
        # second compute the mean and standard error across data generation seeds
        acc_mean_std = acc_mean_std.groupby(["_model", "_size", "difficulty"]).agg([mean, std])
        acc_mean_std = acc_mean_std.groupby(["_model", "_size", "difficulty"]).agg([mean, std])
        acc_mean_std = acc_mean_std.reset_index()

        acc_mean_std = acc_mean_std[acc_mean_std["_model"] == model]
        acc_mean_std = acc_mean_std[acc_mean_std["_model"] == model]
        if len(acc_mean_std) == 0:
            logging.warning(f"No data for model {model}")
            continue

        # get the distinct x values
        x = acc_mean_std["_size"].astype(int).values
        x = acc_mean_std["_size"].astype(int).values
        # get the distinct y values
        y = acc_mean_std["difficulty"].values
        y = acc_mean_std["difficulty"].values
        # get the accuracy values
        z = acc_mean_std[(metric, "mean")].values
        z = acc_mean_std[(metric, "mean")].values
        # get x and y labels
        xlabels = sorted([*np.unique(x), fmt_max_universe_size])
        xticks = np.log10(xlabels)
        yticks = ylabels = np.unique(y)


        # add dummy entries to plot the out-of-context region
        X, Y = np.meshgrid(np.linspace(max(x) + 1, fmt_max_universe_size, 100), yticks)
        X, Y = np.meshgrid(np.linspace(max(x) + 1, fmt_max_universe_size, 100), yticks)
        Z = np.zeros_like(X)
        # extend the x values to the right
        x = np.append(x, X.flatten())
        y = np.append(y, Y.flatten())
        z = np.append(z, Z.flatten())

        # plot tricontourf
        contour = axs[i].tricontourf(np.log10(x), y, z, levels=40, cmap="viridis")
        contour.set_clim(0, 1)
        # Hide the contour lines
        # https://stackoverflow.com/questions/8263769/hide-contour-linestroke-on-pyplot-contourf-to-get-only-fills/32911283#32911283
        contour.set_edgecolor("face")
        if i == 2:
            # add colorbar with min=0 and max=1
            cbar = fig.colorbar(contour, ax=axs, shrink=0.2, aspect=20)
            # cbar.set_label(metric.capitalize())
            cbar.set_label("F1 Score", labelpad=0.5)
            # set tick labels to every 0.1
            cbar.set_ticks([0, 1])
            cbar.ax.set_position([0.9, 0.3, 0.05, 0.55])  # [x, y, width, height]

            cbar.set_ticks([0, 1])
            cbar.ax.set_position([0.9, 0.3, 0.05, 0.55])  # [x, y, width, height]

        # format x-axis
        xticks = [50, *plotting_utils.DEC * 100, *plotting_utils.DEC * 1000]
        xticks = [50, *plotting_utils.DEC * 100, *plotting_utils.DEC * 1000]
        # Set major and minor ticks
        major_ticks = [np.log10(x) for x in xticks if np.log10(x).is_integer()]
        minor_ticks = [np.log10(x) for x in xticks if not np.log10(x).is_integer()]
        axs[i].set_xticks(major_ticks)
        axs[i].set_xticks(minor_ticks, minor=True)
        # Set major tick labels
        axs[i].set_xticklabels(
            [f"$10^{int(np.log10(x))}$" for x in xticks if np.log10(x).is_integer()], fontsize=TICK_FONT_SIZE
        )
        axs[i].set_xticklabels(
            [f"$10^{int(np.log10(x))}$" for x in xticks if np.log10(x).is_integer()], fontsize=TICK_FONT_SIZE
        )
        # set the xlim
        axs[i].set_xlim(np.log10(50), np.log10(10000))
        # Set tick lengths
        axs[i].tick_params(axis="x", which="major", length=TICK_LENGTH)
        axs[i].tick_params(axis="x", which="minor", length=MINOR_TICK_LENGTH)
        axs[i].tick_params(axis="x", which="major", length=TICK_LENGTH)
        axs[i].tick_params(axis="x", which="minor", length=MINOR_TICK_LENGTH)

        # format y-axis
        if i == 0:
        if i == 0:
            yticks = [1, 5, 10, 15]
            axs[i].set_yticks(yticks)
            axs[i].tick_params(axis="y", which="major", length=TICK_LENGTH)
            axs[i].tick_params(axis="y", which="minor", length=MINOR_TICK_LENGTH)
            axs[i].set_yticks(range(1, MAX_DIFFICULTY + 1), minor=True)
            axs[i].tick_params(axis="y", which="major", labelsize=TICK_FONT_SIZE)
            axs[i].tick_params(axis="y", which="minor", labelsize=MINOR_TICK_LENGTH)
            axs[i].tick_params(axis="y", which="major", length=TICK_LENGTH)
            axs[i].tick_params(axis="y", which="minor", length=MINOR_TICK_LENGTH)
            axs[i].set_yticks(range(1, MAX_DIFFICULTY + 1), minor=True)
            axs[i].tick_params(axis="y", which="major", labelsize=TICK_FONT_SIZE)
            axs[i].tick_params(axis="y", which="minor", labelsize=MINOR_TICK_LENGTH)
            axs[i].set_ylim(1, MAX_DIFFICULTY)
            axs[i].set_yticklabels(yticks, fontsize=TICK_FONT_SIZE)
            # set ylabel
            axs[i].set_ylabel("Reasoning steps", fontsize=LABEL_FONT_SIZE)
            axs[i].set_ylabel("Reasoning steps", fontsize=LABEL_FONT_SIZE)
        else:
            # turn off y-axis
            axs[i].set_yticklabels([])
            # turn off spines
            axs[i].spines["left"].set_visible(False)
            axs[i].spines["left"].set_visible(False)
            # turn off all ticks
            axs[i].tick_params(axis="y", which="both", left=False, labelleft=False)

            axs[i].tick_params(axis="y", which="both", left=False, labelleft=False)

        # set title
        axs[i].set_title(method_name, fontsize=LABEL_FONT_SIZE)

        axs[i].spines["bottom"].set_position(("outward", plotting_utils.OUTWARD))  # Move x-axis outward
        axs[i].spines["left"].set_position(("outward", plotting_utils.OUTWARD))  # Move y-axis outward
        axs[i].spines["bottom"].set_position(("outward", plotting_utils.OUTWARD))  # Move x-axis outward
        axs[i].spines["left"].set_position(("outward", plotting_utils.OUTWARD))  # Move y-axis outward

    fig.tight_layout()
    fig.subplots_adjust(
        left=0.15,
        right=0.85,
        top=0.85,
        bottom=0.3,
        wspace=0.1,  # Adjust horizontal space between subplots and reduce padding to the left and right
        left=0.15,
        right=0.85,
        top=0.85,
        bottom=0.3,
        wspace=0.1,  # Adjust horizontal space between subplots and reduce padding to the left and right
    )
    # add label to the x-axis of the figure
    fig.text(0.5, 0.04, "Number of documents", ha="center", fontsize=LABEL_FONT_SIZE)
    fig.text(0.5, 0.04, "Number of documents", ha="center", fontsize=LABEL_FONT_SIZE)

    fig_path = os.path.join(figures_dir, f"size-difficulty-{metric}-{model.replace('/', '--')}.pdf")
    logging.info(f"Saving to {os.path.abspath(fig_path)}")
    fig.savefig(fig_path)

# %%
