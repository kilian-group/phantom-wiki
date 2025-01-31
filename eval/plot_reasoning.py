"""Script for plotting the accuracy of the models versus the difficulty for all splits.

Generates a plot for each metric (EM, precision, recall, f1) with the difficulty on the x-axis and the metric on the y-axis.
Saves the plots to the figures directory of the output directory.

Example:
    python eval/plot_difficulty_accuracy_all_splits.py -od out --method zeroshot --depth 10
"""

# %%
import os
from phantom_eval import get_parser
from phantom_eval.utils import setup_logging
setup_logging("INFO")
from phantom_eval.evaluate_utils import get_evaluation_data, pivot_mean_std, mean, std
from phantom_eval import plotting_utils
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
parser.add_argument(
    "--method_list", 
    nargs="+",
    default=plotting_utils.DEFAULT_METHOD_LIST,
    help="Method to plot"
)
parser.add_argument(
    "--model_list",
    nargs="+",
    default=plotting_utils.DEFAULT_MODEL_LIST,
    help="List of models to plot"
)
args = parser.parse_args()
output_dir = args.output_dir
method_list = args.method_list
model_list = args.model_list
dataset = args.dataset
depth = args.depth
figures_dir = os.path.join(output_dir, 'figures')
os.makedirs(figures_dir, exist_ok=True)
METRICS = [
    # 'EM', 
    # 'precision', 
    # 'recall', 
    'f1',
]
# Difficulty can either be 'difficulty' (i.e., reasoning steps) or 'solutions' (i.e., number of solutions to the questions)
MAX_DIFFICULTY = 15
DIFFICULTY = 'difficulty'

