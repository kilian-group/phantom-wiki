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
DATASET=mlcore/phantom-wiki-v050
echo "Dataset: $DATASET"

#
# Sec 4: Main accuracy table across methods/models
#
python eval/format_leaderboard.py -od $OUTPUT_DIR --dataset $DATASET --method_list $METHOD_LIST

#
# Sec 5: Evaluating Reasoning
#
python eval/plot_reasoning.py -od $OUTPUT_DIR --dataset $DATASET --method_list $METHOD_LIST

#
# Sec 6: Evaluating Retrieval
#
python eval/plot_retrieval.py -od $OUTPUT_DIR --dataset $DATASET --method_list $METHOD_LIST
