#!/bin/bash
# Script to generate tables and plots for exploratory data analysis
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
        "zeroshot-rag"
        "cot-rag"
    )
else
    METHOD_LIST=($2)
fi

echo "Splits: $SPLIT_LIST"

echo "Dataset: $DATASET"

#
# Figures for exporatory data analysis
#
for METHOD in "${METHOD_LIST[@]}"
do
    # csv results
    python eval/format_split_accuracy.py -od $OUTPUT_DIR --method $METHOD --dataset $DATASET
    python eval/format_split_type_accuracy.py -od $OUTPUT_DIR --method $METHOD --dataset $DATASET

    # plot results
    python eval/plot_size_accuracy.py -od $OUTPUT_DIR --method $METHOD --dataset $DATASET
    for data_size in $DATA_SIZE_LIST
    do
        python eval/plot_hops_accuracy.py -od $OUTPUT_DIR --method $METHOD --depth $DATA_DEPTH --size $data_size --dataset $DATASET
        python eval/plot_difficulty_accuracy.py -od $OUTPUT_DIR --method $METHOD --depth $DATA_DEPTH --size $data_size --dataset $DATASET
        python eval/plot_aggregation_accuracy.py -od $OUTPUT_DIR --method $METHOD --depth $DATA_DEPTH --size $data_size --dataset $DATASET
        python eval/plot_solutions_accuracy.py -od $OUTPUT_DIR --method $METHOD --depth $DATA_DEPTH --size $data_size --dataset $DATASET
        if [ $METHOD == "react" ] || [ $METHOD == "act" ]; then
            python eval/plot_hops_interactions.py -od $OUTPUT_DIR --method $METHOD --depth $DATA_DEPTH --size $data_size --dataset $DATASET
            python eval/plot_difficulty_interactions.py -od $OUTPUT_DIR --method $METHOD --depth $DATA_DEPTH --size $data_size --dataset $DATASET
        fi
    done

    # plot results for all splits
    python eval/plot_difficulty_accuracy_all_splits.py -od $OUTPUT_DIR --method $METHOD --split_list $SPLIT_LIST --dataset $DATASET

    # plot precision-recall for all splits
    python eval/plot_prec_recall_all_splits.py -od $OUTPUT_DIR --method $METHOD --split_list $SPLIT_LIST

    # plot per-model contour plots
    python eval/plot_size_hops_accuracy_per_model.py -od $OUTPUT_DIR --method $METHOD --dataset $DATASET
    python eval/plot_size_difficulty_accuracy_per_model.py -od $OUTPUT_DIR --method $METHOD --dataset $DATASET
    # plot pareto curves
    python eval/plot_size_hops_accuracy.py -od $OUTPUT_DIR --method $METHOD --dataset $DATASET
    python eval/plot_size_difficulty_accuracy.py -od $OUTPUT_DIR --method $METHOD --dataset $DATASET
done
