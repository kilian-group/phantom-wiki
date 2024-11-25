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
METADATA = ['model', 'split', 'batch_size', 'batch_number']
for filename in files:
    print(f"Reading from {filename}...")
    df = pd.read_json(filename, orient='index')
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
from phantom_eval.score import match
df['score'] = df.apply(lambda x: match(x['pred'], ', '.join(x['true'])), axis=1)
print(df)
# group by model and split
grouped = df.groupby(['_model', '_split'])
# print the accuracy
print(grouped['score'].mean())