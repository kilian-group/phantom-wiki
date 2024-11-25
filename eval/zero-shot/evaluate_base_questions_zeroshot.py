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
from argparse import ArgumentParser
parser = ArgumentParser(description="Phantom Wiki CLI")
parser.add_argument("--data_path", "-dp", default="../../output",
                    help="Path to generated dataset, assumes that there is a subfolder called 'questions_answers'")
parser.add_argument("--output_path", "-op", default="out",
                    help="Path to save output")
parser.add_argument("--model", "-m", default="llama-3.1-8b",
                    help="Model to use for the generation")
parser.add_argument("--split", "-s", default="base",
                    help="Dataset split (e.g., base, derived)")
parser.add_argument("--num_people", "-np", default=5, type=int,
                    help="Number of people to evaluate")
# TODO: store the questions as a flat list (currently the questions are grouped by person)
# parser.add_argument("--batch_size", "-bs", default=100, type=int,
#                     help="Batch size (>=1)")
# parser.add_argument("--batch_number", "-bn", default=1, type=int,
#                     help="Batch number (>=1). For example, if batch_size=100 and batch_number=1," \
#                         "then the first 100 questions will be evaluated")
args, _ = parser.parse_known_args()

# %%
# data_path = args.data_path
# output_path = args.output_path
# model = args.model
# split = args.split
# num_people = args.num_people

# Debugging
data_path = "../../out"
output_path = "out"
model = 'llama-3.1-8b'
split = 'base'
num_people = 5

# %%
# remaining imports
import json
import os
from phantom_wiki.utils import green, blue, red, colored
from together import Together

# %%
run_name = f"{split}_{model}"
print(f"Run name: {run_name}")
pred_dir = os.path.join(output_path, "predictions")
os.makedirs(pred_dir, exist_ok=True)

# %%
with open(os.path.join(data_path, "question_answers", f"{split}.json"), "r") as file:
    dataset = json.load(file)
# import pdb; pdb.set_trace()

# %%
client = Together()

# %%
model_map = {
    'llama-3.1-8b': "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
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
for name, evidence_qa in list(dataset.items())[:num_people]:
    evidence = evidence_qa['evidence']
    print('================')
    streaming_output += '================\n'
    print(evidence)
    streaming_output += evidence + '\n'

    for question_answer in evidence_qa["qa_pairs"]:
        uid = question_answer['id']
        question = question_answer['question']
        answer = question_answer['answer']
            
        green("Question:", question)
        streaming_output += '----------------\n'
        streaming_output += f"Question: {question}\n"

        response = client.chat.completions.create(
            model=model_map[model],
            messages=[
                {"role": "user", "content": prompt.format(evidence, question)},
            ],
            temperature=0.7,
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

        blue('Answer:', answer)
        streaming_output += f"Answer: {answer}\n"

        preds[uid] = {
            'answer' : answer,
            'prediction' : pred
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
