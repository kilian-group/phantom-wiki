#!/usr/bin/env bash
#SBATCH --job-name=sft_on_docs
#SBATCH --output=slurm/sft_on_docs-%j.out
#SBATCH --error=slurm/sft_on_docs-%j.err
#SBATCH -p full
#SBATCH -N 1
#SBATCH -n 8
#SBATCH --gres=gpu:a100:4
#SBATCH --mem=100GB
#SBATCH --time=24:00:00

# First argument should be path to the config file
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <path_to_config_file> [additional_args]"
    exit 1
fi
SFT_CONFIG_FILE_PATH=$1

# Get NUM_GPUS from nvidia-smi. It repeats the number of GPUs a few times, take the first one.
NUM_GPUS=$(nvidia-smi --query-gpu=count --format=csv,noheader,nounits | head -n 1)

# --use_vllm reserves 1 GPU for generation, so then set NUM_PROCESSES=NUM_GPUS-1
NUM_PROCESSES=$NUM_GPUS

# Get the model name from config file
MODEL_NAME=$(grep "model_name_or_path" $SFT_CONFIG_FILE_PATH | cut -d '"' -f 2)

# Get CUDA visible devices as 0,...,NUM_GPUS-1 (0 indexing)
CUDA_DEVICES_TRAINING=$(seq -s, 0 $((NUM_GPUS - 1)))

# Get additional arguments
shift 1
cmd_args=$@
echo "-------------------------------"
echo "Additional arguments: $cmd_args"
echo "-------------------------------"

echo "-------------------------------"
echo "Starting SFT training with config file $SFT_CONFIG_FILE_PATH on GPUs $CUDA_DEVICES_TRAINING"
echo "-------------------------------"

CUDA_VISIBLE_DEVICES=$CUDA_DEVICES_TRAINING ACCELERATE_LOG_LEVEL=info accelerate launch \
    --num_processes=$NUM_PROCESSES \
    --config_file recipes/accelerate_configs/zero1.yaml \
	sft_on_docs.py \
	--config $SFT_CONFIG_FILE_PATH \
    $cmd_args
