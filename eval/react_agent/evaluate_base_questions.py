# %%
import os
import sys
from pathlib import Path

import dotenv
dotenv.load_dotenv(".env", override=True)

# %%
# Specify argument parser
import argparse
import llm

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, default="gpt-4o-mini-2024-07-18", choices=llm.SUPPORTED_LLM_NAMES)
    # parser.add_argument("--model_name", type=str, default="claude-3-5-haiku-20241022", choices=llm.SUPPORTED_LLM_NAMES)

    # Dataset arguments
    parser.add_argument("--eval_split", type=str, default="depth_6_size_26_seed_1")

    # React Agent arguments
    parser.add_argument("--max_steps", type=int, default=6)
    parser.add_argument("--window_size", type=int, default=6)
    parser.add_argument("--samples", type=int, default=5)
    args, unknown = parser.parse_known_args()

# %%
# Load the dataset
import datasets
from datasets import load_dataset

ds_qa = datasets.load_dataset("mlcore/phantom-wiki", "question-answer", split=args.eval_split)
ds_text_corpus = datasets.load_dataset("mlcore/phantom-wiki", "text-corpus", split=args.eval_split)


# %%
import pandas as pd

# Load the QA dataset into a dataframe
# Filter out samples without answers
df_qa_w_answers = pd.DataFrame(
    filter(lambda sample: len(sample["answer"]) > 0, ds_qa)
)
# Filter easy questions, type 1 == "who is the mother of X?"
df_qa_w_answers = df_qa_w_answers.loc[df_qa_w_answers["type"] == 1, :]
# Load the text corpus dataset into a dataframe
df_text_corpus = pd.DataFrame(ds_text_corpus)

print("Question Answer dataset:")
print(df_qa_w_answers.head())

print("Text corpus dataset:")
print(df_text_corpus.head())

# %%
from agents import ReactAgent
from llm import get_llm 

# Get the LLM model and prompts
model_kwargs = dict(
    max_retries=3,
    wait_seconds=1,
    temperature=0,
    seed=0,
)
llm_chat, llm_prompts = get_llm(args.model_name, model_kwargs=model_kwargs)

# Construct react agent for each sample in the QA dataset
agents: list[ReactAgent] = []
for i, sample in enumerate(df_qa_w_answers[:args.samples].itertuples()):
    agent = ReactAgent(
        sample.question,
        sample.answer,
        agent_prompt=llm_prompts.react_agent_prompt(),
        max_steps=args.max_steps,
        text_corpus=df_text_corpus,
    )
    agents.append(agent)

    print("** Agent's initial prompt:")
    print(agent._build_agent_prompt())

# %%
# Run `n` trials (note: Reflexion with n=1 is the same as ReAct)
# n = 5
n = 1
trial = 0
log = "" 

# Specify the save directory
save_dir = Path("./results") / "react_agent" / args.model_name
save_dir.mkdir(parents=True, exist_ok=True)

# %%
from util import summarize_react_trial, log_react_trial, save_agents, save_log
from util import (red, blue, green, yellow, cyan)

for i in range(n):
    for agent in [a for a in agents if not a.is_correct()]:
        blue(agent.question)
        agent.run(llm_chat)

        print(f"Answer: {agent.keys}")

        # Debugging outputs
        try:
            yellow(f"List of actions: {agent.actions}")
        except AttributeError:
            yellow(f'List of actions: {agent.actions}')
        if agent.error:
            red(f'Error: {agent.error}')
        
    trial += 1
    # log per trial
    trial_log = log_react_trial(agents, trial, llm_chat)
    # cumulative log
    log += trial_log
    correct, incorrect, halted, runtime_error = summarize_react_trial(agents, llm_chat)
    print(f'Finished Trial {trial}, Correct: {len(correct)}, Incorrect: {len(incorrect)}, Halted: {len(halted)}, Runtime Error: {len(runtime_error)}')

    # Save the log per trial
    trial_save_dir = os.path.join(save_dir, f'trial_{trial}')
    save_log(
        trial_log, 
        trial_save_dir, 
        f'{len(agents)}_questions_{trial}_trials.txt'
    )
    save_agents(
        agents, 
        os.path.join(trial_save_dir, 'agents')
    )

# Save the result log
save_log(
    log, 
    save_dir, 
    f'{len(agents)}_questions_{trial}_trials.txt'
)


# %%
