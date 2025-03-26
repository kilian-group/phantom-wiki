"""Convert the PhantomWiki corpus to a JSONL file.

Reference: https://github.com/RUC-NLPIR/FlashRAG?tab=readme-ov-file#corpus-construction

Example usage:
```bash
python save_corpus_as_jsonl.py --dataset DATASET_NAME_OR_PATH --split_list SPLIT_LIST
```
If using local dataset, add the `--from_local` flag.
"""

import os
import json

from phantom_eval.utils import load_data
from phantom_eval import get_parser

parser = get_parser()
args = parser.parse_args()
split_list = args.split_list
dataset = args.dataset
output_dir = args.output_dir
from_local = args.from_local

assert len(split_list) == 1, "Only one split is supported"
split = split_list[0]

os.makedirs(output_dir, exist_ok=True)

for split in split_list:
    ds = load_data(dataset, split, from_local)

    save_path = os.path.join(output_dir, f"{split}.jsonl")
    print(f"Saving corpus to {save_path}")
    with open(save_path, "w") as f:
        for item in ds['text'].to_list():
            f.write(json.dumps({
                "id": item['title'],
                "contents": item['article']
            }) + "\n")
