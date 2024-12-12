"""
Script for getting predictions across all models and all splits.
Includes functionality to upload predictions to HuggingFace.
To run:
  python get_predictions.py
"""
# %%
import subprocess
import os
from datetime import datetime
from glob import glob
import json
from datasets import (load_dataset,
                      Dataset)
import torch

# get base parser
from phantom_eval.utils import get_parser
# get models
# from phantom_eval.utils import LOCAL_MODELS
LOCAL_MODELS = [
    "meta-llama/llama-3.1-8b-instruct", 
    "microsoft/phi-3.5-mini-instruct",
    "mistralai/mistral-7b-instruct-v0.3",
    "google/gemma-2-2b-it",
    "google/gemma-2-9b-it",
    "google/gemma-2-27b-it",
    "microsoft/phi-3.5-moe-instruct",
    "meta-llama/llama-3.1-70b-instruct", 
]

# %%
parser = get_parser()
parser.add_argument("--upload-to-hf", action="store_true", 
                    help="Upload predictions to HuggingFace")
args = parser.parse_args()
output_dir = args.output_dir
upload_to_hf = args.upload_to_hf

# %%
# get splits in the dataset

dataset = load_dataset("mlcore/phantom-wiki", "question-answer")
print("Splits in the dataset:")
for i, split in enumerate(dataset.keys()):
    print(f"#{i+1}: {split}")
SPLITS = [
    'depth_10_size_26_seed_1',
    'depth_10_size_50_seed_1',
    'depth_10_size_100_seed_1',
    'depth_10_size_200_seed_1',
]
print("Using splits:", SPLITS)

# %%
stderr_dir = os.path.join(output_dir, "stderr")
os.makedirs(stderr_dir, exist_ok=True)
stdout_dir = os.path.join(output_dir, "stdout")
os.makedirs(stdout_dir, exist_ok=True)
for model in LOCAL_MODELS:
    for split in SPLITS:
        num_rows = dataset.num_rows[split]
        for seed in range(1, 6):
            cmd = [
                "python", "zeroshot.py", 
                "-m", model, 
                "-s", split, 
                "-bs", str(num_rows),# NOTE: since we are using vLLM, we can pass in a single batch
                "-bn", "1",
                "--seed", str(seed), 
                "-od", args.output_dir,
                "--tensor_parallel_size", "4",
            ]
            print("Running command:", " ".join(cmd))
            result = subprocess.run(cmd, capture_output=True)

            model_name = model.replace('/','--')
            # save stderr to a file
            with open(os.path.join(stderr_dir, f"{split}-{model_name}-{seed}.txt"), "wb") as f:
                f.write(result.stderr)
            # save stdout to a file
            with open(os.path.join(stdout_dir, f"{split}-{model_name}-{seed}.txt"), "wb") as f:
                f.write(result.stdout)

# %%
# Functionality to create a huggingface dataset and upload predictions
dt = datetime.now().strftime("%y%m%d-%H%M%S")
repo_id = os.path.join("ag2435", output_dir + "-" + dt)
print(f"Repo ID: {repo_id}")
# preserve the split structure
pred_dir = os.join(output_dir, "preds")
for split in SPLITS:
    # get all files for the split
    files = glob(os.join(pred_dir, f"{split}*.json"))
    # read all files
    data = []
    for file in files:
        with open(file, "r") as f:
            data.extend(json.load(f))
    # convert data to a HF dataset
    split_dataset = Dataset.from_dict(data)
    # push to huggingface
    # Ref: https://huggingface.co/docs/datasets/main/en/package_reference/main_classes#datasets.DatasetDict.push_to_hub
    print(f"Pushing split #{i+1}:", split)
    split_dataset.push_to_hub(repo_id, split=split)