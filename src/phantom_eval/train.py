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
#     display_name: dataset_new
#     language: python
#     name: python3
# ---

# %%
import os 
os.chdir("/home/jcl354/phantom-wiki/src/phantom_eval/")

# %%
import torch
from torch.utils.data import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments
import pandas as pd

# existing files
from utils import load_data
# from agent import _get_evidence
from prompts import LLMPrompt, ZeroshotLLMPrompt

# %%
# # !/home/jcl354/anaconda3/envs/dataset_new/bin/pip install 'accelerate>=0.26.0'

# %%
# def train_model(dataset_splits):
dataset_splits=["depth_20_size_50_seed_1", "depth_20_size_50_seed_2", "depth_20_size_50_seed_3"]
model_name = "meta-llama/Llama-3.2-1B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# %%
training_args = TrainingArguments(
    output_dir="./results",
    evaluation_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    num_train_epochs=3,
    weight_decay=0.01,
    save_total_limit=2,
    save_strategy="epoch"
)

class CustomDataset(Dataset):
    def __init__(self, inputs, labels):
        self.inputs = inputs
        self.labels = labels

    def __len__(self):
        return len(self.inputs["input_ids"])

    def __getitem__(self, idx):
        return {
            "input_ids": self.inputs["input_ids"][idx],
            "attention_mask": self.inputs["attention_mask"][idx],
            "labels": self.labels[idx]
        }
def _get_evidence(text_corpus: pd.DataFrame) -> str:
    """Utility for constructing evidence
    Returns all articles (concatenated as a string) in the text corpus as evidence.
    """
    return "\n================\n\n".join(text_corpus["article"])


# %%
split = dataset_splits[0]
dataset = load_data(dataset="mlcore/phantom-wiki-v0.5", split=split)
df_qa_pairs = pd.DataFrame(dataset["qa_pairs"])
df_text = pd.DataFrame(dataset["text"])
dataset = CustomDataset(df_qa_pairs, df_text)


# %%
# df_qa_pairs.columns
# Index(['id', 'question', 'intermediate_answers', 'answer', 'prolog',
#        'template', 'type', 'difficulty'],
#       dtype='object')
# df_qa_pairs.head()
#                                     id	                  question        	                intermediate_answers	          answer	                                      prolog	                                                template	                                          type	difficulty
# 0	97edcc8c-952c-4f81-be38-f63d81b68517	Who is the granddaughter of the mother of the ...	          []	    [Aida Wang, Barabara Beltran, Christina Coe, C...	      {'answer': 'Y_2', 'query': ['granddaughter(Y_4...	      [Who is, the, <relation>_3, of, the, <relation...	  0	    12

# %%
# for split in dataset_splits:
#     print(f"Training on {split}")
#     dataset = load_dataset(split)
#     tokenized_datasets = dataset.map(lambda examples: tokenizer(examples["text"], truncation=True, padding="max_length"), batched=True)
#     trainer = Trainer(
#         model=model,
#         args=training_args,
#         train_dataset=tokenized_datasets["train"]
#     )
#     trainer.train()

# model.save_pretrained("./trained_model")
# tokenizer.save_pretrained("./trained_model")

# %%
def evaluate_model(eval_split):
    model_name = "./trained_model"
    tokenizer = LlamaTokenizer.from_pretrained(model_name)
    model = LlamaForCausalLM.from_pretrained(model_name)

    dataset = load_dataset(eval_split)
    tokenized_datasets = dataset.map(lambda examples: tokenizer(examples["text"], truncation=True, padding="max_length"), batched=True)

    trainer = Trainer(
        model=model,
        eval_dataset=tokenized_datasets["test"]
    )
    eval_results = trainer.evaluate()
    print(f"Evaluation results: {eval_results}")

# %%
if __name__ == "__main__":
    train_splits = ["depth_20_size_50_seed_1", "depth_20_size_50_seed_2", "depth_20_size_50_seed_3"]
    eval_split = "depth_20_size_50_seed_4"

    train_model(train_splits)
    evaluate_model(eval_split)
