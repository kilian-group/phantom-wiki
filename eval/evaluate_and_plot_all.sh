#!/bin/bash
# Script to generate tables and plots for exploratory data analysis
# Example usage (make sure you are in the repo root directory):
# ```bash
# ./eval/evaluate_and_plot_all.sh OUTPUT_DIRECTORY "zeroshot fewshot"
# ./eval/evaluate_and_plot_all.sh OUTPUT_DIRECTORY
# ```
# The second command (without the method list) will use the default method list

OUTPUT_DIR=$1

source eval/constants.sh

# If second argument is provided, use that for METHOD_LIST
if [ -z "$2" ]; then
    echo "Using default method list"
    METHOD_LIST=$METHODS
else
    METHOD_LIST=($2)
fi

echo "Dataset: $DATASET"

read -p "Enter DATA_QUESTION_DEPTH (default: $DATA_QUESTION_DEPTH): " DATA_QUESTION_DEPTH
read -p "Enter DATA_SIZE_LIST (default: $DATA_SIZE_LIST): " DATA_SIZE_LIST

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
        python eval/plot_hops_accuracy.py -od $OUTPUT_DIR --method $METHOD --depth $DATA_QUESTION_DEPTH --size $data_size --dataset $DATASET
        python eval/plot_difficulty_accuracy.py -od $OUTPUT_DIR --method $METHOD --depth $DATA_QUESTION_DEPTH --size $data_size --dataset $DATASET
        python eval/plot_aggregation_accuracy.py -od $OUTPUT_DIR --method $METHOD --depth $DATA_QUESTION_DEPTH --size $data_size --dataset $DATASET
        python eval/plot_solutions_accuracy.py -od $OUTPUT_DIR --method $METHOD --depth $DATA_QUESTION_DEPTH --size $data_size --dataset $DATASET
        if [ $METHOD == "react" ] || [ $METHOD == "act" ]; then
            python eval/plot_hops_interactions.py -od $OUTPUT_DIR --method $METHOD --depth $DATA_QUESTION_DEPTH --size $data_size --dataset $DATASET
            python eval/plot_difficulty_interactions.py -od $OUTPUT_DIR --method $METHOD --depth $DATA_QUESTION_DEPTH --size $data_size --dataset $DATASET
        fi
    done

    # plot results for all splits
    python eval/plot_difficulty_accuracy_all_splits.py -od $OUTPUT_DIR --method $METHOD --dataset $DATASET

    # plot precision-recall for all splits
    python eval/plot_prec_recall_all_splits.py -od $OUTPUT_DIR --method $METHOD

    # plot per-model contour plots
    python eval/plot_size_hops_accuracy_per_model.py -od $OUTPUT_DIR --method $METHOD --dataset $DATASET
    python eval/plot_size_difficulty_accuracy_per_model.py -od $OUTPUT_DIR --method $METHOD --dataset $DATASET
    # plot pareto curves
    python eval/plot_size_hops_accuracy.py -od $OUTPUT_DIR --method $METHOD --dataset $DATASET
    python eval/plot_size_difficulty_accuracy.py -od $OUTPUT_DIR --method $METHOD --dataset $DATASET
done
