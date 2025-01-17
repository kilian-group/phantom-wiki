"""Diagnostic script for testing the OpenAI compatible server with vLLM in generate mode.
Ref: https://docs.vllm.ai/en/latest/getting_started/examples/openai_chat_completion_client.html

STEP 1: launch the server
```bash
vllm serve meta-llama/llama-3.1-8b-instruct --api-key token-abc123 --tensor_parallel_size 2
```

STEP 2: run this script
```bash
python vllm_generate.py
```
Note: the output should be a ChatCompletionMessage.
"""

def main():
    from openai import OpenAI
    client = OpenAI(
        base_url="http://0.0.0.0:8000/v1",
        api_key="token-abc123",
    )

    completion = client.chat.completions.create(
        model="meta-llama/llama-3.1-8b-instruct",
        messages=[
            {"role": "user", "content": "Hello!"}
        ]
    )

    print(completion.choices[0].message)

async def async_main():
    from openai import AsyncOpenAI
    client = AsyncOpenAI(
        base_url="http://0.0.0.0:8000/v1",
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
    import asyncio
    asyncio.run(async_main())