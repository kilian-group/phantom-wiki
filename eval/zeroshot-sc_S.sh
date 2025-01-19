#!/bin/bash
#SBATCH -J zeroshot-sc-small                              # Job name
#SBATCH -o slurm/zeroshot-sc-small_%j.out                 # output file (%j expands to jobID)
#SBATCH -e slurm/zeroshot-sc-small_%j.err                 # error log file (%j expands to jobID)
#SBATCH --mail-type=ALL                      # Request status by email 
#SBATCH -N 1                                 # Total number of nodes requested
#SBATCH -n 4                                 # Total number of cores requested
#SBATCH --get-user-env                       # retrieve the users login environment
#SBATCH --mem=32000                         # server memory (MBs) requested (per node)

# Example usage (make sure to activate conda environment first):
# if running on G2:
# sbatch --gres=gpu:3090:1 --partition=kilian -t infinite eval/zeroshot-sc_M.sh <output directory>
# if running on empire:
# sbatch --gres=gpu:1 --partition=cornell -t 1-00:00:00 eval/zeroshot-sc_M.sh <output directory>

# Script for running zeroshot with self-consistency evaluation on all medium models (<10 B params)
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

# list of models
MODELS=(
    'google/gemma-2-2b-it'
    'meta-llama/llama-3.2-1b-instruct'
)
TEMPERATURE=0.7
# if TEMPERATURE=0, then sampling is greedy so no need run with muliptle seeds
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
        --method zeroshot-sc \
        -od $1 \
        -m $model_name \
        --split_list $SPLIT_LIST \
        --inf_seed_list $seed_list \
        --inf_temperature $TEMPERATURE"
    echo $cmd
    eval $cmd
done