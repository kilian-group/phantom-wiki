"""Script to format the accuracy of the models on the splits.

Generates a table with rows for each model, split, and seed combination.
Prints out the leaderboard in latex and markdown formats -- used in the paper.

Example:
    python eval/format_leaderboard.py -od out
"""
import os

import pandas as pd

from phantom_eval import get_parser
from phantom_eval.utils import setup_logging

setup_logging("INFO")
from tabulate import tabulate

from phantom_eval import plotting_utils
from phantom_eval.evaluate_utils import get_evaluation_data, mean, std

parser = get_parser()
parser.add_argument(
    "--method_list", nargs="+", default=plotting_utils.DEFAULT_METHOD_LIST, help="Method to plot"
)
parser.add_argument(
    "--model_list", nargs="+", default=plotting_utils.DEFAULT_MODEL_LIST, help="List of models to plot"
)
args = parser.parse_args()
output_dir = args.output_dir
method_list = args.method_list
model_list = args.model_list
dataset = args.dataset
METRICS = [
    # 'EM',
    # 'precision',
    # 'recall',
    "f1"
]
SIZE_LIST = [50, 500, 5000]

df_list = []
for method in method_list:
    # get evaluation data from the specified output directory and method subdirectory
    df = get_evaluation_data(output_dir, method, dataset)
    if df.empty:
        print(f"No data found for method {method}")
        continue
    # filter by model
    df = df[df["_model"].isin(model_list)]
    # filter by depth
    df = df[df["_depth"] == 20]
    # group by model, split, and seed
    grouped = df.groupby(["_model", "_depth", "_size", "_data_seed", "_seed"])
    # print the accuracy
    acc = grouped[METRICS].mean()
    # add a column that counts the number of elements in the group
    acc["count"] = grouped.size()
    # Save the accuracy to a csv file
    acc.to_csv(os.path.join(output_dir, f"{method}_preds_stats.csv"))
    # print as markdown
    acc_mean_std = acc.groupby(["_model", "_depth", "_size", "_data_seed"]).agg("mean")
    # second compute the mean and standard error across data generation seeds
    AGG = {m: lambda x: f"{mean(x)*100:.2f} ± {std(x)*100:.2f}" for m in METRICS}
    AGG = {**AGG, "count": lambda x: int(mean(x))}
    acc_mean_std = acc_mean_std.groupby(["_model", "_depth", "_size"]).agg(AGG)
    acc_mean_std = acc_mean_std.reset_index()
    # add a column at the end for the method
    # For the paper only: if _model='deepseek-ai/deepseek-r1-distill-qwen-32b' and method="reasoning",
    # then set method to zeroshot
    acc_mean_std["method"] = plotting_utils.SIMPLIFIED_METHODS[method]
    df_list.append(acc_mean_std)

# concatenate all the dataframes
df_all = pd.concat(df_list)
# reset index
df_all = df_all.reset_index(drop=True)

# only consider universe sizes in SIZE_LIST
results = df_all[df_all["_size"].isin(SIZE_LIST)]
# use model aliases
results["_model"] = results["_model"].apply(lambda x: plotting_utils.MODEL_ALIASES.get(x, x))
# create table with models as rows and methods as columns
results = results.pivot_table(index=["_size", "_model"], columns="method", values=METRICS, aggfunc="first")
# replace the column name _size with "Universe Size"
results = results.rename_axis(index=["Universe Size", "Model"])
# currently the resulting columns are (metric, method)
# we want them to be just (method)
results.columns = results.columns.droplevel(0)
# change the order of columns to be the same as method_list
results = results[[method for method in method_list if method in results.columns]]


# add a level to the columns representing whether it's an in-context, rag, or agentic method
def get_method_type(method):
    if method in plotting_utils.INCONTEXT_METHODS:
        method_type = "In-Context"
    elif method in plotting_utils.RAG_METHODS:
        method_type = "RAG"
    elif method in plotting_utils.AGENTIC_METHODS:
        method_type = "Agentic"
    else:
        method_type = "Other"
    # rename the columns to the method aliases
    return method_type, plotting_utils.METHOD_LATEX_ALIASES.get(method, method)


method_types = [get_method_type(method) for method in results.columns]
results.columns = pd.MultiIndex.from_tuples(method_types, names=["Type", "Method"])
# # DeepSeek with CoT and React should be filled with a dash
# deepseek_rows = [x[1] in [plotting_utils.MODEL_ALIASES['deepseek-ai/deepseek-r1-distill-qwen-32b']]
# for x in results.index]
# NON_ZEROSHOT_METHODS = [plotting_utils.METHOD_LATEX_ALIASES[m] for m in plotting_utils.DEFAULT_METHOD_LIST
# if 'zeroshot' not in m]
# deepseek_cols = [x for x in results.columns if x[1] in NON_ZEROSHOT_METHODS] # only reasoning
# results.loc[deepseek_rows, deepseek_cols] = '---'
# Llama-3.3-70B, GPT-4o zeroshot and cot beyond size 5000 should be filled with \ooc
MODELS_128K = [
    plotting_utils.MODEL_ALIASES["meta-llama/llama-3.3-70b-instruct"],
    plotting_utils.MODEL_ALIASES["gpt-4o-2024-11-20"],
]
rows_128k = [(x[0] > 500 and x[1] in MODELS_128K) for x in results.index]
cols_128k = [
    x
    for x in results.columns
    if x[1] in [plotting_utils.METHOD_LATEX_ALIASES[m] for m in plotting_utils.INCONTEXT_METHODS]
]  # only zeroshot and reasoning
results.loc[rows_128k, cols_128k] = "\\ooc"
# Gemini t and cot beyond size 5000 should be filled with \ooc
rows_1M = [
    (x[0] > 500 and x[1] in [plotting_utils.MODEL_ALIASES["gemini-1.5-flash-002"]]) for x in results.index
]
cols_1M = [
    x
    for x in results.columns
    if x[1] in [plotting_utils.METHOD_LATEX_ALIASES[m] for m in plotting_utils.INCONTEXT_METHODS]
]  # only zeroshot and reasoning
results.loc[rows_1M, cols_1M] = "\\ooc"

# reset the index
results = results.reset_index()

print("Accuracies:")
latex_str = results.to_latex(index=False, column_format="c" * len(results.columns))
lines = latex_str.splitlines()
new_lines = [lines[0], lines[1]]  # add the header lines

# Add \midrule between changes in the universe size value
last_size = None
for line in lines[2:]:
    parts = line.split("&")
    current_size = parts[0].strip()
    if current_size != last_size and current_size.isdigit():
        new_lines.append(r"\midrule")
    last_size = current_size
    new_lines.append(line)

print("\n".join(new_lines))

print(tabulate(results, tablefmt="github", headers="keys", showindex=False))

# # save to a csv file
# scores_dir = os.path.join(output_dir, 'scores')
# os.makedirs(scores_dir, exist_ok=True)
# results.to_csv(os.path.join(scores_dir, "scores.csv"))
