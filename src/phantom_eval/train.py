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
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments, DataCollatorForSeq2Seq
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
eval_split = "depth_20_size_50_seed_4"
model_name = "meta-llama/Llama-3.2-1B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)
training_args = TrainingArguments(
    output_dir="./results",
    evaluation_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    num_train_epochs=1,
    weight_decay=0.01,
)
    # evaluation_strategy="no",


# %%
class CustomDataset(Dataset):
    def __init__(self, qa_pairs, text, tokenizer):
        self.prompt = ZeroshotLLMPrompt()
        self.text = text
        self.qa_pairs = qa_pairs
        
        prompts: list[str] = [self._build_agent_prompt(question) for question in qa_pairs["question"].tolist()]
        answers = qa_pairs["answer"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x).tolist()

        tokenizer.pad_token = tokenizer.eos_token
        tokenized_inputs = tokenizer(prompts, padding="max_length", max_length=30000)#, padding="max_length", truncation=True, max_length=max_length, return_tensors="pt")
        tokenized_labels = tokenizer(answers, padding="max_length", max_length=30000)["input_ids"]#, padding="max_length", truncation=True, max_length=max_length, return_tensors="pt")["input_ids"]
        tokenized_labels[tokenized_labels == tokenizer.pad_token_id] = -100         # Ensure labels' padding tokens are ignored in loss computation
        self.inputs = tokenized_inputs
        self.labels = tokenized_labels

    def __len__(self):
        return len(self.qa_pairs)

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
    
    def _build_agent_prompt(self, question: str) -> str:
        return self.prompt.get_prompt().format(
            evidence=self._get_evidence(self.text),
            question=question
        )

data_collator = DataCollatorForSeq2Seq(
    tokenizer=tokenizer,
    model=model,
    padding=True
)
        

# %%
eval_data = load_data(dataset="mlcore/phantom-wiki-v0.5", split=eval_split)
eval_df_qa_pairs = pd.DataFrame(eval_data["qa_pairs"])
eval_df_text = pd.DataFrame(eval_data["text"])
eval_dataset = CustomDataset(qa_pairs=eval_df_qa_pairs, text=eval_df_text, tokenizer=tokenizer)

# %%
for split in dataset_splits:
    print(f"Training on {split}")
    train_data = load_data(dataset="mlcore/phantom-wiki-v0.5", split=split)
    train_df_qa_pairs = pd.DataFrame(train_data["qa_pairs"])
    train_df_text = pd.DataFrame(train_data["text"])
    train_dataset = CustomDataset(qa_pairs=train_df_qa_pairs, text=train_df_text, tokenizer=tokenizer)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
    )
            # save_strategy="epoch"
    trainer.train()

# %%

# %%
# df_qa_pairs.columns
# Index(['id', 'question', 'intermediate_answers', 'answer', 'prolog',
#        'template', 'type', 'difficulty'],
#       dtype='object')
# df_qa_pairs.head()
#                                     id	                  question        	                intermediate_answers	          answer	                                      prolog	                                                template	                                          type	difficulty
# 0	97edcc8c-952c-4f81-be38-f63d81b68517	Who is the granddaughter of the mother of the ...	          []	    [Aida Wang, Barabara Beltran, Christina Coe, C...	      {'answer': 'Y_2', 'query': ['granddaughter(Y_4...	      [Who is, the, <relation>_3, of, the, <relation...	  0	    12
