#!/bin/bash
# Script to generate all tables and plots
# Example usage (make sure you are in the repo root directory):
# ```bash
# ./eval/evaluate.sh OUTPUT_DIRECTORY "zeroshot fewshot"
# ./eval/evaluate.sh OUTPUT_DIRECTORY
# ```
# The second command (without the method list) will use the default method list

OUTPUT_DIR=$1
# If second argument is provided, use that for METHOD_LIST
if [ -z "$2" ]; then
    echo "Using default method list"
    METHOD_LIST=(
        "zeroshot"
        "fewshot"
        "cot"
        "zeroshot-sc"
        "fewshot-sc"
        "cot-sc"
        "react"
        "act"
    )
else
    METHOD_LIST=($2)
fi
# construct split list
for seed in 1 2 3 4 5
do
    for size in 26 50 100 200 500
    do
        SPLIT_LIST+="depth_10_size_${size}_seed_${seed} "
    done
done
echo "Splits: $SPLIT_LIST"

for METHOD in "${METHOD_LIST[@]}"
do
    # # csv results
    # python eval/format_split_accuracy.py -od $OUTPUT_DIR --method $METHOD
    # python eval/format_split_type_accuracy.py -od $OUTPUT_DIR --method $METHOD

    # # plot results
    # python eval/plot_size_accuracy.py -od $OUTPUT_DIR --method $METHOD
    # for split_name in $SPLIT_LIST
    # do
    #     python eval/plot_hops_accuracy.py -od $OUTPUT_DIR --method $METHOD --split_name $split_name
    #     python eval/plot_aggregation_accuracy.py -od $OUTPUT_DIR --method $METHOD --split_name $split_name
    #     python eval/plot_solutions_accuracy.py -od $OUTPUT_DIR --method $METHOD --split_name $split_name
    #     if [ $METHOD == "react" ] || [ $METHOD == "act" ]; then
    #         python eval/plot_hops_interactions.py -od $OUTPUT_DIR --method $METHOD --split_name $split_name
    #     fi
    # done

    # plot per-model contour plots
    python eval/plot_size_hops_accuracy_per_model.py -od $OUTPUT_DIR --method $METHOD
    # # plot pareto curves
    # python eval/plot_size_hops_accuracy.py -od $OUTPUT_DIR --method $METHOD
done