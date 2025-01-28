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
dataset_name="mlcore/phantom-wiki-v0.2"#"mlcore/phantom-wiki-v0.5"
dataset_splits=["depth_10_size_26_seed_1", "depth_10_size_26_seed_2", "depth_10_size_26_seed_3"]#["depth_20_size_25_seed_1", "depth_20_size_25_seed_2"]
eval_split = "depth_10_size_26_seed_4" #"depth_20_size_25_seed_3"
model_name = "meta-llama/Llama-3.2-1B-Instruct"
max_length=5000
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)
training_args = TrainingArguments(
    output_dir="./results",
    eval_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=1,
    num_train_epochs=1,
    weight_decay=0.01,
    eval_accumulation_steps=2,
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
        tokenized_inputs = tokenizer(prompts, padding="max_length", truncation=True, max_length=max_length, return_tensors="pt")
        tokenized_labels = tokenizer(answers, padding="max_length", truncation=True, max_length=max_length, return_tensors="pt")["input_ids"]
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

    def _get_evidence(self, text_corpus: pd.DataFrame) -> str:
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
eval_data = load_data(dataset=dataset_name, split=eval_split)
eval_df_qa_pairs = pd.DataFrame(eval_data["qa_pairs"])
eval_df_text = pd.DataFrame(eval_data["text"])
eval_dataset = CustomDataset(qa_pairs=eval_df_qa_pairs, text=eval_df_text, tokenizer=tokenizer)

# %%
from peft import get_peft_model, TaskType, LoraConfig
lora_config = LoraConfig(
    r=4,
    lora_alpha=8,
    lora_dropout=0.1,
    bias="none",
    task_type=TaskType.CAUSAL_LM,
    target_modules = ["q_proj", "k_proj", "v_proj"]
)
model = get_peft_model(model, lora_config)

# https://discuss.huggingface.co/t/cuda-out-of-memory-when-using-trainer-with-compute-metrics/2941/19
import evaluate
f1_metric=evaluate.load("f1")
def compute_metrics(pred):

    labels_ids = pred.label_ids
    pred_ids = pred.predictions[0]

    pred_str = tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
    labels_ids[labels_ids == -100] = tokenizer.pad_token_id
    label_str = tokenizer.batch_decode(labels_ids, skip_special_tokens=True)

    # rouge_output = rouge.compute(
    #     predictions=pred_str,
    #     references=label_str,
    #     rouge_types=["rouge1", "rouge2", "rougeL", "rougeLsum"],
    # )

    # return {
    #     "R1": round(rouge_output["rouge1"], 4),
    #     "R2": round(rouge_output["rouge2"], 4),
    #     "RL": round(rouge_output["rougeL"], 4),
    #     "RLsum": round(rouge_output["rougeLsum"], 4),
    # }
    cur_f1 = f1_metric.compute(pred_str, label_str)
    return {"F1": round(cur_f1, 4)}

def preprocess_logits_for_metrics(logits, labels):
    """
    Original Trainer may have a memory leak. 
    This is a workaround to avoid storing too many tensors that are not needed.
    """
    pred_ids = torch.argmax(logits, dim=-1)
    return pred_ids, labels

# https://huggingface.co/spaces/evaluate-metric/f1
# https://huggingface.co/docs/evaluate/v0.4.0/en/base_evaluator

import gc
for split in dataset_splits:
    gc.collect()
    torch.cuda.empty_cache()
    print(f"Training on {split}")
    train_data = load_data(dataset=dataset_name, split=split)
    train_df_qa_pairs = pd.DataFrame(train_data["qa_pairs"])
    train_df_text = pd.DataFrame(train_data["text"])
    train_dataset = CustomDataset(qa_pairs=train_df_qa_pairs, text=train_df_text, tokenizer=tokenizer)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        preprocess_logits_for_metrics=preprocess_logits_for_metrics,
        compute_metrics=compute_metrics,
    )
            # save_strategy="epoch"
    trainer.train()

# %%
