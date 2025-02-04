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
"""Script for plotting accuracy contour curves on difficulty vs universe size.

Generates a plot with the universe size on the x-axis, difficulty on the y-axis, and accuracy as the contour.
Saves the plots to the figures directory of the output directory.

Example:
    python eval/plot_size_difficulty_accuracy.py -od out  --method react
"""

# %%
import os
from phantom_eval import get_parser
from phantom_eval.evaluate_utils import get_evaluation_data, COLORS, LINESTYLES, pivot_mean_std, mean, std
from phantom_eval.utils import setup_logging
import matplotlib.pyplot as plt
import numpy as np
import logging
setup_logging(logging.INFO)

parser = get_parser()
parser.add_argument("--threshold_list", type=float, default=[0.25, 0.5, 0.75], nargs='+', 
                    help="List of thresholds to plot")
args = parser.parse_args()
output_dir = args.output_dir
method = args.method
dataset = args.dataset
# get evaluation data from the specified output directory and method subdirectory
df = get_evaluation_data(output_dir, method, dataset)

# %%
# group by model, size, data seed, and seed
grouped = df.groupby(['_model', '_size', '_data_seed', '_seed', 'difficulty'])
# logging.info the accuracy
acc = grouped[['EM','precision', 'recall', 'f1']].mean()
# add a column that counts the number of elements in the group
acc['count'] = grouped.size()

# %%
# get the mean and std of the accuracy for each model and split
# first compute the mean across inference generation seeds
acc_mean_std = acc.groupby(['_model', '_size', '_data_seed', 'difficulty']).agg('mean')
# second compute the mean and standard error across data generation seeds
acc_mean_std = acc.groupby(['_model', '_size', 'difficulty']).agg([mean, std])
acc_mean_std = acc_mean_std.reset_index()
# get all unique models
models = acc_mean_std['_model'].unique()
logging.info(f"Models: {models}")

figures_dir = os.path.join(output_dir, 'figures', method)
os.makedirs(figures_dir, exist_ok=True)

# %%
acc_mean_std

# %%
for metric in ['EM', 'precision', 'recall', 'f1']:
    for threshold in [0.25, 0.5, 0.75]:
        fig, ax = plt.subplots(figsize=(15, 8))
        for model in models:
            acc_mean_std_data_seed = acc_mean_std[acc_mean_std['_model'] == model]
            if len(acc_mean_std_data_seed) == 0:
                logging.warning(f"No data for model {model}")
                continue

            # get the distinct x values
            x = np.sort(np.unique(acc_mean_std_data_seed['_size'].astype(int)))
            logx = np.log2(x)
            # get the distinct y values
            y = np.sort(np.unique(acc_mean_std_data_seed['difficulty']))
            # create a 2D array of z values
            Z = np.zeros((len(y), len(x)))
            for i, size in enumerate(x):
                for j, difficulty in enumerate(y):
                    z = acc_mean_std_data_seed[(acc_mean_std_data_seed['_size'].astype(int) == size) & (acc_mean_std_data_seed['difficulty'] == difficulty)][(metric, 'mean')]
                    Z[j, i] = z.values[0] if len(z) > 0 else np.nan
            # filled in contour
            logX, Y = np.meshgrid(logx, y)
            CS = ax.contour(logX, Y, Z, levels=[threshold])
            # Customize the label
            # Ref: https://matplotlib.org/stable/gallery/images_contours_and_fields/contour_label_demo.html
            # This custom formatter adds the model name to the contour label.
            def fmt(x):
                s = f"{x:.2f} - {model}"
                return s
            # add the contour label
            ax.clabel(CS, CS.levels, fmt=fmt, fontsize=10)

        # ax.legend(title='Model', loc='upper right', fontsize=12)
        # format x-axis
        ax.set_xlabel('Size of universe')
        ax.set_xticks(logx)
        ax.set_xticklabels(x)
        ax.set_ylabel('Difficulty')
        fig.tight_layout()
        fig_path = os.path.join(figures_dir, f'size-difficulty-{metric}@{threshold:.2f}.pdf')
        logging.info(f"Saving to {os.path.abspath(fig_path)}")
        fig.savefig(fig_path)
        # plt.show()

# %%
