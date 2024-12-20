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

# %% [markdown]
# Script to aggregate prediction files, compute metrics, and plot figures
# To run:
#   python evaluate.py -od <path to folder containing outputs>

# %%
import os
from phantom_eval.utils import get_parser
from phantom_eval.evaluate_utils import get_evaluation_data
parser = get_parser()
args, _ = parser.parse_known_args()
output_dir = args.output_dir
method = args.method
# specify which split you want to look at for the plots (besides the one versus universe size, which looks at all splits)
SPLIT_NAME = 'depth_10_size_26_seed_1'
# get evaluation data from the specified output directory and method subdirectory
df = get_evaluation_data(output_dir, method)

# %% [markdown]
# ## Split

# %%
# group by model, split, and seed
grouped = df.groupby(['_model', '_split', '_seed'])
# print the accuracy
acc = grouped[['EM','precision', 'recall', 'f1']].mean()
# add a column that counts the number of elements in the group
acc['count'] = grouped.size()
# print as markdown
print(acc.to_markdown())
# save to a csv file
scores_dir = os.path.join(output_dir, 'scores')
os.makedirs(scores_dir, exist_ok=True)
acc.to_csv(os.path.join(scores_dir, "scores.csv"))

# %% [markdown]
# ## Split & type

# %%
# get accuracies by type
# group by model, split, seed, type
COLS = ['_model', '_split', '_seed', '_type', 'template', 'hops', 'aggregation', 'solutions']
acc_by_type = df.groupby(COLS)[['EM','precision', 'recall', 'f1']].mean()
# compute the mean and std across seeds
# drop '_seed' from COLS
COLS.remove('_seed')
acc_by_type_mean_std = acc_by_type.groupby(COLS).agg(['mean', 'std'])
# print the accuracy
print(acc_by_type_mean_std.to_markdown())
# collapse multi-index columns
acc_by_type_mean_std.columns = acc_by_type_mean_std.columns.to_flat_index()
# save to a csv file
acc_by_type_mean_std.to_csv(os.path.join(scores_dir, "scores_by_type.csv"))

# %%
# hard-code the order of the models for the plot
# otherwise, the order will be alphabetical (and the model size will not be in order)
MODELS = [
    'google/gemma-2-27b-it',
    'google/gemma-2-9b-it',
    'google/gemma-2-2b-it',
    'meta-llama/llama-3.1-8b-instruct',
    'meta-llama/llama-3.1-70b-instruct',
    'microsoft/phi-3.5-mini-instruct',
    'mistralai/mistral-7b-instruct-v0.3',
    'gemini-1.5-flash-8b-001',
    'gemini-1.5-flash-002',
    'gemini-2.0-flash-exp',
]

# %%
# create a plot
import matplotlib.pyplot as plt
# utils for plotting
from matplotlib.patches import Patch
import numpy as np
plt.rcParams.update({
    'font.size': 24,
    'font.family': 'serif',
    'mathtext.fontset': 'stix',
    'axes.labelsize': 24,
    'axes.titlesize': 24,
    'xtick.labelsize': 24,
    'ytick.labelsize': 24,
    'legend.fontsize': 24,
    'axes.linewidth': 0.8,
    'lines.linewidth': 3,
    'lines.markersize': 10,
    'axes.spines.top': False,
    'axes.spines.right': False,
})
figures_dir = os.path.join(output_dir, 'figures')
os.makedirs(figures_dir, exist_ok=True)

# %%
COLORS = {
    'google/gemma-2-27b-it': 'tab:blue',
    'google/gemma-2-9b-it': 'tab:blue',
    'google/gemma-2-2b-it': 'tab:blue',
    'meta-llama/llama-3.1-70b-instruct': 'tab:orange',
    'meta-llama/llama-3.1-8b-instruct': 'tab:orange',
    'microsoft/phi-3.5-mini-instruct': 'tab:green',
    'mistralai/mistral-7b-instruct-v0.3' : 'tab:red',
    'gemini-1.5-flash-002': 'tab:purple',
    'gemini-1.5-flash-8b-001': 'tab:purple',
    'gemini-2.0-flash-exp': 'tab:purple',
}
LINESTYLES = {
    'google/gemma-2-27b-it': '-',
    'google/gemma-2-9b-it': '--',
    'google/gemma-2-2b-it': 'dotted',
    'meta-llama/llama-3.1-70b-instruct': '-',
    'meta-llama/llama-3.1-8b-instruct': '--',
    'microsoft/phi-3.5-mini-instruct': '-',
    'mistralai/mistral-7b-instruct-v0.3' : '-',
    'gemini-2.0-flash-exp': '-',
    'gemini-1.5-flash-002': '--',
    'gemini-1.5-flash-8b-001': 'dotted',
}    

# %% [markdown]
# ## Universe size

# %%
# get the mean and std of the accuracy for each model and split
# where std is the standard deviation across seeds
acc_mean_std = acc.groupby(['_model', '_split']).agg(['mean', 'std'])
acc_mean_std = acc_mean_std.reset_index()
import re
acc_mean_std['_split'] = acc_mean_std['_split'].apply(lambda x: re.match(r"depth_(\d+)_size_(\d+)_seed_(\d+)", x).group(2))


