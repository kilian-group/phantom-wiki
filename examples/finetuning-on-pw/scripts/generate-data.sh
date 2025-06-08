#!/bin/bash
# Script for generating mlcore/phantom-wiki-v1
# HuggingFace: https://huggingface.co/datasets/mlcore/phantom-wiki-v1
# Adapted from data/generate-v1.sh

# check that the correct number of arguments were passed, at least 2
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <output directory> <seed> --flag1 value1 --flag2 value2 ..."
    exit 1
fi

# make directory for output
OUTPUT_DIR=$1
mkdir -p $OUTPUT_DIR
# set seed
SEED=$2

# shift arguments to get flags (script, output directory, seed)
shift 2
cmd_args=$@

echo "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"
echo "Generating data to $OUTPUT_DIR with seed $SEED"
echo "Extra arguments: $cmd_args"
echo "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"
# list of splits
splits=()
SIZE_LIST=(
    50
)
max_tree_size=50
# generate data
for depth in 20
do
    for size in "${SIZE_LIST[@]}"
    do
        od="depth_${depth}_size_${size}_seed_${SEED}"
        cmd="python -m phantom_wiki \
            -od $OUTPUT_DIR/$od \
            --seed $SEED \
            --question-depth $depth \
            --num-family-trees $(($size / $max_tree_size)) \
            --max-family-tree-size $max_tree_size \
            --max-family-tree-depth $depth \
            --article-format json \
            --question-format json \
            $cmd_args"
        echo $cmd
        eval $cmd

        # Append split to list
        splits+=("$od")
    done
done
