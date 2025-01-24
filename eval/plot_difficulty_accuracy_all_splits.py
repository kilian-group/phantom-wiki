"""Script for plotting the accuracy of the models versus the difficulty for all splits.

Generates a plot for each metric (EM, precision, recall, f1) with the difficulty on the x-axis and the metric on the y-axis.
Saves the plots to the figures directory of the output directory.

Example:
    python eval/plot_difficulty_accuracy_all_splits.py -od out --method zeroshot --depth 10
"""

# %%
import os
from phantom_eval import get_parser
from phantom_eval.evaluate_utils import get_evaluation_data, COLORS, LINESTYLES, pivot_mean_std, mean, std, MARKERS
import matplotlib.pyplot as plt
import matplotlib.lines as lines
import matplotlib.patches as mpatches

parser = get_parser()
parser.add_argument(
    '--depth', 
    type=int, 
    default=20, 
    help='Depth to plot accuracies for'
)
args = parser.parse_args()
output_dir = args.output_dir
method = args.method
dataset = args.dataset
depth = args.depth
# get evaluation data from the specified output directory and method subdirectory
df = get_evaluation_data(output_dir, method, dataset)
# filter by depth
df = df[(df['_depth'] == depth)]

# %%
figures_dir = os.path.join(output_dir, 'figures', method)
os.makedirs(figures_dir, exist_ok=True)

# %%
# get accuracies by model, split, difficulty, seed
COLS = ['_model', '_size', '_data_seed', '_seed', 'difficulty']
acc_by_type = df.groupby(COLS)[['EM','precision', 'recall', 'f1']].mean()

# %%
# get the mean and std of the accuracy for each model, split, and difficulty across seeds
# first compute the mean across inference generation seeds
acc_mean_std = acc_by_type.groupby(['_model', '_size', '_data_seed', 'difficulty']).agg(['mean'])
# second compute the mean and standard error across data generation seeds
acc_mean_std = acc_by_type.groupby(['_model', '_size', 'difficulty']).agg([mean, std])
acc_mean_std = acc_mean_std.reset_index()

# %%
# set figure size

# Get sorted list of universe sizes
sizes_in_preds = sorted(acc_mean_std['_size'].unique().tolist())

for metric in ['EM', 'precision', 'recall', 'f1']:
    plt.figure(figsize=(15, 8))

    model_name2labels: dict[str, mpatches.Patch] = {}
    for size in sizes_in_preds:
        acc_mean_std_size = acc_mean_std[acc_mean_std['_size'].astype(int) == size]
        df_mean, df_std = pivot_mean_std(acc_mean_std_size, metric, independent_variable='difficulty')

        x = df_mean.columns
        for model_name, row in df_mean.iterrows():
            y = row
            
            # use a line plot instead of errorbar
            # We can use the index of the size in the list to determine the color intensity
            # Higher index = higher universe size = darker color = higher alpha
            # +1 so that no intensity is 0 = transparent
            color_intensity_for_size = (sizes_in_preds.index(size)+1) / len(sizes_in_preds)  # between 0 and 1
            line_width_for_size = 3*((sizes_in_preds.index(size)+1) / len(sizes_in_preds))  # between 0 and 2

            # Only add label to the last plot
            plt.plot(
                x, y,
                color=COLORS[model_name],
                linestyle=LINESTYLES[model_name],
                alpha=color_intensity_for_size,
                linewidth=line_width_for_size,
            )
            # Add scatter plot
            plt.scatter(
                x, y,
                color=COLORS[model_name],
                s=100, #marker size
                alpha=color_intensity_for_size,
                marker=MARKERS[method],
            )
            # NOTE: not plotting error bars for now because the figure looks crowded
            # yerr = df_std.loc[model_name]
            # # Change color intensity for fill to be between 0 and 0.25
            # color_intensity_for_fill = color_intensity_for_size / 4
            # plt.fill_between(x, y-yerr, y+yerr, alpha=color_intensity_for_fill, color=COLORS[model_name])

            # Add label for the model. [0], [0] are dummy values for the line
            model_name2labels[model_name] = lines.Line2D(
                [0], [0],
                color=COLORS[model_name],
                label=model_name,
                linestyle=LINESTYLES[model_name]
            )
    
    plt.legend(title='Model', loc='upper right', fontsize=12,
               handles=list(model_name2labels.values()), handlelength=4.0)
    # format x-axis
    plt.xlabel('Difficulty')
    plt.xticks(x, df_mean.columns)
    plt.ylabel(metric)
    # set ylim
    plt.ylim(0, 1)
    plt.tight_layout()
    fig_path = os.path.join(figures_dir, f'difficulty-{metric}.pdf')
    print(f"Saving to {os.path.abspath(fig_path)}")
    plt.savefig(fig_path)
