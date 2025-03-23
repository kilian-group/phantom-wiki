#!/bin/bash
# Script to generate tables and plots in the paper
# Example usage (make sure you are in the repo root directory). Additional flags can be passed to the script after method list
# ```bash
# ./eval/evaluate.sh OUTPUT_DIRECTORY MODEL_NAME_OR_PATH "zeroshot cot zeroshot-rag cot-rag react"
# # For local datasets, specify the dataset path and add the --from_local flag
# DATASET="/path/to/dataset/" ./eval/evaluate.sh OUTPUT_DIRECTORY MODEL_NAME_OR_PATH "zeroshot cot zeroshot-rag cot-rag react" --from_local
# ```

# Load constants
source eval/constants.sh
# Parse command line arguments
OUTPUT_DIR=$1
MODEL=$2
METHOD_LIST=$3

# Get additional flags passed to the script
shift 3
cmd_args=$@

echo "Dataset: $DATASET"
echo "Model: $MODEL"
echo "Methods: $METHOD_LIST"
echo "Additional flags: $cmd_args"

# Figure 1: Reasoning and retrieval heatmaps
python eval/plot_reasoning_retrieval.py -od $OUTPUT_DIR --dataset $DATASET -m $MODEL $cmd_args

# Table 2: F1 scores
python eval/format_leaderboard.py -od $OUTPUT_DIR --dataset $DATASET --model_list $MODEL --method_list $METHOD_LIST $cmd_args

# Figure 3: F1 scores as a function of difficulty, as measured by reasoning steps
python eval/plot_reasoning.py -od $OUTPUT_DIR --dataset $DATASET --model_list $MODEL $cmd_args

# Figure 4: F1 scores as a function of universe size
python eval/plot_retrieval.py -od $OUTPUT_DIR --dataset $DATASET --model_list $MODEL $cmd_args
