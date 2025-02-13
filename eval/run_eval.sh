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
if [ "$#" -lt 3 ]; then
    echo "Usage: eval/run_eval.sh <output_dir> <method> <model_name> --flag flag_value"
    exit 1
fi

# Parse the arguments to get extra arguments after the first 4
shift 3
cmd_args=$@

OUTPUT_DIR=$1
METHOD=$2
MODEL_NAME=$3

source eval/constants.sh

# Base command
cmd="python -m phantom_eval \
    --method $METHOD \
    -od $OUTPUT_DIR \
    -m $MODEL_NAME"

# concatenate the extra arguments to the base command
cmd+=" $cmd_args"

# check if input contains --split_list if not add the default SPLIT_LIST
if [[ ! "$@" =~ "--split_list" ]]; then
    cmd+=" --split_list $SPLIT_LIST"
fi

# if the model is deepseek, add the temperature and top_p
if [ "${MODEL_NAME}" =~ "deepseek" ]; then
    TEMPERATURE=0.6
    TOP_P=0.95
    cmd+=" --inf_temperature $TEMPERATURE \
           --inf_top_p $TOP_P"

else
    TEMPERATURE=0
    cmd+=" --inf_temperature $TEMPERATURE"
fi

cmd+=" --inf_seed_list $(get_inf_seed_list $TEMPERATURE)"

# Function to check if the vLLM server is up
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

spinup_server(){
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
    vllm_cmd="vllm serve $MODEL_NAME --api-key token-abc123 --tensor_parallel_size $NUM_GPUS --host 0.0.0.0 --port $PORT" #nohup launches this in the background
    echo $vllm_cmd
    nohup $vllm_cmd &

    # Wait for the server to start
    echo "Waiting for vLLM server to start..."
    SLEEP=60
    while ! check_server $MODEL_NAME $PORT; do
        echo "Server is not up yet. Checking again in $SLEEP seconds..."
        sleep $SLEEP
    done

    echo "vLLM server is up and running."
}

# If the method is react or act, we need to start vLLM server
if [[ "$METHOD" = act ]] || [[ "$METHOD" = react ]]; then
    # print the method
    echo "Method: $METHOD"
    spinup_server
fi

if [[ "$METHOD" =~ "rag" ]]; then
    cmd+=" \
        --retriever_method whereisai/uae-large-v1"
fi
echo $cmd
eval $cmd

# if the method is react or act, we need to stop the vLLM server
if [[ "$METHOD" = act ]] || [[ "$METHOD" = react ]]; then
    # Stop the vLLM server using pkill
    echo "Stopping vLLM server..."
    pkill -e -f vllm
    echo "vLLM server stopped."
fi
