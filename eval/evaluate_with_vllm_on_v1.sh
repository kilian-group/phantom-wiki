#!/bin/bash
# Script to generate tables and plots for any new LLM
# Example usage (make sure you are in the repo root directory). Additional flags can be passed to the script after method list
# ```bash
# ./eval/evaluate_with_vllm_on_v1.sh OUTPUT_DIRECTORY MODEL_NAME_OR_PATH "zeroshot cot zeroshot-rag cot-rag react"
# ```

# Load constants
source eval/constants.sh
# Parse command line arguments
OUTPUT_DIR=$1
MODEL_LIST=$2
METHOD_LIST=$3

# Get additional flags passed to the script
shift 3
plotting_cmd_args=$@

echo "Models: $MODEL_LIST"
echo "Methods: $METHOD_LIST"
echo "Additional plotting flags: $plotting_cmd_args"

# Run phantom_eval with vLLM
for method in $METHOD_LIST
do
    # if method contains "zeroshot" or "cot", add the --inf_vllm_offline flag
    phantom_eval_cmd_args="--server vllm"
    if [[ $method == *"zeroshot"* ]] || [[ $method == *"cot"* ]]; then
        phantom_eval_cmd_args+=" --inf_vllm_offline"
    fi

    for model in $MODEL_LIST
    do
        python -m phantom_eval \
            -od $OUTPUT_DIR \
            --dataset "kilian-group/phantom-wiki-v1" \
            --split_list depth_20_size_50_seed_1 depth_20_size_50_seed_2 depth_20_size_50_seed_3 \
            --model_name $model \
            --method $method \
            $phantom_eval_cmd_args \

    done
done

# Figure 1: Reasoning and retrieval heatmaps
for model in $MODEL_LIST
do
    # TODO make plots for each model
    python eval/plot_reasoning_retrieval.py -od $OUTPUT_DIR --dataset $DATASET -m $model $plotting_cmd_args
done

# Table 2: F1 scores
python eval/format_leaderboard.py -od $OUTPUT_DIR --dataset $DATASET --model_list $MODEL_LIST --method_list $METHOD_LIST $plotting_cmd_args

# Figure 3: F1 scores as a function of difficulty, as measured by reasoning steps
python eval/plot_reasoning.py -od $OUTPUT_DIR --dataset $DATASET --model_list $MODEL_LIST $plotting_cmd_args

# Figure 4: F1 scores as a function of universe size
python eval/plot_retrieval.py -od $OUTPUT_DIR --dataset $DATASET --model_list $MODEL_LIST $plotting_cmd_args
