"""Script for plotting the accuracy of the models versus the difficulty for all splits.

Generates a plot for each metric (EM, precision, recall, f1) with the difficulty on the x-axis and the metric on the y-axis.
Saves the plots to the figures directory of the output directory.

Example:
    python eval/plot_difficulty_accuracy_all_splits.py -od out --method zeroshot
"""

# %%
import os
from phantom_eval import get_parser
from phantom_eval.evaluate_utils import get_evaluation_data, COLORS, LINESTYLES, pivot_mean_std
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

parser = get_parser()
args = parser.parse_args()
output_dir = args.output_dir
method = args.method
dataset = args.dataset
# get evaluation data from the specified output directory and method subdirectory
df = get_evaluation_data(output_dir, method, dataset)

# %%
figures_dir = os.path.join(output_dir, 'figures', method)
os.makedirs(figures_dir, exist_ok=True)

# %%
# get accuracies by model, split, difficulty, seed
COLS = ['_model', '_split', '_seed', 'difficulty']
acc_by_type = df.groupby(COLS)[['EM','precision', 'recall', 'f1']].mean()

# %%
# get the mean and std of the accuracy for each model, split, and difficulty across seeds
acc_mean_std = acc_by_type.groupby(['_model', '_split', 'difficulty']).agg(['mean', 'std'])
acc_mean_std = acc_mean_std.reset_index()

# %%
# set figure size

splits_in_preds = acc_mean_std['_split'].unique()
split_list = [split for split in args.split_list if split in splits_in_preds]

for metric in ['EM', 'precision', 'recall', 'f1']:
    plt.figure(figsize=(15, 8))

    for split_name in split_list:
        acc_mean_std_split = acc_mean_std[acc_mean_std['_split'] == split_name]
        df_mean, df_std = pivot_mean_std(acc_mean_std_split, metric, independent_variable='difficulty')

        x = df_mean.columns
        model_name2labels: dict[str, mpatches.Patch] = {}
        for model_name, row in df_mean.iterrows():
            y = row
            yerr = df_std.loc[model_name]
            # plt.errorbar(x, y, yerr=yerr, label=i, marker='o')
            
            # use a line plot instead of errorbar
            # NOTE: assume that args.split_list was ordered in increasing universe size
            # So we can use the index of the split in the list to determine the color intensity
            # Higher index = higher universe size = darker color = higher alpha
            # +1 so that no intensity is 0 = transparent
            color_intensity_for_split = (split_list.index(split_name)+1) / len(split_list)
            
            # Only add label to the last plot
            plt.plot(
                x, y,
                color=COLORS[model_name],
                linestyle=LINESTYLES[model_name],
                alpha=color_intensity_for_split
            )
            plt.fill_between(x, y-yerr, y+yerr, alpha=0.3, color=COLORS[model_name])

            model_name2labels[model_name] = mpatches.Patch(color=COLORS[model_name], label=model_name)
    
    plt.legend(title='Model', loc='upper right', fontsize=12, handles=list(model_name2labels.values()))
    # format x-axis
    plt.xlabel('Difficulty')
    plt.xticks(x, df_mean.columns)
    plt.ylabel(metric)
    plt.tight_layout()
    fig_path = os.path.join(figures_dir, f'difficulty-{metric}.png')
    print(f"Saving to {os.path.abspath(fig_path)}")
    plt.savefig(fig_path)
