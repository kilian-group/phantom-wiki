# Script to aggregate prediction files and compute metrics
# To run:
#   python evaluate.py -m <model name> -od <path to folder containing outputs>

from phantom_eval.utils import (get_parser)
parser = get_parser()
args, _ = parser.parse_known_args()
output_dir = args.output_dir

from glob import glob
import pandas as pd
# get all files in the output directory
files = glob(f"{output_dir}/preds/*.json")
df_list = []
# keys in the metadata to create new columns
METADATA = ['model', 'split', 'batch_size', 'batch_number', 'seed']
for filename in files:
    print(f"Reading from {filename}...")
    df = pd.read_json(filename, orient='index', dtype=False)
    # add new columns corresponding to the metadata
    for key in METADATA:
        df["_" + key] = df['metadata'].apply(lambda x: x[key])
    # drop the metadata column
    df = df.drop(columns=['metadata'])
    df_list.append(df)
# concatenate all dataframes
df = pd.concat(df_list)
# print(df.columns)

# compute scores
from phantom_eval.score import (match,
                                precision,
                                recall,
                                f1)
# join the true answers with the appropriate seperator
# since the scoring functions expect strings
sep = ', '
df['EM'] = df.apply(lambda x: match(x['pred'], sep.join(x['true'])), axis=1)
df['precision'] = df.apply(lambda x: precision(x['pred'], sep.join(x['true'])), axis=1)
df['recall'] = df.apply(lambda x: recall(x['pred'], sep.join(x['true'])), axis=1)
df['f1'] = df.apply(lambda x: f1(x['pred'], sep.join(x['true'])), axis=1)
print(df)
# group by model and split
grouped = df.groupby(['_model', '_split', '_seed'])
# print the accuracy
acc = grouped[['EM','precision', 'recall', 'f1']].mean()
# print as markdown
print(acc.to_markdown())