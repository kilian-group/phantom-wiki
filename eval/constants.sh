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

API_MODELS=(
    "gemini-1.5-flash-002"
    "gpt-4o-2024-11-20"
)
# L models (run on 8 A6000 GPUs)
LARGE_MODELS=(
    "meta-llama/llama-3.3-70b-instruct"
    # 'google/gemma-2-27b-it' # OPTIONAL
    # 'microsoft/phi-3.5-mini-instruct' # OPTIONAL
    # 'microsoft/phi-3.5-moe-instruct' # OPTIONAL
)
# M models (run on 4 A6000 GPUs)
MEDIUM_MODELS=(
    "meta-llama/llama-3.2-3b-instruct"
    "meta-llama/llama-3.1-8b-instruct"
    # 'google/gemma-2-9b-it' # OPTIONAL
    # 'mistralai/mistral-7b-instruct-v0.3' # OPTIONAL
)
# S models (run on 3090)
SMALL_MODELS=(
    "meta-llama/llama-3.2-1b-instruct"
    # 'google/gemma-2-2b-it' # OPTIONAL
)
REASONING_MODELS=(
    "deepseek-ai/deepseek-r1-distill-qwen-32b"
)

# Define the default dataset if not already defined
if [ -z "$DATASET" ]; then
    DATASET=kilian-group/phantom-wiki-v1
fi

if [ "$DATASET" = "kilian-group/phantom-wiki-v050" ]; then
    # Define SPLIT_LIST for dataset v0.5
    # Splits of universe sizes 50, 100, 200, 300, 400, 500, 1000, 2500, 5000, 10000 are available on huggingface
    # for dataset v0.5 and we evaluate on them
    DATA_SEED_LIST="1 2 3"
    DATA_QUESTION_DEPTH="20"
    DATA_SIZE_LIST="50 100 200 300 400 500 1000"

    for data_seed in $DATA_SEED_LIST
    do
        for data_size in $DATA_SIZE_LIST
        do
            SPLIT_LIST+="depth_${DATA_QUESTION_DEPTH}_size_${data_size}_seed_${data_seed} "
        done
    done

    # Define large SPLIT_LIST for dataset v0.5
    LARGE_DATA_SEED_LIST="1"
    LARGE_DATA_SIZE_LIST="2500 5000 10000"
    for data_seed in $LARGE_DATA_SEED_LIST
    do
        for data_size in $LARGE_DATA_SIZE_LIST
        do
            LARGE_SPLIT_LIST+="depth_${DATA_QUESTION_DEPTH}_size_${data_size}_seed_${data_seed} "
        done
    done
elif [ "$DATASET" = "kilian-group/phantom-wiki-v1" ]; then
    # Define SPLIT_LIST for dataset v1
    # Splits of universe sizes 50, 500, 5000 are available on huggingface
    # for dataset v1 and we evaluate on them
    DATA_SEED_LIST="1 2 3"
    DATA_QUESTION_DEPTH="20"
    DATA_SIZE_LIST="50 500 5000"

    for data_seed in $DATA_SEED_LIST
    do
        for data_size in $DATA_SIZE_LIST
        do
            SPLIT_LIST+="depth_${DATA_QUESTION_DEPTH}_size_${data_size}_seed_${data_seed} "
        done
    done
else
    echo "Unknown dataset: $DATASET. Please specify the split_list yourself with flags \`--split_list ...\`."
fi

# get list of support methods by running the following python command
METHODS=(
    "zeroshot"
    "fewshot"
    "zeroshot-sc"
    "fewshot-sc"
    "cot"
    "cot-sc"
    "react"
    "act"
    "react->cot-sc"
    "cot-sc->react"
    "zeroshot-rag"
    "fewshot-rag"
    "cot-rag"
)
