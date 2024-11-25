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
#     name: python3
# ---

# %% [markdown]
# ```
# python evaluate_base_questions.py -m llama-3.1-8b -op 
# ```

# %%
# %load_ext autoreload
# %autoreload 2

# %%
from phantom_eval.utils import (get_parser)
parser = get_parser()
args, _ = parser.parse_known_args()

# %%
if True:
    output_dir = args.output_dir
    model = args.model
    split = args.split
    batch_size = args.batch_size
    batch_number = args.batch_number
    temperature = args.temperature
else:
    # Debugging
    output_dir = "out"
    model = 'llama-3.1-8b'
    # model = 'llama-3.1-70b'
    split = 'train'
    batch_size = 10
    batch_number = 1
    temperature = 0.7

# %%
# remaining imports
import json
import os
# utils from phantom_wiki
from phantom_wiki.utils import (green, 
                                blue, 
                                colored)
# utils from phantom_eval
from phantom_eval.utils import (load_data,
                                get_all_articles)
from together import Together
from itertools import islice

# %%
run_name = f"{model}-{split}-bs{batch_size}-bn{batch_number}"
print(f"Run name: {run_name}")
pred_dir = os.path.join(output_dir, "preds")
os.makedirs(pred_dir, exist_ok=True)

# %%
dataset = load_data(split)

# %%
client = Together()

# %%
model_map = {
    'llama-3.1-8b': "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
    'llama-3.1-70b' : "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    'llama-3.1-405b' : "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
}

# %%
prompt = """
Given the following evidence:
{}

Answer the following question:
{}

The output should be one of the following:
- The name of the person if there is a unique answer.
- A list of names separated by commas if there are multiple answers.
- "null" if there is no answer.
DO NOT include any additional information in the output.
"""

# %%
preds = {}
streaming_output = "" #store the output in a string to write to a file
# we are in the setting where we pass in all the articles as evidence
evidence = get_all_articles(dataset)
# save evidence to streaming_output
streaming_output += evidence + '\n'
# for getting subset of the questions
start = (batch_number - 1) * batch_size
end = start + batch_size
for qa in islice(dataset['qa_pairs'], start, end):
    uid = qa['id']
    question = qa['question']
    answer = qa['answer']
    
    green(f"Question: {question}")
    streaming_output += '----------------\n'
    streaming_output += f"Question: {question}\n"

    response = client.chat.completions.create(
        model=model_map[model],
        messages=[
            {"role": "user", "content": prompt.format(evidence, question)},
        ],
        temperature=temperature,
        top_p=0.7,
        top_k=50,
        repetition_penalty=1,
        stop=["<|eot_id|>"],
        stream=True,
    )
    pred = ""
    print(colored('Prediction: ', 'red'), end="", flush=True)
    streaming_output += "Prediction: "
    for chunk in response:
        s = chunk.choices[0].delta.content or ""
        print(colored(s, 'red'), end="", flush=True)
        pred += s
    print()
    streaming_output += pred + '\n'

    blue(f'Answer: {answer}')
    streaming_output += f"Answer: {answer}\n"

    preds[uid] = {
        'true' : answer,
        'pred' : pred,
        'metadata': {
            'model': model,
            'split': split,
            'batch_size': batch_size,
            'batch_number': batch_number,
        }
    }

    print()
    streaming_output += '\n'

# %%
# save predictions
with open(os.path.join(pred_dir, f"{run_name}.json"), "w") as f:
    json.dump(preds, f, indent=4)

# %%
# save streaming output
with open(os.path.join(pred_dir, f"{run_name}.txt"), "w") as f:
    f.write(streaming_output)

# %%
