"""Script for plotting the accuracy of the models versus the universe size.

Generates a plot for each metric (EM, precision, recall, f1) with the universe size on the x-axis and the metric on the y-axis.
Saves the plots to the figures directory of the output directory.

Example:
    python eval/plot_size_accuracy.py -od out --method zeroshot
"""

# %%
import os
import logging
from phantom_eval import get_parser
from phantom_eval.utils import setup_logging
# setup_logging("DEBUG")
from phantom_eval.evaluate_utils import get_evaluation_data, COLORS, LINESTYLES, pivot_mean_std, mean, std, MARKERS
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as lines

import numpy as np
# TODO: use LaTeX for rendering (need to have LaTeX installed locally)

parser = get_parser()
parser.add_argument(
    "--method_list", 
    nargs="+", 
    default=["zeroshot", "cot", "zeroshot-retriever", "cot-retriever"],
    help="Method to plot"
)
parser.add_argument(
    "--model_list",
    nargs="+",
    default=["gemini-1.5-flash-002", "meta-llama/llama-3.3-70b-instruct", "deepseek-ai/deepseek-r1-distill-qwen-32b"],
    help="List of models to plot"
)
args = parser.parse_args()
output_dir = args.output_dir
method_list = args.method_list
model_list = args.model_list
dataset = args.dataset
figures_dir = os.path.join(output_dir, 'figures')
os.makedirs(figures_dir, exist_ok=True)
METRICS = [
    # 'EM', 
    # 'precision', 
    # 'recall', 
    'f1',
]
for metric in METRICS:
    fig = plt.figure(figsize=(3.25, 2.75)) # exact dimensions of ICML single column width
    model_name2labels: dict[str, mpatches.Patch] = {}

    for method in method_list:
        # get evaluation data from the specified output directory and method subdirectory
        df = get_evaluation_data(output_dir, method, dataset)
        # group by model, size, data seed, and inference seed
        grouped = df.groupby(['_model', '_size', '_data_seed', '_seed'])
        # print the accuracy
        acc = grouped[['EM','precision', 'recall', 'f1']].mean()
        # add a column that counts the number of elements in the group
        acc['count'] = grouped.size()

        # get the mean and std of the accuracy for each model and split as follows:
        # first compute the mean across inference generation seeds
        acc_mean_std = acc.groupby(['_model', '_size', '_data_seed']).agg('mean')
        # second compute the mean and standard error across data generation seeds
        acc_mean_std = acc_mean_std.groupby(['_model', '_size']).agg([mean, std])
        acc_mean_std = acc_mean_std.reset_index()

        df_mean, df_std = pivot_mean_std(acc_mean_std, metric, independent_variable='_size')

        # use log2 scale for the x-axis
        x = np.log2(df_mean.columns)
        for model_name, row in df_mean.iterrows():
            if model_name not in model_list:
                continue
            y = row
            yerr = df_std.loc[model_name]
            # plt.errorbar(x, y, yerr=yerr, label=i, marker='o')
            # use a line plot instead of errorbar
            plt.plot(
                x, y, 
                label=f"{method}+{model_name}", # cot+gemini-1.5-flash-002
                color=COLORS[model_name], 
                linestyle=LINESTYLES[model_name],
                linewidth=1,
            )
            # Add scatter plot
            plt.scatter(
                x[::2], y[::2],
                color=COLORS[model_name],
                s=20, #marker size
                marker=MARKERS[method],
            )
            plt.fill_between(x, y-yerr, y+yerr, alpha=0.1, color=COLORS[model_name])
            # Add label for the model. [0], [0] are dummy values for the line
            key = f"{method}+{model_name}"
            model_name2labels[key] = lines.Line2D(
                [0], [0],
                color=COLORS[model_name],
                label=key, ###f"{method}+{model_name}", # cot+gemini-1.5-flash-002
                linestyle=LINESTYLES[model_name],
                marker=MARKERS[method],
                markersize=4,
                linewidth=1,
            )

    plt.legend(
        handles=list(model_name2labels.values()), 
        fontsize=4,
        loc='upper center',
        bbox_to_anchor=(0.5, -0.3),
        ncol=2
    )

    ax = plt.gca()
    ax.spines['bottom'].set_position(('outward', 1))  # Move x-axis outward
    ax.spines['left'].set_position(('outward', 1))    # Move y-axis outward

    # format x-axis
    plt.xlabel('Universe Size', fontsize=16)
    # Only add labels at 10, but keep the ticks at all points
    ticks, labels = zip(*[(t, l if np.log10(l).is_integer() else "") for t, l in zip(x, df_mean.columns.tolist())])
    plt.xticks(ticks, labels, fontsize=10)

    # format y-axis
    plt.ylabel(metric.upper(), fontsize=8)
    plt.ylim(0, 1)
    plt.yticks(fontsize=10)

    plt.tight_layout()
    fig.subplots_adjust(left=0.17, right=0.85, bottom=0.3, top=0.95) #, wspace=0.3, hspace=0.3)

    fig_path = os.path.join(figures_dir, f'size-{metric}.pdf')
    print(f"Saving to {os.path.abspath(fig_path)}")
    plt.savefig(fig_path)
