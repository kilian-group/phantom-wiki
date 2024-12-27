"""Script to format the accuracy of the models on the splits.

Generates a table with rows for each model, split, and seed combination.
Saves to a csv file called scores.csv in the scores directory of the output directory.

Example:
    python format_split_accuracy.py -od out --method zeroshot
"""

import os
from phantom_eval.utils import get_parser
from phantom_eval.evaluate_utils import get_evaluation_data
parser = get_parser()
args = parser.parse_args()
output_dir = args.output_dir
method = args.method
# get evaluation data from the specified output directory and method subdirectory
df = get_evaluation_data(output_dir, method)
# group by model, split, and seed
grouped = df.groupby(['_model', '_split', '_seed'])
# print the accuracy
acc = grouped[['EM','precision', 'recall', 'f1']].mean()
# add a column that counts the number of elements in the group
acc['count'] = grouped.size()
# print as markdown
print(acc.to_markdown())
# add a column at the end for the method
acc['method'] = method
# save to a csv file
scores_dir = os.path.join(output_dir, 'scores', method)
os.makedirs(scores_dir, exist_ok=True)
acc.to_csv(os.path.join(scores_dir, "scores.csv"))