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
"""Script for plotting the `metric` delta between X=zeroshot/fewshot/CoT and X+retriever or X+SC.

Generates a plot for each metric (EM, precision, recall, f1) with the universe size on the x-axis and the `metric` delta on the y-axis.
Saves the plots to the figures directory of the output directory.

Example:
    python eval/plot_size_accuracy.py -od out --method zeroshot --mixin retriever
"""

# %%
import os
from phantom_eval import get_parser
from phantom_eval import plotting_utils
from phantom_eval.evaluate_utils import get_evaluation_data, COLORS, LINESTYLES, HATCHSTYLES, pivot_mean_std, mean, std
import matplotlib.pyplot as plt
import numpy as np

parser = get_parser()
parser.add_argument("--mixin", type=str, default="rag", help="Mixin to compare")
args = parser.parse_args()
output_dir = args.output_dir
method = args.method
dataset = args.dataset
mixin = args.mixin

# get evaluation data from the specified output directory and method subdirectory
df = get_evaluation_data(output_dir, method, dataset)
df_with_retriever = get_evaluation_data(output_dir, f"{method}-{mixin}", dataset)
# import pdb; pdb.set_trace()
# join on ['_model', '_size', '_data_seed', '_seed', 'id]
df = df.merge(df_with_retriever, on=['_model', '_size', '_data_seed', '_seed', 'id'], how='inner', suffixes=('', f'_with_{mixin}'))
# replace ['EM','precision', 'recall', 'f1'] with difference between the two columns
METRICS = [
    'EM',
    'precision', 
    'recall', 
    'f1'
]
df[METRICS] = df[[m + f'_with_{mixin}' for m in METRICS]].sub(df[METRICS].values)
# drop the columns with _with_retriever suffix
df = df.drop(columns=[col for col in df.columns if col.endswith(f'_with_{mixin}')])
# import pdb; pdb.set_trace()

# %%
# group by model, size, data seed, and inference seed
grouped = df.groupby(['_model', '_size', '_data_seed', '_seed'])
# print the accuracy
acc = grouped[METRICS].mean()
# add a column that counts the number of elements in the group
acc['count'] = grouped.size()

# %%
# get the mean and std of the accuracy for each model and split as follows:
# first compute the mean across inference generation seeds
acc_mean_std = acc.groupby(['_model', '_size', '_data_seed']).agg('mean')
# second compute the mean and standard error across data generation seeds
acc_mean_std = acc_mean_std.groupby(['_model', '_size']).agg([mean, std])
acc_mean_std = acc_mean_std.reset_index()

figures_dir = os.path.join(output_dir, 'figures', method)
os.makedirs(figures_dir, exist_ok=True)

# %%
for metric in METRICS:
    df_mean, df_std = pivot_mean_std(acc_mean_std, metric, independent_variable='_size')
    # df_mean columns are the universe sizes
    # df_mean index is the models
    fig = plt.figure(figsize=(3.25, 2.5))
    # import pdb; pdb.set_trace()
    x = np.arange(len(df_mean.columns)) * len(df_mean)
    spacing = 0.2  # space between groups of bars
    width = 0.7-spacing  # the width of the bars

    for idx, (i, row) in enumerate(df_mean.iterrows()):
        y = row.values
        yerr = df_std.loc[i].values
        # import pdb; pdb.set_trace()
        plt.bar(
            x=x + idx * (width + spacing), 
            height=y, 
            width=width, 
            label=i, 
            yerr=yerr, 
            # capsize=5, 
            color=COLORS[i], 
            alpha=0.7, 
            hatch=HATCHSTYLES[i],
        )

    fig.legend(loc='lower center', fontsize=plotting_utils.LEGEND_FONT_SIZE)
    # format x-axis
    plt.xlabel('Size of universe', fontsize=plotting_utils.LABEL_FONT_SIZE)
    plt.xticks(x + (width + spacing) * (len(df_mean) - 1) / 2, df_mean.columns, fontsize=plotting_utils.TICK_FONT_SIZE)
    # format y-axis
    plt.ylabel(f"{metric.upper()} (w/ {mixin} - w/o {mixin})", fontsize=plotting_utils.LABEL_FONT_SIZE)
    plt.yticks(fontsize=plotting_utils.TICK_FONT_SIZE)

    plt.tight_layout()
    plt.subplots_adjust(left=0.2, right=0.95, top=0.95)  # Adjust horizontal space between subplots and reduce padding to the left and right

    fig_path = os.path.join(figures_dir, f'size-delta-{metric}-{mixin}.pdf')
    print(f"Saving to {os.path.abspath(fig_path)}")
    plt.savefig(fig_path)
