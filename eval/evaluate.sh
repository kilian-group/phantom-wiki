#!/bin/bash
OUTPUT_DIR=$1
METHOD=$2
# csv results
python format_split_accuracy.py -od $OUTPUT_DIR --method $METHOD
python format_split_type_accuracy.py -od $OUTPUT_DIR --method $METHOD

# plot results
python plot_size_accuracy.py -od $OUTPUT_DIR --method $METHOD
for split_name in depth_10_size_26_seed_1 depth_10_size_50_seed_1 depth_10_size_100_seed_1 depth_10_size_200_seed_1
do
    python plot_hops_accuracy.py -od $OUTPUT_DIR --method $METHOD --split_name $split_name
    python plot_aggregation_accuracy.py -od $OUTPUT_DIR --method $METHOD --split_name $split_name
    python plot_solutions_accuracy.py -od $OUTPUT_DIR --method $METHOD --split_name $split_name
done