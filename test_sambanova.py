from openai import OpenAI

client = OpenAI(
    api_key="9c546b54-b758-4ddc-8e71-59f09c8305a2",
    base_url="https://api.sambanova.ai/v1",
)

if False:
    if False:
        model = "DeepSeek-R1-0528"
    else:
        model = "DeepSeek-V3-0324"
else:
    if False:
        model = "Qwen3-32B"
    else:
        model = "Meta-Llama-3.3-70B-Instruct"

if False:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"},
        ],
        temperature=0.1,
        top_p=0.1,
    )
else:
    response = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": "What is 1+1?"}], temperature=0.6, top_p=0.95
    )

print(response.choices[0].message.content)
