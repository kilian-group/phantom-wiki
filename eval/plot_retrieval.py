"""Script for plotting the accuracy of the models versus the universe size.

Generates a plot for each metric (EM, precision, recall, f1) with the universe size on the x-axis and the metric on the y-axis.
Saves the plots to the figures directory of the output directory.

Example:
    python eval/plot_size_accuracy.py -od out --method zeroshot
"""

# %%
import os
import logging
from phantom_eval import get_parser
from phantom_eval.utils import setup_logging
setup_logging("INFO")
from phantom_eval.evaluate_utils import get_evaluation_data, COLORS, LINESTYLES, pivot_mean_std, mean, std, MARKERS
from phantom_eval import plotting_utils
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as lines

import numpy as np
# TODO: use LaTeX for rendering (need to have LaTeX installed locally)

parser = get_parser()
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
figures_dir = os.path.join(output_dir, 'figures')
os.makedirs(figures_dir, exist_ok=True)
METRICS = [
    # 'EM', 
    # 'precision', 
    # 'recall', 
    'f1',
]

#
# RESTRICT TO LOW DEPTH QUESTIONS (i.e., questions generated from the CFG with depth=10)
# Note that the full dataset is generated using depth=20, but we can filter the
# question-answer pairs by the template used to generate the question, which is
# stored in the 'template' column of the dataframe.
# 
from nltk import CFG
from phantom_wiki.facts.templates import QA_GRAMMAR_STRING, generate_templates
grammar = CFG.fromstring(QA_GRAMMAR_STRING)
question_templates_10 = [' '.join(question) for question, _, _ in generate_templates(grammar, depth=10)]
# import pdb; pdb.set_trace()

