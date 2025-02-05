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
API_MODELS=(
    gemini-1.5-flash-002
    gpt-4o-2024-11-20
)
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

DATASET=mlcore/phantom-wiki-v050

# if dataset is mlcore/phantom-wiki-v0.2, use the following
if [ "$DATASET" = "mlcore/phantom-wiki-v0.2" ]; then
    # Define SPLIT_LIST for dataset v0.2
    DATA_SEED_LIST="1 2 3 4 5"
    DATA_DEPTH="10"
    DATA_SIZE_LIST="26 50 100 200 500"

    for data_seed in $DATA_SEED_LIST
    do
        for data_size in $DATA_SIZE_LIST
        do
            SPLIT_LIST+="depth_${DATA_DEPTH}_size_${data_size}_seed_${data_seed} "
        done
    done
elif [ "$DATASET" = "mlcore/phantom-wiki-v0.3" ]; then
    # Define SPLIT_LIST for dataset v0.3
    DATA_SEED_LIST="1 2 3"
    DATA_DEPTH="20"
    DATA_SIZE_LIST="50 100 200 300 400 500"

    for data_seed in $DATA_SEED_LIST
    do
        for data_size in $DATA_SIZE_LIST
        do
            SPLIT_LIST+="depth_${DATA_DEPTH}_size_${data_size}_seed_${data_seed} "
        done
    done
elif [ "$DATASET" = "mlcore/phantom-wiki-v050" ]; then
    # Define SPLIT_LIST for dataset v0.3
    DATA_SEED_LIST="1 2 3"
    DATA_DEPTH="20"
    DATA_SIZE_LIST="50 100 200 300 400 500 1000"

    for data_seed in $DATA_SEED_LIST
    do
        for data_size in $DATA_SIZE_LIST
        do
            SPLIT_LIST+="depth_${DATA_DEPTH}_size_${data_size}_seed_${data_seed} "
        done
    done
else
    echo "Unknown dataset: $DATASET. Cannot define SPLIT_LIST."
    exit 1
fi
