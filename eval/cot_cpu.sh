#!/bin/bash
#SBATCH -J cot-cpu                              # Job name
#SBATCH -o slurm/cot-cpu_%j.out                 # output file (%j expands to jobID)
#SBATCH -e slurm/cot-cpu_%j.err                 # error log file (%j expands to jobID)
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
# activate conda environment
source /share/apps/anaconda3/2021.05/etc/profile.d/conda.sh
# NOTE: this assumes that conda environment is called `dataset`
# change this to your conda environment as necessary
conda activate dataset

TEMPERATURE=0
# if TEMPERATURE=0, then sampling is greedy so no need run with multiple seeds
if (( $(echo "$TEMPERATURE == 0" | bc -l) ))
then
    seed_list="1"
else
    seed_list="1 2 3 4 5"
fi

source eval/constants.sh

# NOTE: specify batch size to save intermediate batches
python -m phantom_eval \
    --method cot \
    -od $1 \
    -m $2 \
    -bs 10 \
    --split_list $SPLIT_LIST \
    --inf_seed_list $seed_list \
    --inf_temperature $TEMPERATURE