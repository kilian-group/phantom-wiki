"""Script for plotting the accuracy of the models versus the difficulty for all splits.

Generates a plot for each metric (EM, precision, recall, f1) with the difficulty on the x-axis and the metric
on the y-axis.
Saves the plots to the figures directory of the output directory.

Example usage:
```bash
python eval/plot_reasoning.py -od out --filter_by_depth 20 --model_list meta-llama/llama-3.3-70b-instruct
```
"""

import logging

# %%
import os
import random

import matplotlib.lines as lines
import matplotlib.pyplot as plt

from phantom_eval import get_parser, plotting_utils
from phantom_eval.evaluate_utils import get_evaluation_data, mean, pivot_mean_std, std
from phantom_eval.utils import setup_logging

setup_logging("INFO")

# utils for plotting
plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Times New Roman"],
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


parser = get_parser()
parser.add_argument("--filter_by_depth", type=int, default=20, help="Depth to plot accuracies for")
parser.add_argument(
    "--filter_by_num_solutions", type=int, default=None, help="Number of solutions to filter by"
)
parser.add_argument(
    "--model_list", nargs="+", default=plotting_utils.DEFAULT_MODEL_LIST, help="List of models to plot"
)
parser.add_argument("--seed", type=int, default=42, help="Random seed for color generation")
args = parser.parse_args()
output_dir = args.output_dir
model_list = args.model_list
dataset = args.dataset
filter_by_depth = args.filter_by_depth
from_local = args.from_local
seed = args.seed

figures_dir = os.path.join(output_dir, "figures")
os.makedirs(figures_dir, exist_ok=True)
METRICS = [
    # 'EM',
    # 'precision',
    # 'recall',
    "f1",
]
# Difficulty can either be 'difficulty' (i.e., reasoning steps) or 'solutions' (i.e., number of solutions to
# the questions)
MAX_DIFFICULTY = 15
DIFFICULTY = "difficulty"

random.seed(seed)


def random_rgb_color():
    """Generate a random RGB color tuple."""
    return (random.random(), random.random(), random.random())


COLORS = {}


def get_color(model, method, by_model=True):
    if by_model:
        model_name = model.lower()
        if model_name in plotting_utils.COLORS:
            return plotting_utils.COLORS[model_name]
        else:
            if model_name not in COLORS:
                COLORS[model_name] = random_rgb_color()
            return COLORS[model_name]
    else:
        match method.lower():
            case "selfask":
                color = "tab:blue"
            case "ircot":
                color = "tab:green"
            case "sft":
                color = "tab:blue"
            case "grpo":
                color = "tab:green"
            case "zeroshot":
                color = "tab:red"
            case "cot":
                color = "tab:red"
            case _:
                color = "black"
        return color


METHOD_LIST = [
    ("In-Context", plotting_utils.INCONTEXT_METHODS),
    ("RAG", plotting_utils.RAG_METHODS),
    ("Agentic", plotting_utils.AGENTIC_METHODS),
]

