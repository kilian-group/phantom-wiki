#!/bin/bash
# Script to generate tables and plots for the ICML paper
# Example usage (make sure you are in the repo root directory):
# ```bash
# ./eval/evaluate_icml.sh OUTPUT_DIRECTORY "zeroshot cot zeroshot-rag cot-rag react"
# ./eval/evaluate_icml.sh OUTPUT_DIRECTORY
# ```
# If the second argument is not provided, the default method list will be used.

# Load constants
source eval/constants.sh
# Parse command line arguments
OUTPUT_DIR=$1
# If second argument is provided, use that for METHOD_LIST
if [ -z "$2" ]; then
    echo "Using default method list"
    METHOD_LIST="zeroshot cot zeroshot-rag cot-rag react"
else
    METHOD_LIST=$2
fi

# Override whichever dataset was specified in constants.sh
DATASET=mlcore/phantom-wiki-v1
echo "Dataset: $DATASET"
MODEL="meta-llama/llama-3.3-70b-instruct"

# Figure 1: Reasoning and retrieval heatmaps
python eval/plot_reasoning_retrieval.py -od $OUTPUT_DIR --dataset $DATASET -m $MODEL

# Table 2: F1 scores
python eval/format_leaderboard.py -od $OUTPUT_DIR --dataset $DATASET --method_list $METHOD_LIST

# Figure 3: F1 scores as a function of difficulty, as measured by reasoning steps
python eval/plot_reasoning.py -od $OUTPUT_DIR --dataset $DATASET

# Figure 4: F1 scores as a function of universe size
python eval/plot_retrieval.py -od $OUTPUT_DIR --dataset $DATASET
