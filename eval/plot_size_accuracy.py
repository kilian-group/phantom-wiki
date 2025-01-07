"""Script for plotting the accuracy of the models versus the universe size.

Generates a plot for each metric (EM, precision, recall, f1) with the universe size on the x-axis and the metric on the y-axis.
Saves the plots to the figures directory of the output directory.

Example:
    python plot_size_accuracy.py -od out --method zeroshot
"""

# %%
import os
from phantom_eval import get_parser
from phantom_eval.evaluate_utils import get_evaluation_data, COLORS, LINESTYLES, pivot_mean_std
import matplotlib.pyplot as plt
import numpy as np

parser = get_parser()
args = parser.parse_args()
output_dir = args.output_dir
method = args.method
# get evaluation data from the specified output directory and method subdirectory
df = get_evaluation_data(output_dir, method)

# %%
# group by model, split, and seed
grouped = df.groupby(['_model', '_split', '_seed'])
# print the accuracy
acc = grouped[['EM','precision', 'recall', 'f1']].mean()
# add a column that counts the number of elements in the group
acc['count'] = grouped.size()

# %%
# get the mean and std of the accuracy for each model and split
# where std is the standard deviation across seeds
acc_mean_std = acc.groupby(['_model', '_split']).agg(['mean', 'std'])
acc_mean_std = acc_mean_std.reset_index()
import re
acc_mean_std['_split'] = acc_mean_std['_split'].apply(lambda x: re.match(r"depth_(\d+)_size_(\d+)_seed_(\d+)", x).group(2))

figures_dir = os.path.join(output_dir, 'figures', method)
os.makedirs(figures_dir, exist_ok=True)

# %%
# set figure size
for metric in ['EM', 'precision', 'recall', 'f1']:
    df_mean, df_std = pivot_mean_std(acc_mean_std, metric)

    plt.figure(figsize=(15, 8))
    # use log2 scale for the x-axis
    x = np.log2(df_mean.columns)
    for i, row in df_mean.iterrows():
        y = row
        yerr = df_std.loc[i]
        # plt.errorbar(x, y, yerr=yerr, label=i, marker='o')
        # use a line plot instead of errorbar
        plt.plot(x, y, label=i, marker='o', color=COLORS[i], linestyle=LINESTYLES[i])
        plt.fill_between(x, y-yerr, y+yerr, alpha=0.3, color=COLORS[i])

    plt.legend(title='Model', loc='lower right', fontsize=12)
    # format x-axis
    plt.xlabel('Size of universe')
    plt.xticks(x, df_mean.columns)
    plt.ylabel(metric)
    plt.tight_layout()
    fig_path = os.path.join(figures_dir, f'size-{metric}.png')
    print(f"Saving to {os.path.abspath(fig_path)}")
    plt.savefig(fig_path)
