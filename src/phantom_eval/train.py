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

# %%
# import os 
# os.chdir("/home/jcl354/phantom-wiki/src/phantom_eval/")

# %%
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments
from utils import load_data

# %%
# !pip install transformers[torch]

# %%
# def train_model(dataset_splits):
dataset_splits=["depth_20_size_50_seed_1", "depth_20_size_50_seed_2", "depth_20_size_50_seed_3"]
model_name = "meta-llama/Llama-3.2-1B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

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

# %%
for split in dataset_splits:
    print(f"Training on {split}")
    dataset = load_dataset(split)
    tokenized_datasets = dataset.map(lambda examples: tokenizer(examples["text"], truncation=True, padding="max_length"), batched=True)
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"]
    )
    trainer.train()

model.save_pretrained("./trained_model")
tokenizer.save_pretrained("./trained_model")


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
