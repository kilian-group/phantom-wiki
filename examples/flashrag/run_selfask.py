import os
import json
from pathlib import Path

from flashrag.config import Config
from flashrag.utils import get_dataset
from flashrag.pipeline import SelfAskPipeline

split_list = ["depth_20_size_50_seed_1"]
# model_name = "Qwen/Qwen2-7B-Instruct"
model_name = "meta-llama/Llama-3.1-8B-Instruct"
output_dir = "selfask_output"
seed = 1

config_dict = {
    "data_dir": "dataset/",
    "dataset_name": "phantom-wiki-v1",
    "split": split_list,
    "seed": 1,
    "gpu_id": "0,1,2,3,4,5,6,7",
    "index_path": "indexes/bm25/",
    "corpus_path": "indexes/depth_20_size_50_seed_1.jsonl",
    "model2path": {
        # model_name: "Llama-3.1-8B-Instruct",
    },
    # "framework": "openai",
    "generator_model": model_name,
    "retrieval_method": "bm25",
    "bm25_backend": "bm25s",
    "metrics": ["em", "f1", "acc"],
    "retrieval_topk": 4,
    "save_intermediate_data": True,
}

config = Config(config_dict = config_dict)

all_split = get_dataset(config)

preds_dir = os.path.join(output_dir, "preds")
os.makedirs(preds_dir, exist_ok=True)

for split, test_data in all_split.items():
    pipeline = SelfAskPipeline(config, max_iter=15, single_hop=False)
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
    pred_path = Path(os.path.join(output_dir, "preds", "selfask", f"{run_name}.json"))
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
                "dataset": "phantom-wiki-v1",
                "split": split,
                "batch_size": batch_size,
                "batch_number": batch_number,
                "type": None,
            },
            "inference_params": {
                "seed": seed,
            },
            "model_kwargs": {}, # model_kwargs,
            "agent_kwargs": {}, # agent_kwargs,
            "usage": {}, # responses[i].usage,
        }

    print(f"Saving predictions to {pred_path}...")
    with open(pred_path, "w") as f:
        json.dump(preds, f, indent=4)
        f.flush()