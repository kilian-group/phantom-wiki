#!/usr/bin/env bash
#SBATCH -J selfask                              # Job name
#SBATCH -o slurm/selfask_%j.out                 # output file (%j expands to jobID)
#SBATCH -e slurm/selfask_%j.err                 # output file (%j expands to jobID)
#SBATCH --mail-type=ALL                      # Request status by email
#SBATCH -N 1                                 # Total number of nodes requested
#SBATCH -n 8                                 # Total number of cores requested
#SBATCH --get-user-env                       # retrieve the users login environment
#SBATCH --mem=100GB                         # server memory (MBs) requested (per node)
#SBATCH -t 2-00:00:00                          # Time limit (hh:mm:ss)
#SBATCH --gres=gpu:a100:4                   # Number of GPUs requested
#SBATCH --partition=full                   # Request partition

# The first argument is the seed
if [ -z "$1" ]; then
    echo "Usage: $0 <seed>"
    exit 1
fi
seed=$1

# Anmol's script to evaluate selfask on PhantomWiki datasets with specified seed,
# adapted from Chao's instructions.

cd $HOME/work/phantom-wiki-copy

size=50
echo "Processing size $size with seed $seed"

# Save the dataset as JSONL for the specified size and seed
cd $HOME/work/phantom-wiki-copy/examples/flashrag/
python save_as_jsonl.py \
    --dataset kilian-group/phantom-wiki-v1 \
    --split_list depth_20_size_${size}_seed_${seed}

cd $HOME/work/FlashRAG
python -m flashrag.retriever.index_builder \
    --retrieval_method bm25 \
    --corpus_path $HOME/work/phantom-wiki-copy/examples/flashrag/indexes/depth_20_size_${size}_seed_${seed}.jsonl \
    --bm25_backend bm25s \
    --save_dir $HOME/work/phantom-wiki-copy/examples/flashrag/indexes/depth_20_size_${size}_seed_${seed}

cd $HOME/work/phantom-wiki-copy/examples/flashrag/
python run_selfask.py \
    --split depth_20_size_${size}_seed_${seed} \
    --model_name "meta-llama/Llama-3.1-8B-Instruct" \
    --output_dir "selfask_output"
