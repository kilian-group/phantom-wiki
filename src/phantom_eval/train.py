import argparse
import os
from pathlib import Path

from transformers import LlamaForCausalLM, LlamaTokenizer, TrainingArguments, Trainer
from datasets import load_dataset, DatasetDict
import torch

# Set up logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from utils import load_data

def load_and_prepare_data(dataset_names):
    """Load and concatenate datasets for fine-tuning."""
    datasets = [load_data(dataset_name, split="train") for dataset_name in dataset_names]
    return datasets[0].concatenate(*datasets[1:])

def fine_tune_llama(model_name, train_dataset, output_dir):
    """Fine-tune the Llama model."""
    tokenizer = LlamaTokenizer.from_pretrained(model_name)
    model = LlamaForCausalLM.from_pretrained(model_name)

    # Tokenize dataset
    def tokenize_function(examples):
        return tokenizer(examples["text"], padding="max_length", truncation=True)

    tokenized_dataset = train_dataset.map(tokenize_function, batched=True)

    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        evaluation_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=4,
        num_train_epochs=3,
        save_steps=10_000,
        save_total_limit=2,
        logging_dir=f'{output_dir}/logs',
        logging_steps=500,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
    )

    trainer.train()
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

def run_inference(model_dir, test_dataset, output_file):
    """Run inference on the fine-tuned model."""
    tokenizer = LlamaTokenizer.from_pretrained(model_dir)
    model = LlamaForCausalLM.from_pretrained(model_dir)
    model.eval()

    results = []
    for item in test_dataset:
        inputs = tokenizer(item["text"], return_tensors="pt")
        with torch.no_grad():
            outputs = model.generate(inputs["input_ids"], max_length=50)
        decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
        results.append({"input": item["text"], "output": decoded})

    with open(output_file, "w") as f:
        for result in results:
            f.write(f"Input: {result['input']}\nOutput: {result['output']}\n\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fine-tune and run inference on Llama model.")
    parser.add_argument("--train_datasets", nargs='+', default="depth_20_size_50_seed_1 depth_20_size_50_seed_2 depth_20_size_50_seed_3",help="List of training dataset names.")
    parser.add_argument("--test_dataset", default="depth_20_size_50_seed_4",help="Test dataset name.")
    parser.add_argument("--model_name", default="google/gemma-2-2b-it", help="Pretrained model name.")
    parser.add_argument("--output_dir", default="./fine_tuned_model", help="Directory to save fine-tuned model.")
    parser.add_argument("--output_file", default="inference_results.txt", help="File to save inference results.")
    args = parser.parse_args()

    logger.info("Loading and preparing datasets...")
    train_dataset = load_and_prepare_data(args.train_datasets)
    test_dataset = load_data(args.test_dataset, split="train")

    logger.info("Starting fine-tuning...")
    fine_tune_llama(args.model_name, train_dataset, args.output_dir)

    logger.info("Running inference...")
    run_inference(args.output_dir, test_dataset, args.output_file)

    logger.info("Process complete.")
