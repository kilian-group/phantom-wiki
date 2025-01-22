#!/bin/bash
# Script to generate all tables and plots
# Example usage (make sure you are in the repo root directory):
# ```bash
# ./eval/evaluate.sh OUTPUT_DIRECTORY "zeroshot fewshot"
# ./eval/evaluate.sh OUTPUT_DIRECTORY
# ```
# The second command (without the method list) will use the default method list

OUTPUT_DIR=$1

source eval/constants.sh

# If second argument is provided, use that for METHOD_LIST
if [ -z "$2" ]; then
    echo "Using default method list"
    METHOD_LIST=(
        "zeroshot"
        "fewshot"
        "cot"
        "react"
        "act"
        "zeroshot-sc"
        "fewshot-sc"
        "cot-sc"
    )
else
    METHOD_LIST=($2)
fi
echo "Splits: $SPLIT_LIST"

for METHOD in "${METHOD_LIST[@]}"
do
    # csv results
    python eval/format_split_accuracy.py -od $OUTPUT_DIR --method $METHOD
    python eval/format_split_type_accuracy.py -od $OUTPUT_DIR --method $METHOD

    # plot results
    python eval/plot_size_accuracy.py -od $OUTPUT_DIR --method $METHOD
    for data_size in $DATA_SIZE_LIST
    do
        python eval/plot_hops_accuracy.py -od $OUTPUT_DIR --method $METHOD --depth $DATA_DEPTH --size $data_size
        python eval/plot_difficulty_accuracy.py -od $OUTPUT_DIR --method $METHOD --depth $DATA_DEPTH --size $data_size
        python eval/plot_aggregation_accuracy.py -od $OUTPUT_DIR --method $METHOD --depth $DATA_DEPTH --size $data_size
        python eval/plot_solutions_accuracy.py -od $OUTPUT_DIR --method $METHOD --depth $DATA_DEPTH --size $data_size
        if [ $METHOD == "react" ] || [ $METHOD == "act" ]; then
            python eval/plot_hops_interactions.py -od $OUTPUT_DIR --method $METHOD --depth $DATA_DEPTH --size $data_size
            python eval/plot_difficulty_interactions.py -od $OUTPUT_DIR --method $METHOD --depth $DATA_DEPTH --size $data_size
        fi
    done

    # plot per-model contour plots
    python eval/plot_size_hops_accuracy_per_model.py -od $OUTPUT_DIR --method $METHOD
    python eval/plot_size_difficulty_accuracy_per_model.py -od $OUTPUT_DIR --method $METHOD
    # plot pareto curves
    python eval/plot_size_hops_accuracy.py -od $OUTPUT_DIR --method $METHOD
    python eval/plot_size_difficulty_accuracy.py -od $OUTPUT_DIR --method $METHOD
done
