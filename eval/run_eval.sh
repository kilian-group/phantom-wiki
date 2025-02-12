#!/bin/bash
#SBATCH -J method-size                              # Job name
#SBATCH -o slurm/method-size_%j.out                 # output file (%j expands to jobID)
#SBATCH -e slurm/method-size_%j.err                 # error log file (%j expands to jobID)
#SBATCH --mail-type=ALL                      # Request status by email 
#SBATCH --mail-user=xxx@cornell.edu          # Email address to send results to.
#SBATCH -N 1                                 # Total number of nodes requested
#SBATCH -n n                                 # Total number of cores requested
#SBATCH --get-user-env                       # retrieve the users login environment
#SBATCH --mem=100000                         # server memory (MBs) requested (per node)
#SBATCH -t infinite                          # Time limit (hh:mm:ss)
#SBATCH --gres=gpu:a6000:n                   # Number of GPUs requested
#SBATCH --partition=kilian                   # Request partition

# Script for running zero-shot evaluation on all small models (<4 B params)
# GPU requirements when using max context length (i.e., `max_model_len=None`)
# Model Size    | 3090 GPU   | A6000 GPU | H100 GPU
# ------------- | -----------|-----------|---------
# ~4B models    | 1          | 1         | 1
# ~8B models    | 2          | 1         | 1
# ~70B models   |            | 8         | 4

#!/bin/bash

# Check if the number of arguments is less than 4 (excluding the script name)
if [ "$#" -lt 4 ]; then
    echo "Usage: $0 <output_dir> <method> <model_name> <split>"
    exit 1
fi

OUTPUT_DIR=$1
METHOD=$2
MODEL_NAME=$3
SPLIT=$4

# Print values (for debugging or confirmation)
echo "Running eval with $0: \
    Output Directory: $OUTPUT_DIR \
    Method: $METHOD \
    Model Name: $MODEL_NAME \
    Split: $SPLIT"

source eval/constants.sh
# activate conda environment
# source /share/apps/anaconda3/2021.05/etc/profile.d/conda.sh
# conda init bash
# NOTE: this assumes that conda environment is called `dataset`
# change this to your conda environment as necessary
# conda activate dataset

# Base command
cmd="python -m phantom_eval \
    --method $METHOD \
    -od $OUTPUT_DIR \
    -m $MODEL_NAME \
    --split_list $SPLIT"

# fix some parameters if using reasoning method
if [ "${METHOD}" == "reasoning" ]; then
    TEMPERATURE=0.6
    TOP_P=0.95
    if [ "$MODEL_NAME" != "deepseek-ai/deepseek-r1-distill-qwen-32b" ]; then   
        echo "Reasoning method only available for 'deepseek-ai/deepseek-r1-distill-qwen-32b'"
        exit 1
    fi
    cmd+=" \
        --inf_temperature $TEMPERATURE \
        --inf_top_p $TOP_P"

else
    TEMPERATURE=0
    cmd+=" \
    --inf_temperature $TEMPERATURE"
fi


# If not using API, need to start vLLM server 
if [[ ! " ${API_MODELS[@]} " =~ " ${model} " ]]; then
do
    # Get the number of gpus by counting the number of lines in the output of nvidia-smi
    NUM_GPUS=$(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l)
    echo "Number of GPUs: $NUM_GPUS"

    # Check for the next available port not in use with vllm
    PORT=8000
    while lsof -Pi :$PORT -sTCP:LISTEN -t; do
        PORT=$((PORT + 1))
    done

    cmd+=" \
        --inf_vllm_port $PORT"

    echo "Using port: $PORT"
    echo "Starting vLLM server..."
    vllm_cmd="vllm serve $model --api-key token-abc123 --tensor_parallel_size $NUM_GPUS --host 0.0.0.0 --port $PORT" #nohup launches this in the background
    echo $vllm_cmd
    nohup $vllm_cmd &
    
    # Wait for the server to start
    echo "Waiting for vLLM server to start..."
    SLEEP=60
    while ! check_server $model $PORT; do
        echo "Server is not up yet. Checking again in $SLEEP seconds..."
        sleep $SLEEP
    done

    echo "vLLM server is up and running."

if [[ "$method" =~ "rag" ]]; then
    cmd+=" \
        --retriever_method whereisai/uae-large-v1"
fi
echo $cmd
eval $cmd


if [[ ! " ${API_MODELS[@]} " =~ " ${model} " ]]; then
    # Stop the vLLM server using pkill
    echo "Stopping vLLM server..."
    pkill -e -f vllm
    echo "vLLM server stopped."
fi
