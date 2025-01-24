"""Script to format the accuracy of the models on the splits.

Generates a table with rows for each model, split, and seed combination.
Saves to a csv file called scores.csv in the scores directory of the output directory.

Example:
    python eval/format_split_accuracy.py -od out --method zeroshot
"""
import pdb; pdb.set_trace()
import os
import pandas as pd
# from phantom_eval import get_parser
from phantom_eval.evaluate_utils import get_evaluation_data
from tabulate import tabulate
from argparse import ArgumentParser
parser = ArgumentParser()
# Dataset params
parser.add_argument("--dataset", type=str, default="mlcore/phantom-wiki-v0.3",
                    help="Dataset name")
parser.add_argument("--output_dir", "-od", default="out",
                help="Path to read/write the outputs")
parser.add_argument(
    "--method_list", 
    nargs="+", 
    default=["zeroshot"], 
    help="Method to plot"
)
parser.add_argument(
    "--model_list",
    nargs="+",
    default=["gemini-1.5-flash-002"],
    help="List of models to plot"
)
args = parser.parse_args()
output_dir = args.output_dir
method_list = args.method_list
model_list = args.model_list
dataset = args.dataset
METRICS = [
    'EM',
    # 'precision', 
    # 'recall', 
    'f1'
]

acc_list = []
for method in method_list:
    # get evaluation data from the specified output directory and method subdirectory
    df = get_evaluation_data(output_dir, method, dataset)
    df = df[df['_model'].isin(model_list)]
    # group by model, split, and seed
    grouped = df.groupby(['_model', '_depth', '_size', '_data_seed', '_seed'])
    # print the accuracy
    acc = grouped[METRICS].mean()
    # add a column that counts the number of elements in the group
    acc['count'] = grouped.size()
    # print as markdown
    print(acc.to_markdown())
    # add a column at the end for the method
    acc['method'] = method
    acc_list.append(acc)

# concatenate all the dataframes
acc = pd.concat(acc_list)
print("Accuracies:")
print(acc.to_latex())
print(tabulate(acc, tablefmt="github", headers="keys"))

# save to a csv file
scores_dir = os.path.join(output_dir, 'scores')
os.makedirs(scores_dir, exist_ok=True)
acc.to_csv(os.path.join(scores_dir, "scores.csv"))