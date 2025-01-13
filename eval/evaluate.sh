#!/bin/bash
# Script to generate all tables and plots
# Example usage (make sure you are in the repo root directory):
# ```bash
# ./eval/evaluate.sh out zeroshot
# ```

OUTPUT_DIR=$1
METHOD=$2
# csv results
python eval/format_split_accuracy.py -od $OUTPUT_DIR --method $METHOD
python eval/format_split_type_accuracy.py -od $OUTPUT_DIR --method $METHOD

# plot results
python eval/plot_size_accuracy.py -od $OUTPUT_DIR --method $METHOD
for split_name in depth_10_size_26_seed_1 depth_10_size_50_seed_1 depth_10_size_100_seed_1 depth_10_size_200_seed_1
do
    python eval/plot_hops_accuracy.py -od $OUTPUT_DIR --method $METHOD --split_name $split_name
    python eval/plot_aggregation_accuracy.py -od $OUTPUT_DIR --method $METHOD --split_name $split_name
    python eval/plot_solutions_accuracy.py -od $OUTPUT_DIR --method $METHOD --split_name $split_name
    # Note: the following script fails for method != react, but that's fine
    python eval/plot_hops_interactions.py -od $OUTPUT_DIR --method $METHOD --split_name $split_name
done