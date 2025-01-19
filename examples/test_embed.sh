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
#SBATCH --gres=gpu:a6000:1                   # Number of GPUs requested
#SBATCH --partition=kilian                   # Request partition

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

source /home/jcl354/anaconda3/etc/profile.d/conda.sh
conda activate dataset
eval nohup vllm serve meta-llama/llama-3.2-1b-instruct --api-key token-abc123 --tensor_parallel_size 8 --task embed 
# eval nohup vllm serve meta-llama/llama-3.1-70b-instruct --api-key token-abc123 --tensor_parallel_size 8 --task embed 

SLEEP=60
while ! check_server $model_name $port; do
    echo "Server is not up yet. Checking again in $SLEEP seconds..."
    sleep $SLEEP
done

eval nohup python -m vllm_embed.py

pkill -e -f vllm
