#!/bin/bash
#SBATCH -J reasoning-large                              # Job name
#SBATCH -o slurm/reasoning-large_%j.out                 # output file (%j expands to jobID)
#SBATCH -e slurm/reasoning-large_%j.err                 # error log file (%j expands to jobID)
#SBATCH --mail-type=ALL                      # Request status by email
#SBATCH --mail-user=ag2435@cornell.edu       # Email address to send results to.
#SBATCH -N 1                                 # Total number of nodes requested
#SBATCH -n 8                                 # Total number of cores requested
#SBATCH --get-user-env                       # retrieve the users login environment
#SBATCH --mem=100000                         # server memory (MBs) requested (per node)

# Example usage (make sure to activate conda environment first):
# if running on G2:
# sbatch --gres=gpu:a6000:8 --partition=kilian -t infinite eval/zeroshot_L.sh <output directory>
# if running on empire:
# sbatch --gres=gpu:4 --partition=cornell -t 1-00:00:00 eval/zeroshot_L.sh <output directory>

# Script for running zero-shot evaluation on all large models (10-70 B params)
# GPU requirements when using max context length (i.e., `max_model_len=None`)
# Model Size    | 3090 GPU   | A6000 GPU | H100 GPU
# ------------- | -----------|-----------|---------
# ~4B models    | 1          | 1         | 1
# ~8B models    | 2          | 1         | 1
# ~70B models   |            | 8         | 4

# check that the correct number of arguments were passed
if [ -z "$1" ]; then
    echo "Usage: $0 <output directory>"
    exit 1
fi

TEMPERATURE=0.6
TOP_P=0.95
REASONING_MODELS=('deepseek-ai/deepseek-r1-distill-qwen-32b')

source eval/constants.sh

SPLIT_LIST=""
DATA_SEED_LIST="1 2 3"
DATA_DEPTH="20"
DATA_SIZE_LIST="500 50"

for data_seed in $DATA_SEED_LIST
do
    for data_size in $DATA_SIZE_LIST
    do
        SPLIT_LIST+="depth_${DATA_DEPTH}_size_${data_size}_seed_${data_seed} "
    done
done

for model_name in "${REASONING_MODELS[@]}"
do
    cmd="python -m phantom_eval \
        --method cot-reasoning \
        -od $1 \
        -m $model_name \
        --split_list $SPLIT_LIST \
        --inf_seed_list $(get_inf_seed_list $TEMPERATURE) \
        --inf_temperature $TEMPERATURE \
        --inf_top_p $TOP_P
        -bs 10
        "

    echo $cmd
    eval $cmd
done
