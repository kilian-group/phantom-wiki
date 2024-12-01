# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     custom_cell_magics: kql
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.11.2
#   kernelspec:
#     display_name: dataset
#     language: python
#     name: dataset
# ---

# %% [markdown]
# Script to get the predictions from a specified model with zero-shot prompting.
# To run:
# ```
# python zeroshot.py -m <model name>
# ```
# By default, the script will save the predictions to `out/preds` as JSON files 
# with the following schema:
# question_id -> {"true" : <answer list>, "pred" : <generated string>, "metadata" : <additional metadata>}

# %%
# %load_ext autoreload
# %autoreload 2

# %%
from phantom_eval.utils import (get_parser)
parser = get_parser()
parser.add_argument("--ignore_evidence", action="store_true", 
                    help="Ignore evidence and only use the question as input." \
                        "This is useful as a sanity check.")
args, _ = parser.parse_known_args()

# %%
output_dir = args.output_dir
model = args.model
split = args.split
batch_size = args.batch_size
batch_number = args.batch_number
# sampling parameters
temperature = args.temperature
top_p = args.top_p
top_k = args.top_k

# 
# Default parameters
# 
# NOTE: eot_id indicates the end of a message in a turn
# Ref: https://www.llama.com/docs/model-cards-and-prompt-formats/meta-llama-3/
STOP = ["\n"]
MAX_TOKENS = 512
# Params specific to Together and vLLM
LLAMA_STOP = STOP + ["<|eot_id|>",]
repetition_penalty = 1.0
# Params specific to vLLM
seed = args.seed
max_model_len = args.max_model_len
tensor_parallel_size = args.tensor_parallel_size

# %%
# remaining imports
import json
import os
import logging
# set logging level
logging.basicConfig(level=logging.INFO)
# utils from phantom_eval
from phantom_eval.utils import (load_data,
                                get_all_articles)

# %%
run_name = f"{split}-{model.replace('/','--')}-bs{batch_size}-bn{batch_number}-s{seed}"
print(f"Run name: {run_name}")
pred_dir = os.path.join(output_dir, "preds")
os.makedirs(pred_dir, exist_ok=True)

# %%
dataset = load_data(split)

# %%
prompt = """{evidence}
Answer the following question:
{question}

The output should be one of the following:
- A name (if there is only one correct answer)
- A list of names separated by commas (if there are multiple correct answers)
- A number (if the answer is a number)
DO NOT include any additional information in the output.
"""

# %%
preds = {}
# we are in the setting where we pass in all the articles as evidence
if args.ignore_evidence:
    print("Ignoring evidence and only using the question as input.")
    evidence = ""
else:
    evidence = "Given the following evidence:\n"
    evidence += '========BEGIN EVIDENCE========\n'
    evidence += get_all_articles(dataset)
    evidence += '========END EVIDENCE========\n'

print("Evidence:")
print(evidence)
# for getting subset of the questions
start = (batch_number - 1) * batch_size
end = start + batch_size
print(f"Getting predictions for questions [{start}, {end}) out of {len(dataset['qa_pairs'])}")
batch = list(dataset['qa_pairs'])[start:end]

# %%
def get_message(instruction):
    message = [
        {"role": "user", "content": instruction},
    ]
    return message

# %%
# get all the messages so that we can use batch inference
messages = []
messages_instructions_only = [] # Gemini requires only the instructions
for qa in batch:
    instruction = prompt.format(
        evidence=evidence, 
        question=qa['question'],
    )
    messages.append(get_message(instruction))
    messages_instructions_only.append(instruction)

# %%
if model.startswith("together:"):
    """
    Ref:
    - https://docs.together.ai/reference/completions-1
    """
    logging.warning(f"Setting seed does not guarantee deterministic results for Together.")
    import os, asyncio
    from together import AsyncTogether
    # the Together api use slightly different model names
    TOGETHER_MODEL_ALIASES = {
        'meta-llama/llama-3.1-8b-instruct':'meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo',
        'meta-llama/llama-3.1-70b-instruct':'meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo',
        'meta-llama/llama-3.1-405b-instruct':'meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo',
    }
    async def async_chat_completion(messages):
        async_client = AsyncTogether()
        tasks = [
            # NOTE: this creates a coroutine object
            async_client.chat.completions.create(
                model=TOGETHER_MODEL_ALIASES[model.replace("together:", "")],
                messages=message,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repetition_penalty=repetition_penalty,
                stop=LLAMA_STOP,
                max_tokens=MAX_TOKENS,
                seed=seed,
            )
            for message in messages
        ]
        responses = await asyncio.gather(*tasks)
        return [
            {
                'pred' : response.choices[0].message.content,
                'usage' : response.usage.model_dump(),
            }
            for response in responses
        ]

    responses = asyncio.run(async_chat_completion(messages))

elif model.startswith("gpt"):
    logging.warning(f"Setting seed does not guarantee deterministic results for OpenAI.")
    import os, asyncio
    from openai import AsyncOpenAI
    async def async_chat_completion(messages):
        async_client = AsyncOpenAI()
        # Ref: 
        # - https://platform.openai.com/docs/api-reference/chat
        # - https://github.com/openai/openai-python
        tasks = [
            async_client.chat.completions.create(
                model=model,
                messages=message,
                temperature=temperature,
                top_p=top_p,
                # NOTE: top_k is not supported by OpenAI's API
                # NOTE: repetition_penalty is not supported by OpenAI's API
                stop=STOP,
                max_completion_tokens=MAX_TOKENS,
                seed=seed,
            )
            for message in messages
        ]
        responses = await asyncio.gather(*tasks)
        # return [response.choices[0].message.content for response in responses]
        return [
            {
                'pred' : response.choices[0].message.content,
                'usage' : response.usage.model_dump(),
            }
            for response in responses
        ]
    
    responses = asyncio.run(async_chat_completion(messages))

