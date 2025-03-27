"""Script to run IRCoT on PhantomWiki.

Reference: https://github.com/RUC-NLPIR/FlashRAG/blob/a5bf203359fcc1e5ea56c88307bbfb57b35fd5e5/examples/methods/run_exp.py#L438
"""

import os
from flashrag.config import Config
from flashrag.utils import get_dataset
from flashrag.pipeline import IRCOTPipeline

from phantom_eval import get_parser

parser = get_parser()
args = parser.parse_args()
output_dir = args.output_dir
split_list = args.split_list
model_name = args.model_name

if False:
    config_dict = {
        "data_dir": "dataset/",
        "dataset_name": "phantom-wiki-v1",
        "split": ["depth_20_size_50_seed_1"],
        "seed": 1,
        "index_path": "indexes/bm25/",
        "corpus_path": "indexes/depth_20_size_50_seed_1.jsonl",
        # TODO: change to vllm later, using gpt-4o only for debugging purpose
        "framework": "openai",
        "generator_model": "gpt-4o-mini-2024-07-18",
        "retrieval_method": "bm25",
        "bm25_backend": "bm25s",
        "metrics": ["em", "f1", "acc"],
        "retrieval_topk": 4,
        "save_intermediate_data": True,
    }
else:
    config_dict = {
        "data_dir": "dataset/",
        "dataset_name": "phantom-wiki-v1",
        "split": split_list,
        "seed": 1,
        "index_path": "indexes/bm25/",
        "corpus_path": "indexes/depth_20_size_50_seed_1.jsonl",
        "model2path": {
            model_name: "Llama-3.1-8B-Instruct"
        },
        "generator_model": model_name,
        "retrieval_method": "bm25",
        "bm25_backend": "bm25s",
        "metrics": ["em", "f1", "acc"],
        "retrieval_topk": 4,
        "save_intermediate_data": True,
    }

config = Config(config_dict=config_dict)

all_split = get_dataset(config)

preds_dir = os.path.join(output_dir, "preds")
os.makedirs(preds_dir, exist_ok=True)

for split in split_list:
    test_data = all_split[split]
    pipeline = IRCOTPipeline(config)
    output_dataset = pipeline.run(test_data,do_eval=True)   
    print("---generation output---")
    # print(output_dataset.pred)

    # import pdb; pdb.set_trace()
    # save the output dataset to a json file
    save_path = os.path.join(preds_dir, f"split={split}_model_name={model_name}.json")
    output_dataset.to_json(save_path)
