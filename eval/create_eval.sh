#!/bin/bash
# Script to generate slurm script for running evaluation

source eval/constants.sh

#
# Construct job name
#
read -p "Enter the method: " METHOD
# if method is not in the list of methods, exit
if [[ ! " ${METHODS[@]} " =~ " ${METHOD} " ]]; then
    echo "Invalid method. Exiting..."
    exit 1
fi
# if model contains the word rag, prompt the user to enter the retriever method, else set it to the default value
if [[ "$METHOD" =~ "rag" ]]; then
    read -p "Enter the retriever method: " RETRIEVER_METHOD
else
    RETRIEVER_METHOD=""
fi
read -p "Enter the model name or absolute path: " MODEL_NAME_OR_PATH
# Remove the final / if present, and get an alias for the model
MODEL_ALIAS=$(basename ${MODEL_NAME_OR_PATH%/})
JOB_NAME=${METHOD}-${MODEL_ALIAS##*/}

#
# Add option to set the cluster name
#
read -p "Enter cluster name (G2 or Empire or aida): " CLUSTER_NAME
# Add flags:
# - specify GPUs configuration with --gres=${GRES}
# - specify partition with --partition=${PARTITION}
# - specify time with --time=${TIME}
if [[ "$CLUSTER_NAME" =~ ^[Gg]2$ ]]; then
    # Default options
    GPU=a6000
    NUM_GPUS=1
    if [[ " ${LARGE_MODELS[@]} " =~ " ${MODEL_NAME_OR_PATH} " ]]; then
        GPU=a6000
        NUM_GPUS=8
    elif [[ " ${REASONING_MODELS[@]} " =~ " ${MODEL_NAME_OR_PATH} " ]]; then
        GPU=a6000
        NUM_GPUS=4
    elif [[ " ${MEDIUM_MODELS[@]} " =~ " ${MODEL_NAME_OR_PATH} " ]]; then
        GPU=a6000
        NUM_GPUS=1
    elif [[ " ${SMALL_MODELS[@]} " =~ " ${MODEL_NAME_OR_PATH} " ]]; then
        GPU=3090
        NUM_GPUS=1
    else
        echo "Did not recognize model, using default values for GPU=$GPU and NUM_GPUS=$NUM_GPUS"
    fi
    GRES="gpu:${GPU}:${NUM_GPUS}"
    PARTITION=kilian
    TIME=infinite
elif [[ "$CLUSTER_NAME" =~ ^[Ee]mpire$ ]]; then
    NUM_GPUS=1
    if [[ " ${LARGE_MODELS[@]} " =~ " ${MODEL_NAME_OR_PATH} " ]]; then
        NUM_GPUS=4
    elif [[ " ${REASONING_MODELS[@]} " =~ " ${MODEL_NAME_OR_PATH} " ]]; then
        NUM_GPUS=2
    elif [[ " ${MEDIUM_MODELS[@]} " =~ " ${MODEL_NAME_OR_PATH} " ]]; then
        NUM_GPUS=1
    elif [[ " ${SMALL_MODELS[@]} " =~ " ${MODEL_NAME_OR_PATH} " ]]; then
        NUM_GPUS=1
    else
        echo "Did not recognize model, using default value of NUM_GPUS=$NUM_GPUS"
    fi
    GRES="gpu:${NUM_GPUS}"
    PARTITION=cornell
    TIME="1-00:00:00"
elif [[ "$CLUSTER_NAME" =~ aida$ ]]; then
    GPU=a100
    NUM_GPUS=1
    if [[ " ${LARGE_MODELS[@]} " =~ " ${MODEL_NAME_OR_PATH} " ]]; then
        NUM_GPUS=4
    elif [[ " ${REASONING_MODELS[@]} " =~ " ${MODEL_NAME_OR_PATH} " ]]; then
        NUM_GPUS=2
    elif [[ " ${MEDIUM_MODELS[@]} " =~ " ${MODEL_NAME_OR_PATH} " ]]; then
        NUM_GPUS=1
    elif [[ " ${SMALL_MODELS[@]} " =~ " ${MODEL_NAME_OR_PATH} " ]]; then
        NUM_GPUS=1
    else
        echo "Did not recognize model, using default value of GPU=$GPU and NUM_GPUS=$NUM_GPUS"
    fi
    GRES="gpu:${GPU}:${NUM_GPUS}"
    PARTITION=full
    TIME="1-00:00:00"
else
    echo "Invalid cluster name. Exiting..."
    exit 1
fi

#
# Add option to set the number of CPUs and memory
#
read -p "Enter the number of CPUs (default: 8): " CPUS
read -p "Enter the memory in GB (default: 100): " MEMORY
# Set default values if not provided
CPUS=${CPUS:-8}
MEMORY=${MEMORY:-100}

#
# Add option to set if the model is deepseek r1
#
read -p "Is the model DeepSeek R1 (to correctly parse <think> tags and set DeepSeek R1-specific stop tokens)? (y/N): " IS_DEEPSEEK_R1

#
# Generate the slurm script
#
echo "Generating slurm script..."
mkdir -p eval/slurm_scripts
SLURM_OUTPUT_DIR=logs
echo "Creating directory ${SLURM_OUTPUT_DIR}/ to save slurm outputs..."
mkdir -p $SLURM_OUTPUT_DIR

cat << EOT > eval/slurm_scripts/${JOB_NAME}.slurm
#!/bin/bash
#SBATCH -J ${JOB_NAME}                              # Job name
#SBATCH -o ${SLURM_OUTPUT_DIR}/${JOB_NAME}_%j.out                 # output file (%j expands to jobID)
#SBATCH -e ${SLURM_OUTPUT_DIR}/${JOB_NAME}_%j.err                 # error log file (%j expands to jobID)
#SBATCH --mail-type=ALL                      # Request status by email
#SBATCH -N 1                                 # Total number of nodes requested
#SBATCH -n ${CPUS}                                 # Total number of cores requested
#SBATCH --get-user-env                       # retrieve the users login environment
#SBATCH --mem=${MEMORY}GB                         # server memory (MBs) requested (per node)
#SBATCH -t ${TIME}                          # Time limit (hh:mm:ss)
#SBATCH --gres=${GRES}                   # Number of GPUs requested
#SBATCH --partition=${PARTITION}                   # Request partition

source eval/constants.sh

# The first argument is expected to be the output directory
OUTPUT_DIR=\$1
echo "Output directory: \$OUTPUT_DIR"
echo "##################################################"

# Parse the arguments to get extra arguments after the first 2
shift 1
cmd_args=\$@
echo "Extra arguments: \$cmd_args"
echo "##################################################"

# Base command
cmd="python -m phantom_eval \
    --method $METHOD \
    -od \$OUTPUT_DIR \
    --server vllm \
    -m $MODEL_NAME_OR_PATH"

# concatenate the extra arguments to the base command
cmd+=" \$cmd_args"

# check if input contains --split_list if not add the default SPLIT_LIST
if [[ ! "\$@" =~ "--split_list" ]]; then
    cmd+=" --split_list \$SPLIT_LIST"
fi

# if the model is deepseek, add the temperature and top_p and inf_is_deepseek_r1_model flag
if [[ "$IS_DEEPSEEK_R1" =~ ^[Yy]$ ]]; then
    TEMPERATURE=0.6
    TOP_P=0.95
    cmd+=" --inf_temperature \$TEMPERATURE \
           --inf_top_p \$TOP_P \
           --inf_is_deepseek_r1_model"
else
    TEMPERATURE=0
    cmd+=" --inf_temperature \$TEMPERATURE"
fi

cmd+=" --inf_seed_list \$(get_inf_seed_list \$TEMPERATURE)"

# Function to check if the vLLM server is up
check_server() {
    local model_name=\$1
    local port=\$2
    # echo http://0.0.0.0:8001/v1/chat/completions
    response=\$(curl -o /dev/null -s -w "%{http_code}" http://0.0.0.0:\$port/v1/chat/completions \
                    -X POST \
                    -H "Content-Type: application/json" \
                    -H "Authorization: Bearer token-abc123" \
                    -d "{\"model\": \"\$model_name\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello!\"}]}")

    if [ "\$response" -eq 200 ]; then
        return 0
    else
        return 1
    fi
}

spinup_server(){
    # Check for the next available port not in use with vllm
    PORT=8000
    while lsof -Pi :\$PORT -sTCP:LISTEN -t; do
        PORT=\$((PORT + 1))
    done

    cmd+=" \
        --inf_vllm_port \$PORT"
    echo "Using port: \$PORT"

    echo "Starting vLLM server..."
    vllm_cmd="vllm serve $MODEL_NAME_OR_PATH --api-key token-abc123 --tensor_parallel_size $NUM_GPUS --host 0.0.0.0 --port \$PORT" #nohup launches this in the background
    echo \$vllm_cmd
    nohup \$vllm_cmd &

    # Wait for the server to start
    echo "Waiting for vLLM server to start..."
    SLEEP=60
    while ! check_server $MODEL_NAME_OR_PATH \$PORT; do
        echo "Server is not up yet. Checking again in \$SLEEP seconds..."
        sleep \$SLEEP
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
        --retriever_method $RETRIEVER_METHOD"
fi
echo \$cmd
echo "##################################################"
eval \$cmd

# if the method is react or act, we need to stop the vLLM server
if [[ "$METHOD" = act ]] || [[ "$METHOD" = react ]]; then
    # Stop the vLLM server using pkill
    echo "Stopping vLLM server..."
    pkill -e -f vllm
    echo "vLLM server stopped."
fi
EOT

chmod +x eval/slurm_scripts/${JOB_NAME}.slurm

#
# Add option to run the script
#
read -p "Launch the script? (y/N): " LAUNCH

# Add option to run the script
if [[ "$LAUNCH" =~ ^[Yy]$ ]]; then
    echo "Launching the script..."
    read -p "Enter the output directory: " OUTPUT_DIR
    sbatch eval/slurm_scripts/${JOB_NAME}.slurm $OUTPUT_DIR
else
    echo "Slurm script generated. To launch the script, run:"
    echo "sbatch eval/slurm_scripts/${JOB_NAME}.slurm OUTPUT_DIR --flag flag_value"
    echo ""
    echo "To specify environment variables such as DATASET=kilian-group/phantom-wiki-v1, run:"
    echo "sbatch --export=ALL,DATASET='kilian-group/phantom-wiki-v1' eval/slurm_scripts/${JOB_NAME}.slurm OUTPUT_DIR --flag flag_value"
fi
