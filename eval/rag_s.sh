#!/bin/bash
#SBATCH -J rag-small                              # Job name
#SBATCH -o slurm/rag-small_%j.out                 # output file (%j expands to jobID)
#SBATCH -e slurm/rag-small_%j.err                 # error log file (%j expands to jobID)
#SBATCH -N 1                                 # Total number of nodes requested
#SBATCH -n 8                                 # Total number of cores requested
#SBATCH --get-user-env                       # retrieve the users login environment
#SBATCH --mem=100000                         # server memory (MBs) requested (per node)
#SBATCH -t infinite                           # Time limit (hh:mm:ss)
#SBATCH --gres=gpu:a6000:2                   # Number of GPUs requested
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
# activate conda environment
# source /share/apps/anaconda3/2021.05/etc/profile.d/conda.sh
source /home/jcl354/anaconda3/etc/profile.d/conda.sh
# conda init bash
# NOTE: this assumes that conda environment is called `dataset`
# change this to your conda environment as necessary
conda activate dataset

# list of models
MODELS=(
    # google/gemma-2-2b-it
    meta-llama/llama-3.1-8b-instruct
    # "meta-llama/meta-llama-3.1-8b-instruct-turbo"
    # 'meta-llama/llama-3.2-1b-instruct'
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
    # # Start the vLLM server in the background
    echo "Starting vLLM server..."
    vllm_cmd="nohup vllm serve $model_name --api-key token-abc123 --tensor_parallel_size 2" #nohup launches this in the background
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
        --method rag \
        -od $1 \
        -m $model_name \
        --split_list depth_10_size_26_seed_1 \
        --inf_seed_list $seed_list \
        --inf_temperature $TEMPERATURE"
    echo $cmd
    eval $cmd

    # Stop the vLLM server using pkill
    echo "Stopping vLLM server..."
    pkill -e -f vllm
    echo "vLLM server stopped."
done

# sbatch eval/rag_s.sh /home/jcl354/phantom-wiki/out