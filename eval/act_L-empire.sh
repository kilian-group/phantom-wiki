#!/bin/bash
#SBATCH -J act-large                              # Job name
#SBATCH -o slurm/act-large_%j.out                 # output file (%j expands to jobID)
#SBATCH -e slurm/act-large_%j.err                 # error log file (%j expands to jobID)
#SBATCH --mail-type=ALL                      # Request status by email 
#SBATCH --mail-user=ag2435@cornell.edu       # Email address to send results to.
#SBATCH -N 1                                 # Total number of nodes requested
#SBATCH -n 8                                 # Total number of cores requested
#SBATCH --get-user-env                       # retrieve the users login environment
#SBATCH --mem=100000                         # server memory (MBs) requested (per node)
#SBATCH -t 1-00:00:00                           # Time limit (hh:mm:ss)
#SBATCH --gres=gpu:4                   # Number of GPUs requested
#SBATCH --partition=cornell                   # Request partition
#SBATCH --nodelist=alphagpu03

# Script for running zero-shot evaluation on all large models (10-70 B params)
# GPU requirements when using max context length (i.e., `max_model_len=None`)
# Model Size    | A6000 GPU  | H100 GPU
# ------------- | -----------|-----------
# ~8B models    | 1          | 1
# ~70B models   | 8          | 4

# check that the correct number of arguments were passed
if [ -z "$1" ]; then
    echo "Usage: $0 <output directory>"
    exit 1
fi
# activate conda environment
source ~/miniconda3/etc/profile.d/conda.sh
# NOTE: this assumes that conda environment is called `dataset`
# change this to your conda environment as necessary
conda activate dataset

# list of models
MODELS=(
    # 'google/gemma-2-27b-it'
    # 'microsoft/phi-3.5-moe-instruct'
    'meta-llama/llama-3.1-70b-instruct'
    'meta-llama/llama-3.3-70b-instruct'
    # 'meta-llama/llama-3.1-8b-instruct'
)
TEMPERATURE=0
# if TEMPERATURE=0, then sampling is greedy so no need run with muliptle seeds
if (( $(echo "$TEMPERATURE == 0" | bc -l) ))
then
    seed_list="1"
else
    seed_list="1 2 3 4 5"
fi

# Function to check if the server is up
check_server() {
    local model_name=$1
    response=$(curl -o /dev/null -s -w "%{http_code}" http://0.0.0.0:8000/v1/chat/completions \
                    -X POST \
                    -H "Content-Type: application/json" \
                    -H "Authorization: Bearer token-abc123" \
                    -d "{\"model\": \"$model_name\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello!\"}]}")
    if [ "$response" -eq 200 ]; then
        return 0
    else
        return 1
    fi
}

for model_name in "${MODELS[@]}"
do
    # Start the vLLM server in the background
    echo "Starting vLLM server..."
    vllm_cmd="nohup vllm serve $model_name --api-key token-abc123 --tensor_parallel_size 4"
    echo $vllm_cmd
    nohup $vllm_cmd &
    
    # Wait for the server to start
    echo "Waiting for vLLM server to start..."
    SLEEP=60
    while ! check_server $model_name; do
        echo "Server is not up yet. Checking again in $SLEEP seconds..."
        sleep $SLEEP
    done

    echo "vLLM server is up and running."

    # Run the main Python script
    cmd="python -m phantom_eval \
        --method act \
        -od $1 \
        -m $model_name \
        --split_list depth_10_size_26_seed_1 depth_10_size_50_seed_1 depth_10_size_100_seed_1 depth_10_size_200_seed_1 depth_10_size_500_seed_1 \
        --inf_seed_list $seed_list \
        --inf_temperature $TEMPERATURE \
        -bs 10"
    echo $cmd
    eval $cmd

    # Stop the vLLM server using pkill
    echo "Stopping vLLM server..."
    pkill -e -f vllm
    echo "vLLM server stopped."
done