for metric in METRICS:
    # fig = plt.figure(figsize=(3.25, 2.75)) # exact dimensions of ICML single column width
    # replace this with a subplot figure with 1 rows and 3 columns
    fig_width = max(2.25 * len(METHOD_LIST), 3.25)
    fig, axs = plt.subplots(1, len(METHOD_LIST), figsize=(fig_width, 2.5))

    for i, (name, methods) in enumerate(METHOD_LIST):
        method_handles = {}
        ax = axs[i] if len(METHOD_LIST) > 1 else axs
        for method in methods:
            print(f"Plotting {method} for {metric}")
            # get evaluation data from the specified output directory and method subdirectory
            df = get_evaluation_data(output_dir, method, dataset, from_local)
            if df.empty:
                print(f"No data found for {method}")
                continue

            # ignore difficulty beyond 15
            df = df[df[DIFFICULTY] <= MAX_DIFFICULTY]

            if args.filter_by_num_solutions is not None:
                logging.warning(f"Filtering out {method} with more than 1 solution")
                df = df[df["solutions"] <= args.filter_by_num_solutions]

            # filter by depth
            df = df[(df["_depth"] == filter_by_depth)]

            # get accuracies by model, split, difficulty, seed
            COLS = ["_model", "_size", "_data_seed", "_seed", DIFFICULTY]
            acc_by_type = df.groupby(COLS)[METRICS].mean()

            # get the mean and std of the accuracy for each model, split, and difficulty across seeds
            # first compute the mean across inference generation seeds
            acc_mean_std = acc_by_type.groupby(["_model", "_size", "_data_seed", DIFFICULTY]).agg("mean")
            # second compute the mean and standard error across data generation seeds
            acc_mean_std = acc_mean_std.groupby(["_model", "_size", DIFFICULTY]).agg([mean, std])
            acc_mean_std = acc_mean_std.reset_index()

            # Get sorted list of universe sizes
            sizes_in_preds = sorted(acc_mean_std["_size"].unique().tolist())
            # only plot the minimum size
            sizes_in_preds = [min(sizes_in_preds)]

            for size in sizes_in_preds:
                acc_mean_std_size = acc_mean_std[acc_mean_std["_size"].astype(int) == size]
                df_mean, df_std = pivot_mean_std(
                    acc_mean_std_size, metric, independent_variable=DIFFICULTY, enforce_order=False
                )
                x = df_mean.columns
                for model_name, row in df_mean.iterrows():
                    if model_name.lower() not in map(str.lower, model_list):
                        continue
                    y = row
                    color = get_color(model_name, method)
                    ax.plot(
                        x,
                        y,
                        color=color,
                        # NOTE: determine the linestyle using the method
                        linestyle=plotting_utils.METHOD_LINESTYLES.get(method.lower(), "solid"),
                        linewidth=1,
                        alpha=plotting_utils.LINE_ALPHA,
                    )
                    # Add scatter plot
                    ax.scatter(
                        x,
                        y,
                        color=color,
                        s=plotting_utils.MARKER_SIZE,  # marker size
                        alpha=plotting_utils.MARKER_ALPHA,
                        clip_on=False,
                    )

                    # Add error bars
                    yerr = df_std.loc[model_name]
                    # Change color intensity for fill to be between 0 and 0.25
                    color_intensity_for_fill = 0.1
                    ax.fill_between(
                        x,
                        y - yerr,
                        y + yerr,
                        alpha=color_intensity_for_fill,
                        color=color,
                    )

            # Add method to legend
            key = f"{plotting_utils.METHOD_ALIASES.get(method.lower(), method)}"
            if key not in method_handles:
                method_handles[key] = lines.Line2D(
                    [0],
                    [0],
                    color=get_color(None, method, by_model=False),
                    label=key,
                    linestyle=plotting_utils.METHOD_LINESTYLES[method],
                    linewidth=1,
                )
        ax.legend(
            handles=[v for _, v in method_handles.items()],
            fontsize=plotting_utils.LEGEND_FONT_SIZE,
            loc="upper right",
            ncol=1,
            handlelength=2,
            frameon=True,
        )

        ax.spines["bottom"].set_position(("outward", plotting_utils.OUTWARD))  # Move x-axis outward
        ax.spines["left"].set_position(("outward", plotting_utils.OUTWARD))  # Move y-axis outward

        # format x-axis
        ax.set_xlim(1, MAX_DIFFICULTY)
        LABELS = {
            "difficulty": "Reasoning steps",
            "solutions": "Solutions",
        }
        ax.set_xlabel(LABELS[DIFFICULTY], fontsize=plotting_utils.LABEL_FONT_SIZE)
        xticks = [1, 5, 10, 15]
        ax.set_xticks(xticks)
        ax.set_xticks(range(1, MAX_DIFFICULTY + 1), minor=True)
        ax.tick_params(axis="x", which="major")
        ax.tick_params(axis="x", which="minor")
        ax.set_xticklabels(xticks, fontsize=plotting_utils.TICK_FONT_SIZE)
        ax.set_xlim(1, MAX_DIFFICULTY)
        if i == 0:
            ax.set_ylabel(metric.upper(), fontsize=plotting_utils.LABEL_FONT_SIZE)
        # set ylim
        ax.set_ylim(0, 1)
        yticks = [0, 0.25, 0.5, 0.75, 1]
        ax.set_yticks(yticks)
        ax.set_yticklabels(yticks, fontsize=plotting_utils.TICK_FONT_SIZE)
        # set title if there are more than panel
        if len(METHOD_LIST) > 1:
            ax.set_title(name, fontsize=plotting_utils.LABEL_FONT_SIZE)

    # Model handles at the bottom of the figure
    model_handles = []
    for model in model_list:
        key = f"{plotting_utils.MODEL_ALIASES.get(model.lower(), model)}"
        model_handles.append(
            lines.Line2D(
                [0],
                [0],
                color=get_color(model, method),
                label=key,
                linewidth=1,
            )
        )
    ncol = 1 if len(model_handles) <= 2 else 2
    fig.legend(
        handles=model_handles,
        fontsize=plotting_utils.LEGEND_FONT_SIZE,
        loc="lower center",
        ncol=ncol,
        handlelength=4,
        frameon=False,  # Remove bounding box around legend
        bbox_to_anchor=(0.5, -0.15),
    )

    plt.tight_layout()
    if len(METHOD_LIST) == 1:
        plt.subplots_adjust(
            left=0.2, right=0.95, top=0.9, bottom=0.2, wspace=0.3
        )  # Adjust horizontal space between subplots and reduce padding to the left and right
    else:
        plt.subplots_adjust(
            left=0.1, right=0.95, top=0.9, bottom=0.3, wspace=0.3
        )  # Adjust horizontal space between subplots and reduce padding to the left and right

    fig_path = os.path.join(figures_dir, f"{DIFFICULTY}-{metric}.pdf")
    print(f"Saving to {os.path.abspath(fig_path)}")
    plt.savefig(fig_path, bbox_inches="tight", dpi=300)

# %%
