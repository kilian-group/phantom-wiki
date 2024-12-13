#!/bin/bash
#SBATCH -J vllm                              # Job name
#SBATCH -o slurm/vllm_%j.out                 # output file (%j expands to jobID)
#SBATCH -e slurm/vllm_%j.err                 # error log file (%j expands to jobID)
#SBATCH --mail-type=ALL                      # Request status by email 
#SBATCH --mail-user=ag2435@cornell.edu       # Email address to send results to.
#SBATCH -N 1                                 # Total number of nodes requested
#SBATCH -n 8                                 # Total number of cores requested
#SBATCH --get-user-env                       # retrieve the users login environment
#SBATCH --mem=100000                         # server memory (MBs) requested (per node)
#SBATCH -t infinite                           # Time limit (hh:mm:ss)
#SBATCH --gres=gpu:a6000:8                   # Number of GPUs requested
#SBATCH --partition=kilian                   # Request partition

# check that the correct number of arguments were passed
if [ -z "$1" ]; then
    echo "Usage: $0 <model>"
    exit 1
fi

python zeroshot_local.py \
    -od out-test-1203 \
    -m $1 \
    --split_list depth_10_size_26_seed_1 depth_10_size_50_seed_1 depth_10_size_100_seed_1 depth_10_size_200_seed_1 \
    --seed_list 1 2 3 4 5 \
    --tensor_parallel_size 8