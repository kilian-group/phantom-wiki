"""Script for plotting the accuracy of the models versus the difficulty for all splits.

Generates a plot for each metric (EM, precision, recall, f1) with the difficulty on the x-axis and the metric on the y-axis.
Saves the plots to the figures directory of the output directory.

Example:
    python eval/plot_difficulty_accuracy_all_splits.py -od out --method zeroshot --depth 10
"""

# %%
import os
from phantom_eval import get_parser
from phantom_eval.evaluate_utils import get_evaluation_data, COLORS, LINESTYLES, pivot_mean_std, mean, std, MARKERS, MODEL_ALIASES
import matplotlib.pyplot as plt
import matplotlib.lines as lines
import matplotlib.patches as mpatches

# TODO: use LaTeX for rendering (need to have LaTeX installed locally)
# import matplotlib as mpl
# # Add LaTeX packages (note: latex must be installed)
# mpl.rcParams['text.latex.preamble'] = r'\usepackage{amssymb} \usepackage{amsmath}'
# # Enable LaTeX rendering
# mpl.rcParams['text.usetex'] = True
# mpl.rcParams['font.family'] ='serif'

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
    default=["zeroshot", "cot", "zeroshot-retriever", "cot-retriever", "react", 
            #  "act" # TODO: some json IO issue
             ], 
    help="Method to plot"
)
parser.add_argument(
    "--model_list",
    nargs="+",
    default=["gemini-1.5-flash-002", "meta-llama/llama-3.3-70b-instruct", "deepseek-ai/deepseek-r1-distill-qwen-32b"],
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
MAX_DIFFICULTY = 16
for metric in METRICS:
    fig = plt.figure(figsize=(3.25, 2.75)) # exact dimensions of ICML single column width
    model_name2labels: dict[str, mpatches.Patch] = {}

    for method in method_list:
        # get evaluation data from the specified output directory and method subdirectory
        df = get_evaluation_data(output_dir, method, dataset)

        # ignore difficulty beyond 15
        df = df[df['difficulty'] <= MAX_DIFFICULTY]
        # filter by depth
        df = df[(df['_depth'] == depth)]
        # get accuracies by model, split, difficulty, seed
        COLS = ['_model', '_size', '_data_seed', '_seed', 'difficulty']
        acc_by_type = df.groupby(COLS)[METRICS].mean()

        # get the mean and std of the accuracy for each model, split, and difficulty across seeds
        # first compute the mean across inference generation seeds
        acc_mean_std = acc_by_type.groupby(['_model', '_size', '_data_seed', 'difficulty']).agg('mean')
        # second compute the mean and standard error across data generation seeds
        acc_mean_std = acc_mean_std.groupby(['_model', '_size', 'difficulty']).agg([mean, std])
        acc_mean_std = acc_mean_std.reset_index()
        # Get sorted list of universe sizes
        sizes_in_preds = sorted(acc_mean_std['_size'].unique().tolist())
        # only plot a few sizes
        sizes_in_preds = [min(sizes_in_preds)]

        for size in sizes_in_preds:
            acc_mean_std_size = acc_mean_std[acc_mean_std['_size'].astype(int) == size]
            df_mean, df_std = pivot_mean_std(acc_mean_std_size, metric, independent_variable='difficulty')

            x = df_mean.columns
            for model_name, row in df_mean.iterrows():
                if model_name not in model_list:
                    continue
                y = row

                # Only add label to the last plot
                plt.plot(
                    x, y,
                    color=COLORS[model_name],
                    linestyle=LINESTYLES[model_name],
                    linewidth=1,
                )
                # Add scatter plot
                plt.scatter(
                    x[::2], y[::2],
                    color=COLORS[model_name],
                    s=20, #marker size
                    marker=MARKERS[method],
                )
                # NOTE: not plotting error bars for now because the figure looks crowded
                yerr = df_std.loc[model_name]
                # Change color intensity for fill to be between 0 and 0.25
                color_intensity_for_fill = 0.1
                plt.fill_between(x, y-yerr, y+yerr, alpha=color_intensity_for_fill, color=COLORS[model_name])

                # Add label for the model. [0], [0] are dummy values for the line
                # key = f"{method}+{model_name}"
                key = f"{method} + {MODEL_ALIASES[model_name]}"
                model_name2labels[key] = lines.Line2D(
                    [0], [0],
                    color=COLORS[model_name],
                    label=key, ###f"{method}+{model_name}", # cot+gemini-1.5-flash-002
                    linestyle=LINESTYLES[model_name],
                    marker=MARKERS[method],
                    markersize=4,
                    linewidth=1,
                )

    plt.legend(
        handles=list(model_name2labels.values()), 
        fontsize=4,
        loc='upper center',
        bbox_to_anchor=(0.5, -0.3),
        ncol=2,
        handlelength=4,
    )
    ax = plt.gca()
    ax.spines['bottom'].set_position(('outward', 1))  # Move x-axis outward
    ax.spines['left'].set_position(('outward', 1))    # Move y-axis outward

    TICK_FONT_SIZE = 8
    # format x-axis
    plt.xlabel('Reasoning Steps', fontsize=10)
    plt.xticks(x[::5], df_mean.columns[::5], fontsize=TICK_FONT_SIZE)
    # set xlim
    plt.xlim(1, MAX_DIFFICULTY)
    plt.ylabel(metric.upper(), fontsize=8)
    plt.yticks(fontsize=TICK_FONT_SIZE)
    # set ylim
    plt.ylim(0, 1)
    plt.tight_layout()

    fig.subplots_adjust(left=0.17, right=0.95, bottom=0.3, top=0.95) #, wspace=0.3, hspace=0.3)
    fig_path = os.path.join(figures_dir, f'difficulty-{metric}.pdf')
    print(f"Saving to {os.path.abspath(fig_path)}")
    plt.savefig(fig_path)
