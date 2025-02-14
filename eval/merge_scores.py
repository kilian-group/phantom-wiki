from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument(
    "--output_dir", "-od", default="out", type=str, help="Path to directory containing all outputs"
)
args, _ = parser.parse_known_args()
output_dir = args.output_dir

import os
from glob import glob

import pandas as pd

scores_files = glob(os.path.join(output_dir, "scores/*/scores.csv"))

df_list = []
for file_path in scores_files:
    df = pd.read_csv(file_path)
    df_list.append(df)
df = pd.concat(df_list, ignore_index=True)

# add additional columns for depth, size, split
import re

df["_split_depth"] = df["_split"].apply(lambda x: re.match(r"depth_(\d+)_size_(\d+)_seed_(\d+)", x).group(1))
df["_split_size"] = df["_split"].apply(lambda x: re.match(r"depth_(\d+)_size_(\d+)_seed_(\d+)", x).group(2))
df["_split_seed"] = df["_split"].apply(lambda x: re.match(r"depth_(\d+)_size_(\d+)_seed_(\d+)", x).group(3))
# reorder the columns so that all columns starting with _split are at the front
split_cols = [col for col in df.columns if col.startswith("_split")]
other_cols = [col for col in df.columns if not col.startswith("_split")]
df = df[split_cols + other_cols]

df.to_csv(os.path.join(output_dir, "scores", "all_scores.csv"), index=False)
