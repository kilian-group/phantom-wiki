#!/bin/bash
#SBATCH -J zeroshot-large                              # Job name
#SBATCH -o slurm/zeroshot-large_%j.out                 # output file (%j expands to jobID)
#SBATCH -e slurm/zeroshot-large_%j.err                 # error log file (%j expands to jobID)
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

TEMPERATURE=0.7

source eval/constants.sh

for model_name in "${LARGE_MODELS[@]}"
do
    cmd="python -m phantom_eval \
        --method reasoning \
        -od $1 \
        -m $model_name \
        --split_list depth_20_size_50_seed_1 \
        --inf_seed_list 1 \
        --inf_temperature $TEMPERATURE"
                # --split_list $SPLIT_LIST \
                # --inf_seed_list $(get_inf_seed_list $TEMPERATURE) \
    echo $cmd
    eval $cmd
done