for metric in METRICS:
    # fig = plt.figure(figsize=(3.25, 2.75)) # exact dimensions of ICML single column width
    # replace this with a subplot figure with 1 rows and 3 columns
    fig, axs = plt.subplots(1, 3, figsize=(6.75, 2.5))

    for i, (name, methods) in enumerate([('In-Context', plotting_utils.INCONTEXT_METHODS), ('RAG', plotting_utils.RAG_METHODS), ('Agentic', plotting_utils.AGENTIC_METHODS)]):
        method_handles = {}
        for method in methods:
            print(f"Plotting {method} for {metric}")
            # get evaluation data from the specified output directory and method subdirectory
            df = get_evaluation_data(output_dir, method, dataset)
            if df.empty:
                print(f"No data found for {method}")
                continue
            # ignore difficulty beyond 15
            df = df[df[DIFFICULTY] <= MAX_DIFFICULTY]
            # df = df[df['solutions']<= 1]
            # filter by depth
            df = df[(df['_depth'] == depth)]
            # get accuracies by model, split, difficulty, seed
            COLS = ['_model', '_size', '_data_seed', '_seed', DIFFICULTY]
            acc_by_type = df.groupby(COLS)[METRICS].mean()

            # get the mean and std of the accuracy for each model, split, and difficulty across seeds
            # first compute the mean across inference generation seeds
            acc_mean_std = acc_by_type.groupby(['_model', '_size', '_data_seed', DIFFICULTY]).agg('mean')
            # second compute the mean and standard error across data generation seeds
            acc_mean_std = acc_mean_std.groupby(['_model', '_size', DIFFICULTY]).agg([mean, std])
            acc_mean_std = acc_mean_std.reset_index()
            # Get sorted list of universe sizes
            sizes_in_preds = sorted(acc_mean_std['_size'].unique().tolist())
            # only plot a few sizes
            sizes_in_preds = [min(sizes_in_preds)]
            method_ = plotting_utils.SIMPLIFIED_METHODS[method]

            for size in sizes_in_preds:
                acc_mean_std_size = acc_mean_std[acc_mean_std['_size'].astype(int) == size]
                df_mean, df_std = pivot_mean_std(acc_mean_std_size, metric, independent_variable=DIFFICULTY)
                x = df_mean.columns
                for model_name, row in df_mean.iterrows():
                    if model_name not in model_list:
                        continue
                    y = row
                    # Only add label to the last plot
                    axs[i].plot(
                        x, y,
                        color=plotting_utils.COLORS[model_name],
                        # NOTE: determine the linestyle using the method
                        linestyle=plotting_utils.METHOD_LINESTYLES[method_],
                        linewidth=1,
                        alpha=plotting_utils.LINE_ALPHA,
                    )
                    # Add scatter plot
                    axs[i].scatter(
                        x, y,
                        color=plotting_utils.COLORS[model_name],
                        s=plotting_utils.MARKER_SIZE, #marker size
                        alpha=plotting_utils.MARKER_ALPHA,
                        clip_on=False,
                    )
                    # NOTE: not plotting error bars for now because the figure looks crowded
                    yerr = df_std.loc[model_name]
                    # Change color intensity for fill to be between 0 and 0.25
                    color_intensity_for_fill = 0.1
                    axs[i].fill_between(x, y-yerr, y+yerr, alpha=color_intensity_for_fill, color=plotting_utils.COLORS[model_name])
            
            # Add method to legend
            key = f"{plotting_utils.METHOD_ALIASES[method_]}"
            if key not in method_handles:
                method_handles[key] = lines.Line2D(
                    [0], [0],
                    color="black",
                    label=key, 
                    linestyle=plotting_utils.METHOD_LINESTYLES[method_],
                    linewidth=1,
                )
        axs[i].legend(
            handles=[v for _, v in method_handles.items()],
            fontsize=plotting_utils.LEGEND_FONT_SIZE,
            loc='upper right',
            ncol=1,
            handlelength=2,
            frameon=True,
        )
        
        axs[i].spines['bottom'].set_position(('outward', plotting_utils.OUTWARD))  # Move x-axis outward
        axs[i].spines['left'].set_position(('outward', plotting_utils.OUTWARD))    # Move y-axis outward

        # format x-axis
        axs[i].set_xlim(1, MAX_DIFFICULTY)
        LABELS = {
            'difficulty': 'Reasoning steps',
            'solutions': 'Solutions',
        }
        axs[i].set_xlabel(LABELS[DIFFICULTY], fontsize=plotting_utils.LABEL_FONT_SIZE)
        xticks = [1, 5, 10, 15]
        axs[i].set_xticks(xticks)
        axs[i].set_xticks(range(1, MAX_DIFFICULTY+1), minor=True)
        axs[i].tick_params(axis='x', which='major')
        axs[i].tick_params(axis='x', which='minor')
        axs[i].set_xticklabels(xticks, fontsize=plotting_utils.TICK_FONT_SIZE)
        axs[i].set_xlim(1, MAX_DIFFICULTY)
        if i == 0:
            axs[i].set_ylabel(metric.upper(), fontsize=plotting_utils.LABEL_FONT_SIZE)
        # set ylim
        axs[i].set_ylim(0, 1)
        yticks = [0, 0.5, 1]
        axs[i].set_yticks(yticks)
        axs[i].set_yticks([0.25, 0.75], minor=True)
        axs[i].set_yticks(yticks)
        axs[i].set_yticklabels(yticks, fontsize=plotting_utils.TICK_FONT_SIZE)
        # set title
        axs[i].set_title(name, fontsize=plotting_utils.LABEL_FONT_SIZE)

    # Create separate handles for models and methods
    # We will plot models on the left column and methods on the right column
    # Having the combination of model and method in the legend is too crowded
    model_handles = []
    for model in model_list:
        key = f"{plotting_utils.MODEL_ALIASES[model]}"
        model_handles.append( lines.Line2D(
            [0], [0],
            color=plotting_utils.COLORS[model],
            label=key,
            linewidth=1,
        ) )

    # attach the legend to the entire figure instead of any individual subplot
    fig.legend(
        handles=model_handles,
        fontsize=plotting_utils.LEGEND_FONT_SIZE,
        loc='lower center',
        ncol=6,
        handlelength=4,
        frameon=False,  # Remove bounding box around legend
        bbox_to_anchor=(0.5, 0.0)
    )
    plt.tight_layout()
    plt.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.3, wspace=0.3)  # Adjust horizontal space between subplots and reduce padding to the left and right

    fig_path = os.path.join(figures_dir, f'{DIFFICULTY}-{metric}.pdf')
    print(f"Saving to {os.path.abspath(fig_path)}")
    plt.savefig(fig_path)

# %%
