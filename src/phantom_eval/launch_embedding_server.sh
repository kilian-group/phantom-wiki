#!/bin/bash

check_server() {
    local model_name=$1
    local port=$2
    # echo http://0.0.0.0:8001/v1/chat/completions
    response=$(curl -o /dev/null -s -w "%{http_code}" http://0.0.0.0:$port/v1/chat/completions \
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

# source /home/jcl354/anaconda3/etc/profile.d/conda.sh
# conda activate dataset

model_name=$1
port=$2
CUDA_VISIBLE_DEVICES=$3
if ! check_server $model_name $port; then
    echo "Starting $model_name embedding server..."
    eval export CUDA_VISIBLE_DEVICES="$CUDA_VISIBLE_DEVICES"
    vllm_cmd="nohup vllm serve $model_name --api-key token-abc123 --tensor_parallel_size 1 --task embed --host 0.0.0.0 --port $port"
    nohup $vllm_cmd &
    # echo $vllm_cmd
fi

SLEEP=40
while ! check_server $model_name $port; do
    echo "Embedding server is not up yet. Checking again in $SLEEP seconds..."
    sleep $SLEEP
done
# echo "Embedding server is up and running."

