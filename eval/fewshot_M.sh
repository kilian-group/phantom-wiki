#!/bin/bash
#SBATCH -J fewshot-medium                              # Job name
#SBATCH -o slurm/fewshot-medium_%j.out                 # output file (%j expands to jobID)
#SBATCH -e slurm/fewshot-medium_%j.err                 # error log file (%j expands to jobID)
#SBATCH --mail-type=ALL                      # Request status by email 
#SBATCH --mail-user=ag2435@cornell.edu       # Email address to send results to.
#SBATCH -N 1                                 # Total number of nodes requested
#SBATCH -n 8                                 # Total number of cores requested
#SBATCH --get-user-env                       # retrieve the users login environment
#SBATCH --mem=100000                         # server memory (MBs) requested (per node)
#SBATCH -t infinite                           # Time limit (hh:mm:ss)
#SBATCH --gres=gpu:a6000:2                   # Number of GPUs requested
#SBATCH --partition=kilian                   # Request partition

# Script for running fewshot evaluation on all medium models (<10 B params)
# GPU requirements when using max context length (i.e., `max_model_len=None`)
# Model Size    | 3090 GPU   | A6000 GPU | H100 GPU
# ------------- | -----------|-----------|---------
# ~4B models    | 1          | 1         | 1
# ~8B models    | 2          | 1         | 1
# ~70B models   |            | 8         | 4
# NOTE: meta-llama/llama-3.2-11b-vision-instruct runs out of memory on 8 A6000 GPUs

# check that the correct number of arguments were passed
if [ -z "$1" ]; then
    echo "Usage: $0 <output directory>"
    exit 1
fi
# activate conda environment
source /share/apps/anaconda3/2021.05/etc/profile.d/conda.sh
# NOTE: this assumes that conda environment is called `dataset`
# change this to your conda environment as necessary
conda activate dataset

# list of models
MODELS=(
    # 'microsoft/phi-3.5-mini-instruct' # runs out of memory on 2 A6000 GPUs
    'meta-llama/llama-3.2-3b-instruct'
    'meta-llama/llama-3.1-8b-instruct'
    'google/gemma-2-9b-it'
    'mistralai/mistral-7b-instruct-v0.3'
)
TEMPERATURE=0
# if TEMPERATURE=0, then sampling is greedy so no need run with multiple seeds
if (( $(echo "$TEMPERATURE == 0" | bc -l) ))
then
    seed_list="1"
else
    seed_list="1 2 3 4 5"
fi

source eval/constants.sh

for model_name in "${MODELS[@]}"
do
    cmd="python -m phantom_eval \
        --method fewshot \
        -od $1 \
        -m $model_name \
        --split_list $SPLIT_LIST \
        --inf_seed_list $seed_list \
        --inf_temperature $TEMPERATURE"
    echo $cmd
    eval $cmd
done