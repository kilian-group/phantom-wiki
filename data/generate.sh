#!/bin/bash

# check that the correct number of arguments were passed
if [ -z "$1" ]; then
    echo "Usage: $0 <output directory>"
    exit 1
fi

# make directory for output
mkdir -p $1

# generate data
for seed in 1 2 3 4 5
do
    for depth in 10 20 30 40 50
    do
        for size in 26 50 100 200 500 1000
        do
            od="$1/depth_${depth}_size_${size}_seed_${seed}"
            cmd="python -m phantom_wiki \
                -od $od \
                -s $seed \
                --depth $depth \
                --max-tree-size $size \
                --article-format json \
                --question-format json \
                --valid-only"
            echo $cmd
            eval $cmd
        done
    done
done