#!/bin/bash
# Constants and helper functions for evaluation scripts

get_inf_seed_list() {
    local temperature=$1
    if (( $(echo "$temperature == 0" | bc -l) )); then
        echo "1"
    else
        echo "1 2 3 4 5"
    fi
}

# L models (run on 8 A6000 GPUs)
LARGE_MODELS=(
    'meta-llama/llama-3.3-70b-instruct'
    'deepseek-ai/deepseek-r1-distill-qwen-32b'
    # 'google/gemma-2-27b-it' # OPTIONAL
    # 'microsoft/phi-3.5-mini-instruct' # OPTIONAL
    # 'microsoft/phi-3.5-moe-instruct' # OPTIONAL
)
# M models (run on 4 A6000 GPUs)
MEDIUM_MODELS=(
    'meta-llama/llama-3.2-3b-instruct'
    'meta-llama/llama-3.1-8b-instruct'
    # 'google/gemma-2-9b-it' # OPTIONAL
    # 'mistralai/mistral-7b-instruct-v0.3' # OPTIONAL
)
# S models (run on 3090)
SMALL_MODELS=(
    'meta-llama/llama-3.2-1b-instruct'
    # 'google/gemma-2-2b-it' # OPTIONAL
)
# TODO add CPU models

# Define SPLIT_LIST for dataset v0.3
for seed in 1 2 3
do
    for size in 50 100 200 300 400 500
    do
        SPLIT_LIST+="depth_20_size_${size}_seed_${seed} "
    done
done