for metric in METRICS:
    fig = plt.figure(figsize=(3.25, 2.75)) # exact dimensions of ICML single column width
    fig, axs = plt.subplots(1, 3, figsize=(6.75, 2.5))

    all_x = []

    for i, (name, methods) in enumerate([('Simple', plotting_utils.SIMPLE_METHODS), ('RAG', plotting_utils.RAG_METHODS), ('Agentic', plotting_utils.AGENTIC_METHODS)]):
        method_handles = {}
        for method in methods:
            # get evaluation data from the specified output directory and method subdirectory
            df = get_evaluation_data(output_dir, method, dataset)
            # import pdb; pdb.set_trace()
            if df.empty:
                logging.warning(f"No data found for {method}")
                continue
            if True:
                logging.warning("Reducing the difficulty by only including those questions that are generated from depth=10 templates")
                include = df.apply(lambda x: x['template'] in question_templates_10, axis=1)
                df = df[include]

            # group by model, size, data seed, and inference seed
            grouped = df.groupby(['_model', '_size', '_data_seed', '_seed'])
            # print the accuracy
            acc = grouped[['EM','precision', 'recall', 'f1']].mean()
            # add a column that counts the number of elements in the group
            acc['count'] = grouped.size()

            # get the mean and std of the accuracy for each model and split as follows:
            # first compute the mean across inference generation seeds
            acc_mean_std = acc.groupby(['_model', '_size', '_data_seed']).agg('mean')
            # second compute the mean and standard error across data generation seeds
            acc_mean_std = acc_mean_std.groupby(['_model', '_size']).agg([mean, std])
            acc_mean_std = acc_mean_std.reset_index()

            df_mean, df_std = pivot_mean_std(acc_mean_std, metric, independent_variable='_size')
            # For the paper only: if _model='deepseek-ai/deepseek-r1-distill-qwen-32b' and method="reasoning", then set method to zeroshot
            method_ = method.replace("reasoning", "zeroshot") if "reasoning" in method else method

            # use log2 scale for the x-axis
            all_x.extend(df_mean.columns.tolist())
            log2x = np.log2(df_mean.columns)
            # add the x values to a list
            for model_name, row in df_mean.iterrows():
                if model_name not in model_list:
                    continue
                y = row
                yerr = df_std.loc[model_name]
                # plt.errorbar(x, y, yerr=yerr, label=i, marker='o')
                # use a line plot instead of errorbar
                axs[i].plot(
                    log2x, y, 
                    label=f"{method_}+{model_name}", # cot+gemini-1.5-flash-002
                    color=COLORS[model_name], 
                    linestyle=LINESTYLES[model_name],
                    linewidth=1,
                )
                # Add scatter plot
                axs[i].scatter(
                    log2x[::2], y[::2],
                    color=COLORS[model_name],
                    s=20, #marker size
                    marker=MARKERS[method_],
                )
                axs[i].fill_between(log2x, y-yerr, y+yerr, alpha=0.1, color=COLORS[model_name])
            
            key = f"{plotting_utils.METHOD_ALIASES[method_]}"
            if key not in method_handles:
                method_handles[key] = lines.Line2D(
                    [0], [0],
                    color="black",
                    label=key, 
                    linestyle='none',
                    marker=MARKERS[method_],
                    markersize=4,
                )
        axs[i].legend(
            handles=[v for _, v in method_handles.items()],
            fontsize=plotting_utils.LEGEND_FONT_SIZE,
            loc='upper right',
            ncol=1,
            handlelength=2,
        )

        axs[i].spines['bottom'].set_position(('outward', 1))  # Move x-axis outward
        axs[i].spines['left'].set_position(('outward', 1))    # Move y-axis outward

        # format y-axis
        if i == 0:
            axs[i].set_ylabel(metric.upper(), fontsize=8)
        axs[i].set_ylim(0, 1)
        # only add tickes at 0, 0.5, 1 
        axs[i].set_yticks([0, 0.5, 1])
        axs[i].set_yticklabels([0, 0.5, 1], fontsize=plotting_utils.TICK_FONT_SIZE)
        # axs[i].tick_params(axis='y', labelsize=plotting_utils.TICK_FONT_SIZE)
        # set title
        axs[i].set_title(name, fontsize=plotting_utils.LABEL_FONT_SIZE)

        if i==0:
            # Add vertical line at x=500 to indicate the max context length of 128k models
            axs[i].axvline(x=np.log2(500), color='gray', linestyle='--', linewidth=0.1)
            axs[i].text(np.log2(500), 1, '128k', fontsize=6, color='gray')

            # add vertical line at x=3125 to indicate the max context length of 1M models
            axs[i].axvline(x=np.log2(3125), color='gray', linestyle='--', linewidth=0.1)
            axs[i].text(np.log2(3125), 1, '1M', fontsize=6, color='gray')
        
    all_x = sorted(list(set(all_x)))
    for i in range(3):
        # format x-axis
        axs[i].set_xlabel('Universe Size', fontsize=plotting_utils.LABEL_FONT_SIZE)
        # Only add labels at 10, but keep the ticks at all points        
        ticks, labels = zip(*[(t, f"$10^{int(np.log10(l))}$" if np.log10(l).is_integer() else "") for t, l in zip(np.log2(all_x), all_x)])
        axs[i].set_xticks(ticks)
        axs[i].set_xticklabels(labels, fontsize=plotting_utils.TICK_FONT_SIZE)

    # attach the model legend to the entire figure instead of any individual subplot
    model_handles = []
    for model in model_list:
        key = f"{plotting_utils.MODEL_ALIASES[model]}"
        model_handles.append( lines.Line2D(
            [0], [0],
            color=COLORS[model],
            label=key, 
            linestyle=LINESTYLES[model],
            linewidth=1,
        ) )
    fig.legend(
        handles=model_handles,
        fontsize=plotting_utils.LEGEND_FONT_SIZE,
        loc='lower center',
        ncol=6,
        handlelength=4,
    )
    plt.tight_layout()
    plt.subplots_adjust(left=0.1, right=0.95, top=0.9, wspace=0.3)  # Adjust horizontal space between subplots and reduce padding to the left and right

    fig_path = os.path.join(figures_dir, f'size-{metric}.pdf')
    logging.info(f"Saving to {os.path.abspath(fig_path)}")
    plt.savefig(fig_path)
