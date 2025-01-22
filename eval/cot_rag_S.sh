#!/bin/bash
#SBATCH -J rag-small                              # Job name
#SBATCH -o slurm/rag-small_%j.out                 # output file (%j expands to jobID)
#SBATCH -e slurm/rag-small_%j.err                 # error log file (%j expands to jobID)
#SBATCH --mail-type=ALL                      # Request status by email 
#SBATCH --mail-user=jcl354@cornell.edu       # Email address to send results to.
#SBATCH -N 1                                 # Total number of nodes requested
#SBATCH -n 8                                 # Total number of cores requested
#SBATCH --get-user-env                       # retrieve the users login environment
#SBATCH --mem=100000                         # server memory (MBs) requested (per node)
#SBATCH -t infinite                           # Time limit (hh:mm:ss)
#SBATCH --gres=gpu:a6000:4                   # Number of GPUs requested
#SBATCH --partition=kilian                   # Request partition

# Script for running zero-shot evaluation on all small models (<4 B params)
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
TEMPERATURE=0

source eval/constants.sh
# activate conda environment
# source /share/apps/anaconda3/2021.05/etc/profile.d/conda.sh
# source /home/jcl354/anaconda3/etc/profile.d/conda.sh
# conda init bash
# NOTE: this assumes that conda environment is called `dataset`
# change this to your conda environment as necessary
# conda activate dataset

# Function to check if the server is up
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

pkill -e -f vllm

# https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html#vllm-serve
for model_name in "${SMALL_MODELS[@]}"
do
    # Start the vLLM server in the background
    port=8000
    echo "Starting vLLM server..."
    eval export CUDA_VISIBLE_DEVICES=0,1,2,3
    vllm_cmd="nohup vllm serve $model_name --api-key token-abc123 --tensor_parallel_size 4 --host 0.0.0.0 --port $port --task generate" #nohup launches this in the background
    echo $vllm_cmd
    nohup $vllm_cmd &
    
    # Wait for the server to start
    echo "Waiting for vLLM server to start..."
    SLEEP=30
    while ! check_server $model_name $port; do
        echo "Server is not up yet. Checking again in $SLEEP seconds..."
        sleep $SLEEP
    done
    echo "vLLM server is up and running."

    # Run the main Python script
    e_port=8001
    eval export CUDA_VISIBLE_DEVICES=0,1,2,3
    cmd="python -m phantom_eval \
        --method cot-retriever \
        -od $1 \
        -m $model_name \
        --split_list $SPLIT_LIST \
        --inf_seed_list $(get_inf_seed_list $TEMPERATURE) \
        --inf_temperature $TEMPERATURE \
        --retriever_method WhereIsAI/UAE-Code-Large-V1 \
        "
        # --force \
    echo $cmd
    eval $cmd

    # Stop the vLLM server using pkill
    echo "Stopping vLLM server..."
    pkill -e -f vllm
    echo "vLLM server stopped."
done
