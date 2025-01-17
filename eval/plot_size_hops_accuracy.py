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
"""Script for plotting accuracy contour curves on hops vs universe size.

Generates a plot with the universe size on the x-axis, number of hops on the y-axis, and accuracy as the contour.
Saves the plots to the figures directory of the output directory.

Example:
    python eval/plot_size_hops_accuracy.py -od out  --method react --split_name depth_10_size_26_seed_1
"""

# %%
import os
from phantom_eval import get_parser
from phantom_eval.evaluate_utils import get_evaluation_data, COLORS, LINESTYLES, pivot_mean_std
import matplotlib.pyplot as plt
import numpy as np

parser = get_parser()
if False:
    args = parser.parse_args()
    output_dir = args.output_dir
    method = args.method
    dataset = args.dataset
else:
    output_dir = '../out-1111'
    method = 'react'
    dataset = 'mlcore/phantom-wiki-v0.2'
# get evaluation data from the specified output directory and method subdirectory
df = get_evaluation_data(output_dir, method, dataset)

# %%
# group by model, split, and seed
grouped = df.groupby(['_model', '_split', '_seed', 'hops'])
# print the accuracy
acc = grouped[['EM','precision', 'recall', 'f1']].mean()
# add a column that counts the number of elements in the group
acc['count'] = grouped.size()

# %%
# get the mean and std of the accuracy for each model and split
# where std is the standard deviation across inference generation seeds
acc_mean_std = acc.groupby(['_model', '_split', 'hops']).agg(['mean', 'std'])
acc_mean_std = acc_mean_std.reset_index()
import re
acc_mean_std['_size'] = acc_mean_std['_split'].apply(lambda x: re.match(r"depth_(\d+)_size_(\d+)_seed_(\d+)", x).group(2))
# now extract the data generation seed
acc_mean_std['_data_seed'] = acc_mean_std['_split'].apply(lambda x: re.match(r"depth_(\d+)_size_(\d+)_seed_(\d+)", x).group(3))
# get all unique data seeds
data_seeds = acc_mean_std['_data_seed'].unique()
print(f"Data seeds: {data_seeds}")

figures_dir = os.path.join(output_dir, 'figures', method)
os.makedirs(figures_dir, exist_ok=True)

# %%
acc_mean_std

# %%
for data_seed in data_seeds:
    acc_mean_std_data_seed = acc_mean_std[acc_mean_std['_data_seed'] == data_seed]

    for metric in ['EM', 'precision', 'recall', 'f1']:
        # NOTE: we don't need to do pivot as we are plotting x=size,y=hops,z=acc together
        # df_mean, df_std = pivot_mean_std(acc_mean_std_data_seed, metric, independent_variable='_size')

        plt.figure(figsize=(15, 8))
        # use log2 scale for the x-axis
        x = acc_mean_std_data_seed['_size'].astype(int).tolist()
        logx = np.log2(x)
        y = acc_mean_std_data_seed['hops'].tolist()
        z = acc_mean_std_data_seed[(metric,'mean')].tolist()
        # plot the contour
        contour = plt.tricontourf(logx, y, z, cmap='viridis')
        plt.colorbar(contour)

        plt.legend(title='Model', loc='upper right', fontsize=12)
        # format x-axis
        plt.xlabel('Size of universe')
        plt.xticks(logx, x)
        plt.ylabel('Number of hops')
        plt.tight_layout()
        fig_path = os.path.join(figures_dir, f'size-hops-{metric}-seed{data_seed}.png')
        print(f"Saving to {os.path.abspath(fig_path)}")
        plt.savefig(fig_path)
        # plt.show()

# %%
