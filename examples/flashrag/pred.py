"""Script to run IRCoT on PhantomWiki.

This script performs both the indexing and the inference.

NOTE: please first clone the HF model repo to this directory.
TODO: fix bug in FlashRAG that requires the model repo to be cloned.

Example usage:
```bash
python pred.py --dataset DATASET --split_list SPLIT --output_dir OUTPUT_DIR --model_name MODEL_NAME
```
NOTE: when using local data, add the `--from_local` flag.
"""

import os
import json
from pathlib import Path
from tqdm import tqdm
from flashrag.config import Config
from flashrag.utils import get_dataset
from flashrag.pipeline import IRCOTPipeline
from flashrag.retriever.index_builder import Index_Builder
from argparse import ArgumentParser
from phantom_eval import get_parser
from phantom_eval.utils import load_data

parser = ArgumentParser(parents=[get_parser()], conflict_handler="resolve")
parser.add_argument("--method", type=str.lower, default="ircot")
args = parser.parse_args()
output_dir = Path(args.output_dir)
dataset = args.dataset
split_list = args.split_list
model_name = args.model_name
from_local = args.from_local
method = args.method

index_dir = output_dir / "indexes"
index_dir.mkdir(parents=True, exist_ok=True)
dataset_name = dataset.split("/")[-1]
dataset_dir = output_dir / "dataset" / dataset_name
dataset_dir.mkdir(parents=True, exist_ok=True)
preds_dir = output_dir / "preds"
preds_dir.mkdir(parents=True, exist_ok=True)

for split in split_list:
    print(f"Indexing dataset {dataset} :: {split}...")
    ds = load_data(dataset, split, from_local)
    corpus_path = os.path.join(index_dir, f"{split}.jsonl")
    with open(corpus_path, "w") as f:
        for item in tqdm(ds['text'].to_list(), desc="Saving corpus"):
            f.write(json.dumps({
                "id": item['title'],
                "contents": item['article']
            }) + "\n")
        f.flush()
    index_builder = Index_Builder(
        retrieval_method="bm25",
        model_path=None,
        corpus_path=corpus_path,
        save_dir=index_dir,
        max_length=180,
            batch_size=512,
            use_fp16=False,
        )
    index_builder.build_index()

    qa_path = os.path.join(dataset_dir, f"{split}.jsonl")
    with open(qa_path, "w") as f:
        for item in tqdm(ds['qa_pairs'].to_list(), desc="Saving question-answer pairs"):
            f.write(json.dumps({
                "id": item['id'],
                "question": item['question'],
                "golden_answers": item['answer']
            }) + "\n")

for seed in args.inf_seed_list:

    config_dict = {
        "data_dir": os.path.join(output_dir, "dataset"),
        "dataset_name": dataset_name,
        "split": split_list,
        "seed": seed,
        "index_path": os.path.join(index_dir, "bm25"),
        "corpus_path": os.path.join(index_dir, "depth_20_size_50_seed_1.jsonl"),
        "model2path": {
            model_name: "Llama-3.1-8B-Instruct"
        },
        "generator_model": model_name,
        "generator_max_input_len": args.inf_vllm_max_model_len if args.inf_vllm_max_model_len else 2048,
        "retrieval_method": "bm25",
        "bm25_backend": "bm25s",
        "metrics": ["em", "f1", "acc", "precision", "recall"],
        "retrieval_topk": 4,
        "save_intermediate_data": True,
    }

    config = Config(config_dict=config_dict)
    all_split = get_dataset(config)

    for split, test_data in all_split.items():
        pipeline = IRCOTPipeline(config)
        output_dataset = pipeline.run(test_data,do_eval=True)

        # save the output dataset to a json file
        batch_size = len(test_data)
        batch_number = 1
        run_name = (
            f"split={split}"
            + f"__model_name={model_name.replace('/', '--')}"
            + f"__bs={batch_size}"
            + f"__bn={batch_number}"
            + f"__seed={seed}"
        )
        pred_path = output_dir / "preds" / method / f"{run_name}.json"
        pred_path.parent.mkdir(parents=True, exist_ok=True)
        # output_dataset.to_json(pred_path)

        preds = {}
        for item in output_dataset.data:
            item_dict = item.to_dict()
            uid = item_dict['id']
            preds[uid] = {
                "true": item_dict['golden_answers'],
                "pred": item_dict['output']['pred'],
                "error": None,  # responses[i].error,
                "interaction": [],  # interactions[i].model_dump() if interactions else [],
                "output": item_dict['output'],  # NOTE: save output from FlashRAG
                "metadata": {
                    "model": model_name,
                    "dataset": dataset,
                    "split": split,
                    "batch_size": batch_size,
                    "batch_number": batch_number,
                    "type": None,
                },
                "inference_params": {}, # inf_gen_config.model_dump(),
                "model_kwargs": {}, # model_kwargs,
                "agent_kwargs": {}, # agent_kwargs,
                "usage": {}, # responses[i].usage,
            }

        print(f"Saving predictions to {pred_path}...")
        with open(pred_path, "w") as f:
            json.dump(preds, f, indent=4)
            f.flush()
