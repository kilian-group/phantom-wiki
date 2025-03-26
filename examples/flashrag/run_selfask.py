from flashrag.config import Config
from flashrag.utils import get_dataset
from flashrag.pipeline import SelfAskPipeline


config_dict = {
    "data_dir": "indexes/",
    "dataset_name": "",
    "split": ['depth_20_size_50_seed_1'],
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

config = Config(config_dict = config_dict)

all_split = get_dataset(config)
test_data = all_split['depth_20_size_50_seed_1']
pipeline = SelfAskPipeline(config)

output_dataset = pipeline.run(test_data,do_eval=True)
print("---generation output---")
print(output_dataset.pred)