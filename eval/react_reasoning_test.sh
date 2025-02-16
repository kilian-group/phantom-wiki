#!/bin/bash
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

model_name = $2
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
    -bs 10 \
    -bn 20 \
    --inf_vllm_port $PORT"
echo $cmd
eval $cmd

# Stop the vLLM server using pkill
echo "Stopping vLLM server..."
pkill -e -f vllm
echo "vLLM server stopped."
