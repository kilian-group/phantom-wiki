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
parser = get_parser()
args = parser.parse_args()
output_dir = args.output_dir
method = args.method
dataset = args.dataset
# get evaluation data from the specified output directory and method subdirectory
df = get_evaluation_data(output_dir, method, dataset)

# %%
# save to a csv file
scores_dir = os.path.join(output_dir, 'scores', method)
os.makedirs(scores_dir, exist_ok=True)

# %%
# get accuracies by type
# group by model, split, seed, type
COLS = [
    '_model', '_depth', '_size', '_data_seed', '_seed', 
    '_type', 'template', 'hops'
]
# NOTE: to compute std error across data generation seeds and/or inference generation seeds, use the following:
# COLS = [
#     '_model', '_depth', '_size',
#     '_type', 'template', 'hops'
# ]
acc_by_type = df.groupby(COLS)[['EM','precision', 'recall', 'f1']].mean()
# compute the mean and std across seeds
# drop '_seed' from COLS
COLS.remove('_seed')
acc_by_type_mean_std = acc_by_type.groupby(COLS).agg(['mean', 'std'])
# print the accuracy
print(acc_by_type_mean_std.to_markdown())
# collapse multi-index columns
acc_by_type_mean_std.columns = acc_by_type_mean_std.columns.to_flat_index()
# add a column at the end for the method
acc_by_type_mean_std['method'] = method
# save to a csv file
acc_by_type_mean_std.to_csv(os.path.join(scores_dir, "scores_by_type.csv"))
