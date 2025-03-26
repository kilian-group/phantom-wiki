"""Script to run IRCoT on PhantomWiki.

Reference: https://github.com/RUC-NLPIR/FlashRAG/blob/a5bf203359fcc1e5ea56c88307bbfb57b35fd5e5/examples/methods/run_exp.py#L438
"""


from flashrag.config import Config
from flashrag.utils import get_dataset
from flashrag.pipeline import IRCOTPipeline


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
# save_note = "ircot"
# config_dict = {
#     "save_note": save_note,
#     "gpu_id": 0,
#     "dataset_name": "phantom-wiki-v1",
#     "split": "depth_20_size_50_seed_1",
# }
config = Config(config_dict=config_dict)
# import pdb; pdb.set_trace()

all_split = get_dataset(config)
test_data = all_split['depth_20_size_50_seed_1']
pipeline = IRCOTPipeline(config)

output_dataset = pipeline.run(test_data,do_eval=True)
print("---generation output---")
print(output_dataset.pred)
