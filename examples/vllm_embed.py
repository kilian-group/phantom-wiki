"""Diagnostic script for vLLM's embeddings API.
Ref: https://docs.vllm.ai/en/latest/getting_started/examples/openai_embedding_client.html

STEP 1: Start the vLLM API server in embedding mode:
```bash
vllm serve meta-llama/llama-3.1-8b-instruct --api-key token-abc123 --tensor_parallel_size 2 --task embedding
```
Note: 
- The `--tensor_parallel_size` argument must match the number of GPUs on your machine.
For meta-llama/llama-3.1-8b-instruct to run, you will need at least 2 A6000 GPUs. (For some reason, the embeddings API requires 2 GPUs, while the generate API only requires 1 GPU.)

STEP 2: Run this script to test the embeddings API.
```bash
python vllm_embed.py
```
Note: The output should be a long list of floats.
"""
from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("--port", type=int, default=8000,
                    help="port number of the server")
args = parser.parse_args()

from openai import OpenAI

# Modify OpenAI's API key and API base to use vLLM's API server.
openai_api_key = "token-abc123"
openai_api_base = f"http://localhost:{args.port}/v1"

client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key=openai_api_key,
    base_url=openai_api_base,
)

models = client.models.list()
model = models.data[0].id

responses = client.embeddings.create(
    input=[
        "Hello my name is",
        "The best thing about vLLM is that it supports many different models"
    ],
    model=model,
)

for data in responses.data:
    print(data.embedding)  # list of float of len 4096