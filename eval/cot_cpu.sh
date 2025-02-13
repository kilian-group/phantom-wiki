#!/bin/bash
#SBATCH -J cot-cpu                              # Job name
#SBATCH -o slurm/cot-cpu_%j.out                 # output file (%j expands to jobID)
#SBATCH -e slurm/cot-cpu_%j.err                 # error log file (%j expands to jobID)
#SBATCH --mail-type=ALL                      # Request status by email 
#SBATCH -N 1                                 # Total number of nodes requested
#SBATCH -n 2                                 # Total number of cores requested
#SBATCH --get-user-env                       # retrieve the users login environment
#SBATCH --mem=8000                         # server memory (MBs) requested (per node)

# check that the correct number of arguments were passed
if [ -z "$1" ]; then
    echo "Usage: $0 <output directory>"
    exit 1
fi

TEMPERATURE=0

source eval/constants.sh

for model_name in "${API_MODELS[@]}"
do
    cmd="python -m phantom_eval \
        --method cot \
        -od $1 \
        -m $model_name \
        --split_list depth_10_size_2500_seed_1 depth_10_size_2500_seed_2 depth_10_size_2500_seed_3 \
        --inf_seed_list $(get_inf_seed_list $TEMPERATURE) \
        --inf_temperature $TEMPERATURE \
        --inf_usage_tier 0"
    echo $cmd
    eval $cmd
done