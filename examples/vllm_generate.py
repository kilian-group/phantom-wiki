"""Diagnostic script for testing the OpenAI compatible server with vLLM in generate mode.
Ref: https://docs.vllm.ai/en/latest/getting_started/examples/openai_chat_completion_client.html

STEP 1: launch the server
```bash
vllm serve meta-llama/llama-3.1-8b-instruct --api-key token-abc123 --tensor_parallel_size 2
```
Note: 
- For meta-llama/llama-3.1-8b-instruct to run, you will need at least 1 A6000 GPU, but running on 2 GPUs is faster.


STEP 2: run this script
```bash
python vllm_generate.py
```
Note: the output should be a ChatCompletionMessage.
"""
from argparse import ArgumentParser

def main(args):
    from openai import OpenAI
    client = OpenAI(
        base_url=f"http://0.0.0.0:{args.port}/v1",
        api_key="token-abc123",
    )

    completion = client.chat.completions.create(
        model="meta-llama/llama-3.1-8b-instruct",
        messages=[
            {"role": "user", "content": "Hello!"}
        ]
    )

    print(completion.choices[0].message)

async def async_main(args):
    from openai import AsyncOpenAI
    client = AsyncOpenAI(
        base_url=f"http://0.0.0.0:{args.port}/v1",
        api_key="token-abc123",
    )

    completion = await client.chat.completions.create(
        model="meta-llama/llama-3.1-8b-instruct",
        messages=[
            {"role": "user", "content": "Hello!"}
        ]
    )
    print(completion.choices[0].message)

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--port", type=int, default=8000,
                        help="port number of the server")
    args = parser.parse_args()

    import asyncio
    asyncio.run(async_main(args))