# %%
def pivot_mean_std(acc_mean_std, metric, independent_variable='_split'):
    """Pivot acc_mean_std so that the specified independent variable becomes the rows
    """
    df_mean = acc_mean_std.pivot(index='_model', columns=independent_variable, values=(metric, 'mean'))
    # change the column names to integers
    df_mean.columns = df_mean.columns.astype(int)
    # reorder the columns in ascending order
    df_mean = df_mean[sorted(df_mean.columns)]
    row_order = [name for name in MODELS if name in df_mean.index]
    df_mean = df_mean.loc[row_order]

    df_std = acc_mean_std.pivot(index='_model', columns=independent_variable, values=(metric, 'std'))
    # change the column names to integers
    df_std.columns = df_std.columns.astype(int)
    df_std = df_std[sorted(df_std.columns)]
    row_order = [name for name in MODELS if name in df_std.index]
    df_std = df_std.loc[row_order]
    return df_mean, df_std

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
    plt.title(metric)
    plt.tight_layout()
    fig_path = os.path.join(figures_dir, f'size-{metric}.png')
    print(f"Saving to {os.path.abspath(fig_path)}")
    plt.savefig(fig_path)

# %% [markdown]
# ## Number of hops
# Grouped bar chart where bars are grouped by number of hops. In each group we have the different splits.

# %%
# get the mean and std of the accuracy for each model and split
# where std is the standard deviation across seeds
acc_mean_std = acc_by_type.groupby(['_model', '_split', 'hops']).agg(['mean', 'std'])
acc_mean_std = acc_mean_std.reset_index()
acc_mean_std_split = acc_mean_std[acc_mean_std['_split'] == SPLIT_NAME]

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
    plt.title(metric)
    plt.tight_layout()
    fig_path = os.path.join(figures_dir, f'hops-{metric}-{SPLIT_NAME}.png')
    print(f"Saving to {os.path.abspath(fig_path)}")
    plt.savefig(fig_path)

# %% [markdown]
# ## Aggregation vs no-aggregation
# Some questions involve the `aggregate_all` predicate. What is the effect of these questions on the accuracy?

# %%
# get the mean and std of the accuracy for each model and split
# where std is the standard deviation across seeds
acc_mean_std = acc_by_type.groupby(['_model', '_split', 'aggregation']).agg(['mean', 'std'])
acc_mean_std = acc_mean_std.reset_index()
acc_mean_std_split = acc_mean_std[acc_mean_std['_split'] == SPLIT_NAME]

# %%
acc_mean_std_split

# %%

# set figure size
for metric in ['EM', 'precision', 'recall', 'f1']:
    df_mean, df_std = pivot_mean_std(acc_mean_std_split, metric, independent_variable='aggregation')

    plt.figure(figsize=(15, 8))
    x = df_mean.columns
    for i, row in df_mean.iterrows():
        y = row
        yerr = df_std.loc[i]
        # use a line plot instead of errorbar
        plt.plot(x, y, label=i, marker='o', color=COLORS[i], linestyle=LINESTYLES[i])
        plt.fill_between(x, y-yerr, y+yerr, alpha=0.3, color=COLORS[i])

    plt.legend(title='Model', loc='lower right', fontsize=12)
    # format x-axis
    plt.xlabel('Aggregation vs no aggregation')
    plt.xticks(x, df_mean.columns)
    plt.ylabel(metric)
    plt.title(metric)
    plt.tight_layout()
    fig_path = os.path.join(figures_dir, f'aggregation-{metric}-{SPLIT_NAME}.png')
    print(f"Saving to {os.path.abspath(fig_path)}")
    plt.savefig(fig_path)

# %% [markdown]
# ## Number of solutions
# Some questions have multiple ground-truth answers. What is the effect of the number of solutions on the accuracy?

# %%
# get the mean and std of the accuracy for each model and split
# where std is the standard deviation across seeds
acc_mean_std = acc_by_type.groupby(['_model', '_split', 'solutions']).agg(['mean', 'std'])
acc_mean_std = acc_mean_std.reset_index()
acc_mean_std_split = acc_mean_std[acc_mean_std['_split'] == SPLIT_NAME]

# %%
acc_mean_std_split

# %%

# set figure size
for metric in ['EM', 'precision', 'recall', 'f1']:
    df_mean, df_std = pivot_mean_std(acc_mean_std_split, metric, independent_variable='solutions')

    plt.figure(figsize=(15, 8))
    x = df_mean.columns
    for i, row in df_mean.iterrows():
        y = row
        yerr = df_std.loc[i]
        # use a line plot instead of errorbar
        plt.plot(x, y, label=i, marker='o', color=COLORS[i], linestyle=LINESTYLES[i])
        plt.fill_between(x, y-yerr, y+yerr, alpha=0.3, color=COLORS[i])

    plt.legend(title='Model', loc='lower right', fontsize=12)
    # format x-axis
    plt.xlabel('Number of solutions')
    plt.xticks(x, df_mean.columns)
    plt.ylabel(metric)
    plt.title(metric)
    plt.tight_layout()
    fig_path = os.path.join(figures_dir, f'solutions-{metric}-{SPLIT_NAME}.png')
    print(f"Saving to {os.path.abspath(fig_path)}")
    plt.savefig(fig_path)

# %%
