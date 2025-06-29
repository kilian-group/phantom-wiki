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
MODEL_LIST=$2
METHOD_LIST=$3

# Get additional flags passed to the script
shift 3
cmd_args=$@

echo "Dataset: $DATASET"
echo "Models: $MODEL_LIST"
echo "Methods: $METHOD_LIST"
echo "Additional flags: $cmd_args"

# Figure 1: Reasoning and retrieval heatmaps
for model in $MODEL_LIST
do
    # TODO make plots for each model
    python eval/plot_reasoning_retrieval.py -od $OUTPUT_DIR --dataset $DATASET -m $model $cmd_args
done

# Table 2: F1 scores
python eval/format_leaderboard.py -od $OUTPUT_DIR --dataset $DATASET --model_list $MODEL_LIST --method_list $METHOD_LIST $cmd_args

# Figure 3: F1 scores as a function of difficulty, as measured by reasoning steps
python eval/plot_reasoning.py -od $OUTPUT_DIR --dataset $DATASET --model_list $MODEL_LIST $cmd_args

# Figure 4: F1 scores as a function of universe size
python eval/plot_retrieval.py -od $OUTPUT_DIR --dataset $DATASET --model_list $MODEL_LIST $cmd_args
