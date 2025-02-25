"""Script to format the accuracy of the models on the splits, stratfied by type.

Generates a table with rows for each model, split, type, and seed combination.
Saves to a csv file called scores_by_type.csv in the scores directory of the output directory.
Includes the question template for improved readability.

Example:
    python eval/format_split_type_accuracy.py -od out --method zeroshot
"""

# %%
import os

from phantom_eval import get_parser
from phantom_eval.evaluate_utils import get_evaluation_data
from phantom_eval.utils import setup_logging

parser = get_parser()
args = parser.parse_args()
output_dir = args.output_dir
method = args.method
dataset = args.dataset
log_level = args.log_level
setup_logging(log_level)
# get evaluation data from the specified output directory and method subdirectory
df = get_evaluation_data(output_dir, method, dataset)

# %%
# get accuracies by type
# group by model, split, seed, type
COLS = [
    "_model",
    "_depth",
    "_size",
    "_data_seed",
    "_seed",
    "_type",
    "template",
    # "hops",
]
# NOTE: to compute std error across data generation seeds and/or inference generation seeds, use the
# following:
# COLS = [
#     '_model', '_depth', '_size',
#     '_type', 'template', 'hops'
# ]
grouped = df.groupby(COLS)
# compute the mean and std across seeds
acc = grouped[["EM", "precision", "recall", "f1"]].agg(["mean", "std"])
# drop '_seed' from COLS
# COLS.remove("_seed")
# add a column that counts the number of elements in the group
acc["count"] = grouped.size()
# collapse multi-index columns
acc.columns = acc.columns.to_flat_index()
# add a column at the end for the method
acc["method"] = method
# print the accuracy
print(acc.to_markdown())

# save to a csv file
scores_dir = os.path.join(output_dir, "scores", method)
os.makedirs(scores_dir, exist_ok=True)
save_path = os.path.join(scores_dir, "scores_by_type.csv")
print(f"Saving scores by type to {save_path}")
acc.to_csv(save_path)
