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
from argparse import ArgumentParser
parser = ArgumentParser(description="Phantom Wiki CLI")
parser.add_argument("--data_path", "-dp", default="../../output",
                    help="Path to generated dataset, assumes that there is a subfolder called 'questions_answers'")
parser.add_argument("--output_path", "-op", default="out",
                    help="Path to save output")
parser.add_argument("--model", "-m", default="llama-3.1-8b",
                    help="Model to use for the generation")
# TODO: batch size
# TODO: batch number
args, _ = parser.parse_known_args()

# %%
# data_path = args.data_path
data_path = "../../out"
output_path = args.output_path
model = args.model

# %%
# remaining imports
import json
import os
from phantom_wiki.utils import green, blue, colored
from together import Together

# %%
with open(os.path.join(data_path, "question_answers", "article_question_answer.json"), "r") as file:
    dataset = json.load(file)
# import pdb; pdb.set_trace()

# %%
client = Together()

# %%
prompt = """
Given the following facts:
{}

Answer the following question:
{}

Please follow these guidelines:
- Only output the name of the person, list of names separated by commas if there are multiple people, or "None" if there is no answer.
"""

# %%
preds = {}
for name, article_base_derived in dataset.items():
    facts = article_base_derived['article']
    print('================')
    print(facts)

    preds[name] = {}
    for question_answer in article_base_derived['base']:
        uid = question_answer['id']
        question = question_answer['question']
        answer = question_answer['answer']
        if answer is None:
            continue
            
        green("Question: " + question)

        response = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            messages=[
                {"role": "user", "content": prompt.format(facts, question)},
            ],
            temperature=0.7,
            top_p=0.7,
            top_k=50,
            repetition_penalty=1,
            stop=["<|eot_id|>"],
            stream=True,
        )
        pred = ""
        for chunk in response:
            s = chunk.choices[0].delta.content or ""
            print(colored(s, 'red'), end="", flush=True)
            pred += s
        print()

        blue('Answer: ' + answer)

        preds[name][uid] = pred

    print()

# %%
# save predictions
pred_dir = os.path.join(output_path, "predictions")
os.makedirs(pred_dir, exist_ok=True)
with open(os.path.join(pred_dir, f"{model}.json"), "w") as file:
    json.dump(preds, file, indent=4)

# %%
