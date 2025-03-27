"""Script to run IRCoT on PhantomWiki.

Reference: https://github.com/RUC-NLPIR/FlashRAG/blob/a5bf203359fcc1e5ea56c88307bbfb57b35fd5e5/examples/methods/run_exp.py#L438
"""


from flashrag.config import Config
from flashrag.utils import get_dataset
from flashrag.pipeline import IRCOTPipeline


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
        "split": ["depth_20_size_50_seed_1"],
        "seed": 1,
        "index_path": "indexes/bm25/",
        "corpus_path": "indexes/depth_20_size_50_seed_1.jsonl",
        "model2path": {
            "llama3.1-8b-instruct": "Llama-3.1-8B-Instruct"
            # "llama3.1-8b-instruct": "~/.cache/huggingface/hub/models--meta-llama--llama-3.1-8b-instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659/"
        },
        "generator_model": "llama3.1-8b-instruct",
        "retrieval_method": "bm25",
        "bm25_backend": "bm25s",
        "metrics": ["em", "f1", "acc"],
        "retrieval_topk": 4,
        "save_intermediate_data": True,
    }

config = Config(config_dict=config_dict)

all_split = get_dataset(config)
test_data = all_split['depth_20_size_50_seed_1']
pipeline = IRCOTPipeline(config)

output_dataset = pipeline.run(test_data,do_eval=True)
print("---generation output---")
print(output_dataset.pred)

import pdb; pdb.set_trace()
# save the output dataset to a json file
output_dataset.to_json("output_dataset.json")
