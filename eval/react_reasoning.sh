#!/bin/bash
#SBATCH -J react-reasoning                              # Job name
#SBATCH -o slurm/react-reasoning_%j.out                 # output file (%j expands to jobID)
#SBATCH -e slurm/react-reasoning_%j.err                 # error log file (%j expands to jobID)
#SBATCH --mail-type=ALL                      # Request status by email
#SBATCH --mail-user=ag2435@cornell.edu       # Email address to send results to.
#SBATCH -N 1                                 # Total number of nodes requested
#SBATCH -n 8                                 # Total number of cores requested
#SBATCH --get-user-env                       # retrieve the users login environment
#SBATCH --mem=100000                         # server memory (MBs) requested (per node)

# Example usage (make sure to activate conda environment first):
# if running on G2:
# sbatch --gres=gpu:a6000:8 --partition=kilian -t infinite eval/react_L.sh <output directory>
# if running on empire:
# sbatch --gres=gpu:4 --partition=cornell -t 1-00:00:00 eval/react_L.sh <output directory>

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

TEMPERATURE=0

source eval/constants.sh

# Get the number of gpus by counting the number of lines in the output of nvidia-smi
NUM_GPUS=$(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l)
echo "Number of GPUs: $NUM_GPUS"
# Check for the next available port not in use with vllm
PORT=8000
while lsof -Pi :$PORT -sTCP:LISTEN -t; do
    PORT=$((PORT + 1))
done
echo "Using port: $PORT"

# Function to check if the server is up
check_server() {
    local model_name=$1
    response=$(curl -o /dev/null -s -w "%{http_code}" http://0.0.0.0:$PORT/v1/chat/completions \
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

for model_name in "${REASONING_MODELS[@]}"
do
    # Start the vLLM server in the background
    echo "Starting vLLM server..."
    vllm_cmd="vllm serve $model_name --api-key token-abc123 --tensor_parallel_size $NUM_GPUS --port $PORT"
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
        --method react \
        -od $1 \
        -m $model_name \
        --split_list $SPLIT_LIST \
        --inf_seed_list $(get_inf_seed_list $TEMPERATURE) \
        --inf_temperature $TEMPERATURE \
        -bs 10 \
        --inf_vllm_port $PORT"
    echo $cmd
    eval $cmd

    # Stop the vLLM server using pkill
    echo "Stopping vLLM server..."
    pkill -e -f vllm
    echo "vLLM server stopped."
done
