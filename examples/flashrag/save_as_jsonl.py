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
from tqdm import tqdm

from phantom_eval.utils import load_data
from phantom_eval import get_parser

parser = get_parser()
args = parser.parse_args()
split_list = args.split_list
dataset = args.dataset
index_dir = "indexes"  # args.output_dir
from_local = args.from_local

assert len(split_list) == 1, "Only one split is supported"
split = split_list[0]

os.makedirs(index_dir, exist_ok=True)
dataset_dir = os.path.join("dataset", dataset.split("/")[-1])
os.makedirs(dataset_dir, exist_ok=True)

for split in split_list:
    ds = load_data(dataset, split, from_local)

    corpus_path = os.path.join(index_dir, f"{split}.jsonl")
    with open(corpus_path, "w") as f:
        for item in tqdm(ds['text'].to_list(), desc="Saving corpus"):
            f.write(json.dumps({
                "id": item['title'],
                "contents": item['article']
            }) + "\n")

    qa_path = os.path.join(dataset_dir, f"{split}.jsonl")
    with open(qa_path, "w") as f:
        for item in tqdm(ds['qa_pairs'].to_list(), desc="Saving question-answer pairs"):
            f.write(json.dumps({
                "id": item['id'],
                "question": item['question'],
                "golden_answers": item['answer']
            }) + "\n")
