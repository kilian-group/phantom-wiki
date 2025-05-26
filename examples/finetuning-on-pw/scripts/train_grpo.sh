#!/usr/bin/env bash
#SBATCH --job-name=grpo
#SBATCH --output=logs/grpo-%j.out
#SBATCH --error=logs/grpo-%j.err
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
GRPO_CONFIG_FILE_PATH=$1

# Get NUM_GPUS from nvidia-smi. It repeats the number of GPUs a few times, take the first one.
NUM_GPUS=$(nvidia-smi --query-gpu=count --format=csv,noheader,nounits | head -n 1)

# --use_vllm reserves 1 GPU for generation, so then set NUM_PROCESSES=NUM_GPUS-1
NUM_PROCESSES=$((NUM_GPUS - 1))

# Get the model name from config file
MODEL_NAME=$(grep "model_name_or_path" $GRPO_CONFIG_FILE_PATH | cut -d '"' -f 2)

echo "-------------------------------"
echo "Starting VLLM server of model $MODEL_NAME on GPU $((NUM_GPUS - 1))"
echo "-------------------------------"
# Route the stdout and stderr to /dev/null to avoid cluttering the logs
CUDA_VISIBLE_DEVICES=$((NUM_GPUS - 1)) trl vllm-serve --model "$MODEL_NAME" > /dev/null 2>&1 &

# Get CUDA visible devices as 0,...,NUM_GPUS-2 (0 indexing, and last one is reserved for vllm)
CUDA_DEVICES_TRAINING=$(seq -s, 0 $((NUM_GPUS - 2)))

# Get additional arguments
shift 1
cmd_args=$@
echo "-------------------------------"
echo "Additional arguments: $cmd_args"
echo "-------------------------------"

echo "-------------------------------"
echo "Starting GRPO training with config file $GRPO_CONFIG_FILE_PATH on GPUs $CUDA_DEVICES_TRAINING"
echo "-------------------------------"

CUDA_VISIBLE_DEVICES=$CUDA_DEVICES_TRAINING ACCELERATE_LOG_LEVEL=info accelerate launch \
    --num_processes=$NUM_PROCESSES \
    --config_file recipes/accelerate_configs/zero1.yaml \
	grpo.py \
	--config $GRPO_CONFIG_FILE_PATH \
    $@

echo "-------------------------------"
echo "Killing VLLM server"
echo "-------------------------------"
pkill -e -f vllm
