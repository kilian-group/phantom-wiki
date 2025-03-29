"""
Files in /share/nikola/phantom-wiki/data/wiki-llama-paraphrased don't follow the same JSON schema
as the original PW datasets. This script fixes the format of those JSON files to match the original.

NOTE: This script is a hack to fix the format. The rephrasing script in src/phantom_wiki/rephrase.py
should fix the format in the future.

For example, the original dataset has the following format:
/share/nikola/phantom-wiki/data/wiki-llama-paraphrased/llama3.3-70B_articles_depth_20_size_50_seed_1_short_prompt.json
contains
```
[
    {"title": "Aida Wang", "article": "..."},
    { ... },
    ...
]
```

This script updates the JSON format to add an empty "facts" field to each article.
```
[
    {"title": "Aida Wang", "article": "...", "facts": []},
    { ... },
    ...
]
```

and then saves the file as "articles.json" to the folder:
```
/share/nikola/phantom-wiki/data/wiki-llama-paraphrased-short-prompt/depth_20_size_50_seed_1/
|- articles.json
|- facts.pl
|- questions.json
|- timings.csv
```

All files except "articles.json" are copied from the original dataset at location `/share/nikola/phantom-wiki/data/wiki-v1/depth_20_size_50_seed_1/`.

Finally,
run phantom_eval with this:
```
python -m phantom_eval --server vllm --method zeroshot --dataset /share/nikola/phantom-wiki/data/wiki-llama-paraphrased/short-prompt --from_local --split_list depth_20_size_50_seed_1 depth_20_size_50_seed_2 depth_20_size_50_seed_3 -od out-0329-rephrased-short --model_name meta-llama/llama-3.3-70b-instruct
```
"""

import argparse
import json
import os
import shutil
from pathlib import Path

# Input and output paths
ORIGINAL_DATASET_DIR = "/share/nikola/phantom-wiki/data/wiki-v1/"
PARAPHRASED_JSON_DIR = "/share/nikola/phantom-wiki/data/wiki-llama-paraphrased/"
# llama3.3-70B_articles_depth_20_size_50_seed_1_short_prompt.json"
# llama3.3-70B_articles_depth_20_size_50_seed_1_long_prompt.json"
# NOTE: change "short" to "long" below for long prompt
OUTPUT_DIR = "/share/nikola/phantom-wiki/data/wiki-llama-paraphrased/short-prompt/"


def fix_json_format(split: str):
    # Read the paraphrased articles
    # NOTE: change "short" to "long" below for long prompt
    paraphrased_json_fname = Path(PARAPHRASED_JSON_DIR) / f"llama3.3-70B_articles_{split}_short_prompt.json"
    with open(paraphrased_json_fname) as f:
        articles = json.load(f)

    # Add empty facts field to each article
    for article in articles:
        article["facts"] = []

    # Save the modified articles
    with open(os.path.join(OUTPUT_DIR, split, "articles.json"), "w") as f:
        json.dump(articles, f, indent=2)


def copy_other_files(split: str):
    # Files to copy from original dataset
    files_to_copy = ["facts.pl", "questions.json", "timings.csv"]

    for file in files_to_copy:
        src = os.path.join(ORIGINAL_DATASET_DIR, split, file)
        dst = os.path.join(OUTPUT_DIR, split, file)
        shutil.copy2(src, dst)


def main(args):
    for split in args.split_list:
        # Create output directory for each split
        split_output_dir = os.path.join(OUTPUT_DIR, split)
        Path(split_output_dir).mkdir(parents=True, exist_ok=True)

        # Fix JSON format and copy other files
        fix_json_format(split)
        copy_other_files(split)
        print(f"Format fixed and files copied to {split_output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix JSON format and copy files.")
    parser.add_argument(
        "--split_list",
        type=list,
        default=["depth_20_size_50_seed_1", "depth_20_size_50_seed_2", "depth_20_size_50_seed_3"],
        help="List of dataset splits to process.",
    )

    args = parser.parse_args()
    main(args)
