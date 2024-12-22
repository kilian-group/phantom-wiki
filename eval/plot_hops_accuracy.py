"""Script for plotting the accuracy of the models versus the number of hops.

Generates a plot for each metric (EM, precision, recall, f1) with the number of hops on the x-axis and the metric on the y-axis.
Saves the plots to the figures directory of the output directory.

Example:
    python plot_hops_accuracy.py -od out --method zeroshot --split_name depth_10_size_26_seed_1
"""

# %%
import os
from phantom_eval.utils import get_parser
from phantom_eval.evaluate_utils import get_evaluation_data, COLORS, LINESTYLES, pivot_mean_std
import matplotlib.pyplot as plt

parser = get_parser()
parser.add_argument(
    '--split_name', 
    type=str, 
    default='depth_10_size_26_seed_1', 
    help='Split to plot accuracies for'
)
args = parser.parse_args()
output_dir = args.output_dir
method = args.method
split_name = args.split_name
# get evaluation data from the specified output directory and method subdirectory
df = get_evaluation_data(output_dir, method)

# %%
figures_dir = os.path.join(output_dir, 'figures')
os.makedirs(figures_dir, exist_ok=True)

# %%
# get accuracies by model, split, hops, seed
COLS = ['_model', '_split', '_seed', 'hops']
acc_by_type = df.groupby(COLS)[['EM','precision', 'recall', 'f1']].mean()

# %%
# get the mean and std of the accuracy for each model, split, and hops across seeds
acc_mean_std = acc_by_type.groupby(['_model', '_split', 'hops']).agg(['mean', 'std'])
acc_mean_std = acc_mean_std.reset_index()
acc_mean_std_split = acc_mean_std[acc_mean_std['_split'] == split_name]

# %%
# set figure size
for metric in ['EM', 'precision', 'recall', 'f1']:
    df_mean, df_std = pivot_mean_std(acc_mean_std_split, metric, independent_variable='hops')

    plt.figure(figsize=(15, 8))
    x = df_mean.columns
    for i, row in df_mean.iterrows():
        y = row
        yerr = df_std.loc[i]
        # plt.errorbar(x, y, yerr=yerr, label=i, marker='o')
        # use a line plot instead of errorbar
        plt.plot(x, y, label=i, marker='o', color=COLORS[i], linestyle=LINESTYLES[i])
        plt.fill_between(x, y-yerr, y+yerr, alpha=0.3, color=COLORS[i])

    plt.legend(title='Model', loc='lower right', fontsize=12)
    # format x-axis
    plt.xlabel('Number of hops')
    plt.xticks(x, df_mean.columns)
    plt.ylabel(metric)
    plt.tight_layout()
    fig_path = os.path.join(figures_dir, f'hops-{metric}-{split_name}.png')
    print(f"Saving to {os.path.abspath(fig_path)}")
    plt.savefig(fig_path)
