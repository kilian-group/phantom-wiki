"""Convert HippoRAG corpus to a JSONL file.

Reference: https://github.com/RUC-NLPIR/FlashRAG?tab=readme-ov-file#corpus-construction

Example usage:
```bash
python build_faiss_index.py --dataset DATASET_NAME_OR_PATH --output_dir OUTPUT_DIR
```
"""

import json
import os

from langchain_community.vectorstores import FAISS
from openai import OpenAI
from tqdm import tqdm

from . import get_parser
from .agents.common import CustomEmbeddings

parser = get_parser()
args = parser.parse_args()
dataset = args.dataset
output_dir = args.output_dir
index_dir = os.path.join(output_dir, "indexes")
os.makedirs(output_dir, exist_ok=True)
os.makedirs(index_dir, exist_ok=True)

with open(dataset) as f:
    ds = json.load(f)

if False:
    corpus_path = os.path.join(index_dir, "corpus.jsonl")
    texts = []
    with open(corpus_path, "w") as f:
        for item in tqdm(ds, desc="Saving corpus"):
            contents = f"(Title: {item['title']}) {item['text']}"
            f.write(json.dumps({"id": item["idx"], "contents": contents}) + "\n")
            texts.append(contents)
    print(f"Saved corpus to {corpus_path}")

texts = [f"(Title: {item['title']}) {item['text']}" for item in ds]

# Embed documents and build retriever
# Assumes the embedding server is already running
BASE_URL = f"http://0.0.0.0:{args.inf_vllm_port}/v1"
API_KEY = "token-abc123"
client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
)
embeddings = CustomEmbeddings(client)
vectorstore = FAISS.from_texts(texts, embeddings)
save_path = os.path.join(index_dir, "faiss_index")
print(f"Saving vectorstore to {save_path}")
vectorstore.save_local(save_path)
print("Save complete.")