elif model.startswith("gemini"):
    """
    Ref:
    - https://github.com/google-gemini/generative-ai-python/blob/main/docs/api/google/generativeai/GenerativeModel.md
    """
    logging.warning(f"Google does not support setting seed for Gemini.")
    import asyncio
    import google.generativeai as genai

    async def async_chat_completion(messages):
        # Initialize Gemini client
        google_model = genai.GenerativeModel(model)
        
        async def generate_response(message):
            # Ref: https://cloud.google.com/vertex-ai/docs/reference/rest/v1/GenerationConfig
            response = await google_model.generate_content_async(
                message,
                generation_config={
                    'temperature': temperature,
                    'top_p': top_p,
                    # 'top_k': top_k, # NOTE: API does not suport topK>40
                    'max_output_tokens': MAX_TOKENS,
                    'stop_sequences': STOP,
                    # NOTE: API does not support seed, repetition_penalty
                }
            )
            return response
        
        tasks = [generate_response(message) for message in messages]
        responses = await asyncio.gather(*tasks)
        return [
            {
                'pred' : response.text,
                'usage' : {
                    'prompt_token_count': response.usage_metadata.prompt_token_count,
                    'response_token_count': response.usage_metadata.candidates_token_count,
                    'total_token_count': response.usage_metadata.total_token_count,
                    'cached_content_token_count': response.usage_metadata.cached_content_token_count,
                },
            }
            for response in responses
        ]

    # Use like other models
    responses = asyncio.run(async_chat_completion(messages_instructions_only))

elif model.startswith("claude"):
    """
    Ref: 
    - https://github.com/anthropics/anthropic-sdk-python?tab=readme-ov-file#async-usage
    - https://docs.anthropic.com/en/api/messages

    NOTE: Claude does not accept whitespace stop sequences like "\n"
    """
    logging.warning("Anthropic does not support setting seed for Claude.")
    import os, asyncio
    from anthropic import AsyncAnthropic

    async def async_chat_completion(messages):
        async_client = AsyncAnthropic()
        semaphore = asyncio.Semaphore(2)  # Limit to 2 concurrent calls
        
        async def rate_limited_message(message):
            async with semaphore:
                response = await async_client.messages.create(
                    model=model,
                    messages=message,
                    temperature=temperature,
                    top_p=top_p,
                    top_k=top_k,
                    # NOTE: repetition_penalty is not supported by Anthropic's API
                    # NOTE: by default, the model will stop at the end of the turn
                    max_tokens=MAX_TOKENS,
                    # NOTE: seed is not supported by Anthropic's API
                )
                await asyncio.sleep(5)
                return response
        
        tasks = [rate_limited_message(message) for message in messages]
        responses = await asyncio.gather(*tasks)
        return [
            {
                'pred' : response.content[0].text,
                'usage' : response.usage.model_dump(),
            }
            for response in responses
        ]

    responses = asyncio.run(async_chat_completion(messages))

else:
    from transformers import AutoTokenizer
    from vllm import LLM, SamplingParams

    tokenizer = AutoTokenizer.from_pretrained(model, trust_remote_code=True)
    prompts = [
        tokenizer.apply_chat_template(
            msg, 
            tokenize=False, 
            add_generation_prompt=True
        )
        for msg in messages
    ]
    # Create a sampling params object.
    # Ref: https://docs.vllm.ai/en/stable/dev/sampling_params.html#vllm.SamplingParams
    sampling_params = SamplingParams(
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        repetition_penalty=repetition_penalty,
        stop=LLAMA_STOP,
        max_tokens=MAX_TOKENS,
        seed=seed,
    )
    # Create an LLM.
    # Ref: https://docs.vllm.ai/en/stable/dev/offline_inference/llm.html#vllm.LLM
    # NOTE: make sure to not have *any* `torch` imports before this step
    # as it leads to runtime error with multiprocessing
    llm = LLM(
        model=model,
        max_model_len=max_model_len,
        tensor_parallel_size=tensor_parallel_size,
    )
    # Generate texts from the prompts. The output is a list of RequestOutput objects
    # that contain the prompt, generated text, and other information.
    outputs = llm.generate(prompts, sampling_params)
    responses = [
        {
            'pred' : output.outputs[0].text,
            'usage' : {
                'prompt_tokens' : len(output.prompt_token_ids),
                'completion_tokens' : len(output.outputs[0].token_ids),
                'total_tokens' : len(output.prompt_token_ids) + len(output.outputs[0].token_ids),
                'cached_tokens' : output.num_cached_tokens,
            }
        }
        for output in outputs
    ]

# %%
preds = {}
for i in range(len(batch)):
    uid = batch[i]['id']
    preds[uid] = {
        'true' : batch[i]['answer'],
        'pred' : responses[i]['pred'],
        'metadata': {
            'model': model,
            'split': split,
            'batch_size': batch_size,
            'batch_number': batch_number,
            'type': batch[i]['type'],
            'seed': seed,
        },
        'sampling_params': {
            'temperature': temperature,
            'top_p': top_p,
            'top_k': top_k,
            'seed': seed,
        },
        'usage': responses[i]['usage'],
    }

# %%
# save predictions
pred_path = os.path.join(pred_dir, f"{run_name}.json")
print(f"Saving predictions to {pred_path}")
with open(pred_path, "w") as f:
    json.dump(preds, f, indent=4)
