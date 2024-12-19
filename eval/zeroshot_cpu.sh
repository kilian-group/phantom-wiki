#!/bin/bash
#SBATCH -J zeroshot-cpu                              # Job name
#SBATCH -o slurm/zeroshot-cpu_%j.out                 # output file (%j expands to jobID)
#SBATCH -e slurm/zeroshot-cpu_%j.err                 # error log file (%j expands to jobID)
#SBATCH --mail-type=ALL                      # Request status by email 
#SBATCH --mail-user=ag2435@cornell.edu       # Email address to send results to.
#SBATCH -N 1                                 # Total number of nodes requested
#SBATCH -n 2                                 # Total number of cores requested
#SBATCH --get-user-env                       # retrieve the users login environment
#SBATCH --mem=8000                         # server memory (MBs) requested (per node)
#SBATCH -t infinite                           # Time limit (hh:mm:ss)
#SBATCH --partition=kilian                   # Request partition

# check that the correct number of arguments were passed
if [ -z "$1" ] && [ -z "$2" ]; then
    echo "Usage: $0 <output directory> <model name>"
    exit 1
fi

TEMPERATURE=0.7
# NOTE: specify batch size to save intermediate batches
python -m phantom_eval \
    --method zeroshot \
    -od $1 \
    -m $2 \
    -bs 10 \
    --split_list depth_10_size_26_seed_1 depth_10_size_50_seed_1 depth_10_size_100_seed_1 depth_10_size_200_seed_1 \
    --seed_list 1 2 3 4 5 \
    --inf_temperature $TEMPERATURE