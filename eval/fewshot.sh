#!/bin/bash
#SBATCH -J fewshot-small                              # Job name
#SBATCH -o slurm/fewshot-small_%j.out                 # output file (%j expands to jobID)
#SBATCH -e slurm/fewshot-small_%j.err                 # error log file (%j expands to jobID)
#SBATCH --mail-type=ALL                      # Request status by email 
#SBATCH --mail-user=ag2435@cornell.edu       # Email address to send results to.
#SBATCH -N 1                                 # Total number of nodes requested
#SBATCH -n 4                                 # Total number of cores requested
#SBATCH --get-user-env                       # retrieve the users login environment
#SBATCH --mem=32000                         # server memory (MBs) requested (per node)
#SBATCH -t infinite                           # Time limit (hh:mm:ss)
#SBATCH --gres=gpu:3090:1                   # Number of GPUs requested
#SBATCH --partition=kilian                   # Request partition

# Script for running fewshot evaluation on all small models (<4 B params)
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

TEMPERATURE=0

source eval/constants.sh

# check which modelsize to run
if [ "$1" == "large" ]; then
    MODELS=("${LARGE_MODELS[@]}")
elif [ "$1" == "medium" ]; then
    MODELS=("${MEDIUM_MODELS[@]}")
elif [ "$1" == "small" ]; then
    MODELS=("${SMALL_MODELS[@]}")
else
    echo "Usage: $0 {large|medium|small}"
    exit 1
fi

for model_name in "${MODELS[@]}"
do
    cmd="python -m phantom_eval \
        --method fewshot \
        -od $1 \
        -m $model_name \
        --split_list $SPLIT_LIST \
        --inf_seed_list $(get_inf_seed_list $TEMPERATURE) \
        --inf_temperature $TEMPERATURE"
    echo $cmd
    eval $cmd
done