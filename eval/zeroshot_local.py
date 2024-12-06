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
# Script to get the vLLM predictions from a specified model with zero-shot prompting.
# To run:
# ```
# python zeroshot_local.py -m <model name> --split_list <list of splits> --seed_list <list of seeds>
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
split_list = args.split_list # TODO: make this a list
assert isinstance(split_list, list), "Split must be a list of strings"
# batch_size = args.batch_size
# batch_number = args.batch_number
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
seed_list = args.seed_list # TODO: make this a list
assert isinstance(seed_list, list), "Seed must be a list of integers"
max_model_len = args.max_model_len
tensor_parallel_size = args.tensor_parallel_size
# import pdb; pdb.set_trace()
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
pred_dir = os.path.join(output_dir, "preds")
os.makedirs(pred_dir, exist_ok=True)    

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
def get_message(instruction):
    message = [
        {"role": "user", "content": instruction},
    ]
    return message

# %%
from transformers import AutoTokenizer
from vllm import LLM, SamplingParams

tokenizer = AutoTokenizer.from_pretrained(model, trust_remote_code=True)

# Create an LLM.
# Ref: https://docs.vllm.ai/en/stable/dev/offline_inference/llm.html#vllm.LLM
# NOTE: make sure to not have *any* `torch` imports before this step
# as it leads to runtime error with multiprocessing
llm = LLM(
    model=model,
    max_model_len=max_model_len,
    tensor_parallel_size=tensor_parallel_size,
)

# %%
for split in split_list:
    # get data
    # import pdb; pdb.set_trace()
    dataset = load_data(split)
    batch_size = len(dataset['qa_pairs'])
    batch_number = 1
    
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

    prompts = [
        tokenizer.apply_chat_template(
            msg, 
            tokenize=False, 
            add_generation_prompt=True
        )
        for msg in messages
    ]
        
    for seed in seed_list:
        # get run name
        run_name = f"{split}-{model.replace('/','--')}-bs{batch_size}-bn{batch_number}-s{seed}"
        print(f"Run name: {run_name}")

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

        # save predictions
        pred_path = os.path.join(pred_dir, f"{run_name}.json")
        print(f"Saving predictions to {pred_path}")
        with open(pred_path, "w") as f:
            json.dump(preds, f, indent=4)
