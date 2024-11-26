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
if True:
    output_dir = args.output_dir
    model = args.model
    split = args.split
    batch_size = args.batch_size
    batch_number = args.batch_number
    # sampling parameters
    temperature = args.temperature
    top_p = args.top_p
    top_k = args.top_k
    repetition_penalty = args.repetition_penalty
    use_together = args.use_together
else:
    # Debugging
    output_dir = "out"
    model = 'llama-3.1-8b'
    # model = 'llama-3.1-70b'
    # model = 'microsoft::phi-3.5-mini-instruct'
    split = 'depth_6_size_26_seed_1'
    batch_size = 10
    batch_number = 1
    # sampling parameters
    temperature = 0.7
    top_p = 0.95
    top_k = 50
    repetition_penalty = 1.0
    use_together = True

# %%
# remaining imports
import json
import os
# utils from phantom_eval
from phantom_eval.utils import (load_data,
                                get_all_articles)

# %%
run_name = f"{model}-{split}-bs{batch_size}-bn{batch_number}"
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
for qa in batch:
    instruction = prompt.format(
        evidence=evidence, 
        question=qa['question'],
    )
    messages.append(get_message(instruction))

# %%
if use_together:
    # response = client.chat.completions.create(
    #     model=model_map[model],
    #     messages=get_message(prompt),
    #     temperature=temperature,
    #     top_p=0.7,
    #     top_k=50,
    #     repetition_penalty=1,
    #     stop=["<|eot_id|>"],
    #     stream=True,
    # )
    import os, asyncio
    from together import AsyncTogether

    MODEL_ALIASES = {
        'llama-3.1-8b': "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        'llama-3.1-70b' : "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        'llama-3.1-405b' : "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
    }
    async def async_chat_completion(messages):
        async_client = AsyncTogether()
        tasks = [
            async_client.chat.completions.create(
                model=MODEL_ALIASES[model],
                messages=message,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repetition_penalty=repetition_penalty,
                stop=["<|eot_id|>"],
            )
            for message in messages
        ]
        responses = await asyncio.gather(*tasks)
        return [response.choices[0].message.content for response in responses]
    responses = asyncio.run(async_chat_completion(messages))
else:
    from transformers import AutoTokenizer
    from vllm import LLM, SamplingParams

    HF_MODEL_NAME = model.replace("::", "/")
    tokenizer = AutoTokenizer.from_pretrained(HF_MODEL_NAME, trust_remote_code=True)
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
        max_tokens=512,
    )
    # Create an LLM.
    # Ref: https://docs.vllm.ai/en/stable/dev/offline_inference/llm.html#vllm.LLM
    llm = LLM(
        model=HF_MODEL_NAME,
        tokenizer=HF_MODEL_NAME,
        max_model_len=4096,
    )
    # Generate texts from the prompts. The output is a list of RequestOutput objects
    # that contain the prompt, generated text, and other information.
    outputs = llm.generate(prompts, sampling_params)
    responses = [output.outputs[0].text for output in outputs]

# %%
preds = {}
for i in range(len(batch)):
    uid = batch[i]['id']
    preds[uid] = {
        'true' : batch[i]['answer'],
        'pred' : responses[i],
        'metadata': {
            'model': model,
            'split': split,
            'batch_size': batch_size,
            'batch_number': batch_number,
            # TODO: add question type, sampling parameters, token usage
        }
    }

# %%
# save predictions
pred_path = os.path.join(pred_dir, f"{run_name}.json")
print(f"Saving predictions to {pred_path}...")
with open(pred_path, "w") as f:
    json.dump(preds, f, indent=4)
