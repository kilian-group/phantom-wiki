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
#     name: dataset
# ---

# %% [markdown]
# Script to aggregate prediction files, compute metrics, and plot figures
# To run:
#   python evaluate.py -od <path to folder containing outputs>

# %%
from phantom_eval.utils import (get_parser)
parser = get_parser()
args, _ = parser.parse_known_args()
output_dir = args.output_dir
method = args.method

# %%
from glob import glob
import pandas as pd
import os
# get all files in the output directory
files = glob(f"{output_dir}/preds/{method}/*.json")
df_list = []
# keys to create auxiliary columns that are useful for analysis
METADATA = ['model', 'split', 'batch_size', 'batch_number', 'type']
SAMPLING_PARAMS = ['seed']
for filename in files:
    print(f"Reading from {filename}...")
    df = pd.read_json(filename, orient='index', dtype=False)
    # add new columns corresponding to the metadata
    for key in METADATA:
        df["_" + key] = df['metadata'].apply(lambda x: x[key])
    # add new columns corresponding to the sampling parameters
    for key in SAMPLING_PARAMS:
        df["_" + key] = df['inference_params'].apply(lambda x: x[key])
    # drop the metadata column
    df = df.drop(columns=['metadata'])
    df_list.append(df)
# concatenate all dataframes
df = pd.concat(df_list)
# print(df.columns)

# %%
# compute scores
from phantom_eval.score import (match,
                                precision,
                                recall,
                                f1)
# join the true answers with the appropriate seperator
# since the scoring functions expect strings
sep = ', ' # TODO: specifiy the type of separator in the model prompt as well
df['EM'] = df.apply(lambda x: match(x['pred'], sep.join(x['true']), exact=True, sep=sep), axis=1)
df['precision'] = df.apply(lambda x: precision(x['pred'], sep.join(x['true']), sep=sep), axis=1)
df['recall'] = df.apply(lambda x: recall(x['pred'], sep.join(x['true']), sep=sep), axis=1)
df['f1'] = df.apply(lambda x: f1(x['pred'], sep.join(x['true']), sep=sep), axis=1)
print(df)
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

# get accuracies by type
if False:
    # group by model, split, seed, and type
    acc_by_type = df.groupby(['_model', '_split', '_seed', '_type'])[['EM','precision', 'recall', 'f1']].mean()
    # compute the mean and std across seeds
    acc_by_type_mean_std = acc_by_type.groupby(['_model', '_split', '_type']).agg(['mean', 'std'])
    # print the accuracy
    print(acc_by_type_mean_std.to_markdown())
    # collapse multi-index columns
    acc_by_type_mean_std.columns = acc_by_type_mean_std.columns.to_flat_index()
    # save to a csv file
    acc_by_type_mean_std.to_csv(os.path.join(scores_dir, "scores_by_type.csv"))
    # # get the length of the query for each type
    # from phantom_wiki.facts.templates import generate_templates
    # # assert the depth is the same for rows in acc_by_type
    # import re
    # depths = acc_by_type['_split'].apply(lambda x: re.match(r"depth_(\d+)_size_(\d+)_seed_(\d+)", x).group(1))
    # assert depths.nunique() == 1
    # depth = int(depths.iloc[0])
    # templates = generate_templates(depth=depth)
    # import pdb; pdb.set_trace()
    # # get the length of the query for each type
    # acc_by_type['query_length'] = acc_by_type['_type'].apply(lambda x: len(templates[x].query.split()))

# %%
# get the mean and std of the accuracy for each model and split
# where std is the standard deviation across seeds
acc_mean_std = acc.groupby(['_model', '_split']).agg(['mean', 'std'])

# %%
acc_mean_std

# %%
acc_mean_std.index

# %%
acc_mean_std = acc_mean_std.reset_index()
import re
acc_mean_std['_split'] = acc_mean_std['_split'].apply(lambda x: re.match(r"depth_(\d+)_size_(\d+)_seed_(\d+)", x).group(2))

# %%
acc_mean_std

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
def get_mean_std(metric):
    df_mean = acc_mean_std.pivot(index='_model', columns='_split', values=(metric, 'mean'))
    # change the column names to integers
    df_mean.columns = df_mean.columns.astype(int)
    # reorder the columns in ascending order
    df_mean = df_mean[sorted(df_mean.columns)]
    row_order = [name for name in MODELS if name in df_mean.index]
    df_mean = df_mean.loc[row_order]

    df_std = acc_mean_std.pivot(index='_model', columns='_split', values=(metric, 'std'))
    # change the column names to integers
    df_std.columns = df_std.columns.astype(int)
    df_std = df_std[sorted(df_std.columns)]
    row_order = [name for name in MODELS if name in df_std.index]
    df_std = df_std.loc[row_order]
    return df_mean, df_std

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

# %%
# set figure size
for metric in ['EM', 'precision', 'recall', 'f1']:
    df_mean, df_std = get_mean_std(metric)

    plt.figure(figsize=(15, 8))
    for i, row in df_mean.iterrows():
        x = df_mean.columns
        # use log2 scale for the x-axis
        x = np.log2(x)
        y = row
        yerr = df_std.loc[i]
        # plt.errorbar(x, y, yerr=yerr, label=i, marker='o')
        # use a line plot instead of errorbar
        plt.plot(x, y, label=i, marker='o', color=COLORS[i], linestyle=LINESTYLES[i])
        plt.fill_between(x, y-yerr, y+yerr, alpha=0.3, color=COLORS[i])

    plt.legend(title='Model', loc='lower right', fontsize=12)
    # format x-axis
    plt.xlabel('Size of universe')
    plt.xticks(np.log2(df_mean.columns), df_mean.columns)
    plt.ylabel(metric)
    plt.title(metric)
    plt.tight_layout()
    fig_path = os.path.join(figures_dir, f'{metric}.png')
    print(f"Saving to {os.path.abspath(fig_path)}")
    plt.savefig(fig_path)

# %%
