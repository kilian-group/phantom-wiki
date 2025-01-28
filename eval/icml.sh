#!/bin/bash
# Script to generate tables and plots for the ICML paper
# Example usage (make sure you are in the repo root directory):
# ```bash
# ./eval/evaluate_icml.sh OUTPUT_DIRECTORY "zeroshot fewshot"
# ./eval/evaluate_icml.sh OUTPUT_DIRECTORY
# ```
# The second command (without the method list) will use the default method list

# Load constants
source eval/constants.sh
# Parse command line arguments
OUTPUT_DIR=$1
# If second argument is provided, use that for METHOD_LIST
if [ -z "$2" ]; then
    echo "Using default method list"
    METHOD_LIST=(
        "zeroshot"
        "cot"
        "react"
        "act"
        "zeroshot-rag"
        "cot-rag"
        "reasoning"
    )
else
    METHOD_LIST=($2)
fi

# Model list is LARGE_MODELS + MEDIUM_MODELS + SMALL_MODELS
MODEL_LIST=(
    "${API_MODELS[@]}"
    "${LARGE_MODELS[@]}"
    "${MEDIUM_MODELS[@]}"
    # "${SMALL_MODELS[@]}"
)
echo "Models: ${MODEL_LIST[@]}"
# Split list is defined in constants.sh
echo "Splits: $SPLIT_LIST"
# Override whichever dataset was specified in constants.sh
DATASET=mlcore/phantom-wiki-v0.5
echo "Dataset: $DATASET"

# 
# Sec 4: Main accuracy table across methods/models
# 
python eval/format_leaderboard.py -od $OUTPUT_DIR --dataset $DATASET --method_list $METHOD_LIST --model_list $MODEL_LIST

#
# Sec 5: Evaluating Reasoning
# 
python eval/plot_reasoning.py -od $OUTPUT_DIR --dataset $DATASET --method_list $METHOD_LIST --model_list $MODEL_LIST
# TODO: add aggregation vs non-aggregation plot

# 
# Sec 6: Evaluating Retrieval
# 
python eval/plot_retrieval.py -od $OUTPUT_DIR --dataset $DATASET --method_list $METHOD_LIST --model_list $MODEL_LIST
python eval/plot_size_accuracy_delta.py -od $OUTPUT_DIR --dataset $DATASET --method_list $METHOD_LIST