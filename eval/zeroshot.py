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
model = args.model_name
split = args.split
batch_size = args.batch_size
batch_number = args.batch_number
# inference parameters
temperature = args.inf_temperature
top_p = args.inf_top_p
top_k = args.inf_top_k

# 
# Default parameters
# 
# NOTE: eot_id indicates the end of a message in a turn
# Ref: https://www.llama.com/docs/model-cards-and-prompt-formats/meta-llama-3/
STOP = ["\n"]
max_tokens = args.inf_max_tokens
# MAX_TOKENS = 512
# Params specific to Together and vLLM
LLAMA_STOP = STOP + ["<|eot_id|>",]
repetition_penalty = 1.0
# Params specific to vLLM
seed = args.inf_seed
# max_model_len = args.inf_max_model_len
# tensor_parallel_size = args.inf_tensor_parallel_size

# %%
# remaining imports
import json
import os
import asyncio
import logging
import time
from tqdm import tqdm
# set logging level
logging.basicConfig(level=logging.INFO)
# utils from phantom_eval
from phantom_eval.utils import (load_data,
                                get_all_articles)
# python sdks
from together import AsyncTogether
from openai import AsyncOpenAI
from google.generativeai import GenerativeModel
from anthropic import AsyncAnthropic

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

# requests per minute
RPM_LIMITS = {
    "together": 3_000,
    "gpt": 5_000,
    "gemini": 15,
    "claude": 2_000,
}
# tokens per minute
TPM_LIMITS = {
    "together": 500_000,
    "gpt": 4_000_000,
    "gemini": 1_000_000,
    "claude": 200_000,
}

# %%
TOGETHER_MODEL_ALIASES = {
    'meta-llama/llama-3.1-8b-instruct':'meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo',
    'meta-llama/llama-3.1-70b-instruct':'meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo',
    'meta-llama/llama-3.1-405b-instruct':'meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo',
}
"""
Ref:
- https://github.com/google-gemini/generative-ai-python/blob/main/docs/api/google/generativeai/GenerativeModel.md
"""
RPM_LIMIT = 15
TPM_LIMIT = 4 * 10**6 
# TODO: add functionality to check the number of requests per day from Google's API
RPD_LIMIT = 1500 # requests per day

async def async_chat_completion(messages):
    # Initialize async client
    if model.startswith("together:"):
        client = AsyncTogether()
    elif model.startswith("gemini"):
        logging.warning(f"Google does not support setting seed for Gemini.")
        client = GenerativeModel(model)
    elif model.startswith("gpt"):
        client = AsyncOpenAI()
    elif model.startswith("claude"):
        client = AsyncAnthropic()
    else:
        raise ValueError(f"Use `zeroshot_local.py` to get vLLM predictions.")
    tasks = []

    start = time.time()
    token_usage_per_minute = 0 # NOTE: we estimate the number of used tokens in the current minute
    
    for i, message in tqdm(enumerate(messages)):
        print(f"{time.time()-start}: Requesting message {i}")
        if model.startswith("gemini"):
            # count the number of tokens in `message`
            input_tokens = client.count_tokens(message).total_tokens
            # NOTE: according to the Google AI API details, token usage refers to the input tokens
        else:
            input_tokens = 0 # TODO: implement count tokens for other models
        token_usage_per_minute += input_tokens

        # check if we need to sleep to respect the TPM rate limit
        remaining = 60 - (time.time() - start) # number of seconds remaining in the current minute
        if token_usage_per_minute > TPM_LIMIT and remaining > 0:
            logging.info(f"Token usage per minute: {token_usage_per_minute}")
            logging.info(f"Sleeping for {remaining} seconds to respect the TPM rate limit")
            await asyncio.sleep(remaining + 1) # NOTE: add an extra second so we definitely pass the minute
        
        # reset if we have passed the minute
        if time.time() - start > 60:
            start = time.time()
            token_usage_per_minute = 0

        # create task
        if model.startswith("together:"):
            t = client.chat.completions.create(
                model=TOGETHER_MODEL_ALIASES[model.replace("together:", "")],
                messages=message,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repetition_penalty=repetition_penalty,
                stop=LLAMA_STOP,
                max_tokens=max_tokens,
                seed=seed,
            )
        elif model.startswith("gpt"):
            t = client.chat.completions.create(
                model=model,
                messages=message,
                temperature=temperature,
                top_p=top_p,
                # NOTE: top_k is not supported by OpenAI's API
                # NOTE: repetition_penalty is not supported by OpenAI's API
                stop=STOP,
                max_completion_tokens=max_tokens,
                seed=seed,
            )
        elif model.startswith("gemini"):
            # Ref: https://cloud.google.com/vertex-ai/docs/reference/rest/v1/GenerationConfig
            t = client.generate_content_async(
                message,
                generation_config={
                    'temperature': temperature,
                    'top_p': top_p,
                    # 'top_k': top_k, # NOTE: API does not suport topK>40
                    'max_output_tokens': max_tokens,
                    'stop_sequences': STOP,
                    # NOTE: API does not support seed, repetition_penalty
                }
            )
        elif model.startswith("claude"):
            t = client.messages.create(
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
        else:
            raise ValueError(f"Use `zeroshot_local.py` to get vLLM predictions.")
        
        tasks.append(asyncio.create_task(t))
        # Sleep to respect the rate limit
        await asyncio.sleep(60 / RPM_LIMIT)
    
    print(f"{time.time()-start}: Waiting for responses")
    responses = await asyncio.gather(*tasks)
    print(f"{time.time()-start}: Got all responses")
    if model.startswith("together:"):
        return [
            {
                'pred' : response.choices[0].message.content,
                'usage' : response.usage.model_dump(),
            }
            for response in responses
        ]
    elif model.startswith("gpt"):
        return [
            {
                'pred' : response.choices[0].message.content,
                'usage' : response.usage.model_dump(),
            }
            for response in responses
        ]
    elif model.startswith("gemini"):
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
    elif model.startswith("claude"):
        return [
            {
                'pred' : response.content[0].text,
                'usage' : response.usage.model_dump(),
            }
            for response in responses
        ]
    else:
        raise ValueError(f"Use `zeroshot_local.py` to get vLLM predictions.")

if False:
    # Use like other models
    if model.startswith("gemini"):
        responses = asyncio.run(async_chat_completion(messages_instructions_only))
    else:
        responses = asyncio.run(async_chat_completion(messages))
else:
    """Start refactor"""
    from phantom_eval.llm import get_llm
    from phantom_eval.data import Conversation, ContentTextMessage, Message

    llm_chat = get_llm(
        model_name=model,
        model_kwargs={
            'temperature' : temperature,
            'top_p' : top_p,
            'top_k' : top_k,
            'max_tokens' : max_tokens,
            'repetition_penalty' : repetition_penalty,
            'seed' : seed,
        }
    )
    conv_list = []
    for qa in batch:
        instruction = prompt.format(
            evidence=evidence, 
            question=qa['question'],
        )
        conv = Conversation(messages=[
            Message(role="user", content=[ContentTextMessage(text=instruction)])
        ])
        conv_list.append(conv)

    responses = llm_chat.batch_generate_response(
        convs=conv_list,
        stop_sequences=['\n',]
    )
    """End refactor"""

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
        'inference_params': {
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
