"""Script to format the accuracy of the models on the splits.

Generates a table with rows for each model, split, and seed combination.
Saves to a csv file called scores.csv in the scores directory of the output directory.

Example:
    python eval/format_split_accuracy.py -od out --method zeroshot
"""
import os
import pandas as pd
# from phantom_eval import get_parser
from phantom_eval.evaluate_utils import get_evaluation_data, mean, std
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
    default=["zeroshot", "cot", "zeroshot-retriever", "cot-retriever"], 
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
METRICS = [
    # 'EM',
    # 'precision', 
    # 'recall', 
    'f1'
]

results = []
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
    acc_mean_std = acc.groupby(['_model', '_depth', '_size', '_data_seed']).agg('mean')
    # second compute the mean and standard error across data generation seeds
    AGG = {
        m: lambda x: f"{mean(x)*100:.2f} ± {std(x)*100:.2f}" for m in METRICS
    }
    AGG = {**AGG, 'count': lambda x: int(mean(x))}
    acc_mean_std = acc_mean_std.groupby(['_model', '_depth', '_size']).agg(AGG)
    acc_mean_std = acc_mean_std.reset_index()
    # add a column at the end for the method
    acc_mean_std['method'] = method
    results.append(acc_mean_std)

# concatenate all the dataframes
results = pd.concat(results)
# reset index
results = results.reset_index(drop=True)

# create table with models as rows and methods as columns
results = results.pivot_table(index=['_model'], columns='method', values=METRICS, aggfunc='first')
# currently the resulting columns are (metric, method)
# we want them to be just (method)
results.columns = results.columns.droplevel(0)
# change the order of columns to be the same as method_list
results = results[[method for method in method_list if method in results.columns]]

print("Accuracies:")
print(results.to_latex())
print(tabulate(results, tablefmt="github", headers="keys"))

# save to a csv file
scores_dir = os.path.join(output_dir, 'scores')
os.makedirs(scores_dir, exist_ok=True)
results.to_csv(os.path.join(scores_dir, "scores.csv"))