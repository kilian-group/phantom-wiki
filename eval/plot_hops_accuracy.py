"""Script for plotting the accuracy of the models versus the number of hops.

Generates a plot for each metric (EM, precision, recall, f1) with the number of hops on the x-axis and the metric on the y-axis.
Saves the plots to the figures directory of the output directory.

Example:
    python eval/plot_hops_accuracy.py -od out --method zeroshot --depth 10 --size 26
"""

# %%
import os
from phantom_eval import get_parser
from phantom_eval.evaluate_utils import get_evaluation_data, COLORS, LINESTYLES, pivot_mean_std, mean, std
import matplotlib.pyplot as plt

parser = get_parser()
parser.add_argument(
    '--depth', 
    type=int, 
    default=20, 
    help='Depth to plot accuracies for'
)
parser.add_argument(
    '--size',
    type=int,
    default=50,
    help='Size to plot accuracies for'
)
args = parser.parse_args()
output_dir = args.output_dir
method = args.method
dataset = args.dataset
depth = args.depth
size = args.size
# get evaluation data from the specified output directory and method subdirectory
df = get_evaluation_data(output_dir, method, dataset)
# filter by depth and size
df = df[(df['_depth'] == depth) & (df['_size'] == size)]

# %%
figures_dir = os.path.join(output_dir, 'figures', method)
os.makedirs(figures_dir, exist_ok=True)

# %%
# get accuracies by model, split, hops, seed
COLS = ['_model', '_data_seed', '_seed', 'hops']
acc_by_type = df.groupby(COLS)[['EM','precision', 'recall', 'f1']].mean()

# %%
# get the mean and std of the accuracy for each model, split, and hops across seeds
# first compute the mean across inference generation seeds
acc_mean_std = acc_by_type.groupby(['_model', '_data_seed', 'hops']).agg('mean')
# second compute the mean and standard error across data generation seeds
acc_mean_std = acc_by_type.groupby(['_model', 'hops']).agg([mean, std])
acc_mean_std = acc_mean_std.reset_index()

# %%
# set figure size
for metric in ['EM', 'precision', 'recall', 'f1']:
    df_mean, df_std = pivot_mean_std(acc_mean_std, metric, independent_variable='hops')

    plt.figure(figsize=(15, 8))
    x = df_mean.columns
    for i, row in df_mean.iterrows():
        y = row
        yerr = df_std.loc[i]
        # plt.errorbar(x, y, yerr=yerr, label=i, marker='o')
        # use a line plot instead of errorbar
        plt.plot(x, y, label=i, marker='o', color=COLORS[i], linestyle=LINESTYLES[i])
        plt.fill_between(x, y-yerr, y+yerr, alpha=0.3, color=COLORS[i])

    plt.legend(title='Model', loc='upper right', fontsize=12)
    # format x-axis
    plt.xlabel('Number of hops')
    plt.xticks(x, df_mean.columns)
    plt.ylabel(metric)
    plt.tight_layout()
    fig_path = os.path.join(figures_dir, f'hops-{metric}-{depth=}-{size=}.png')
    print(f"Saving to {os.path.abspath(fig_path)}")
    plt.savefig(fig_path)
