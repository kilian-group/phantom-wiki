#!/bin/bash
SPLIT=depth_6_size_26_seed_1 # NOTE: this has 80 instances
# SPLIT=depth_8_size_26_seed_1 # NOTE: this has 140 instances
SEED=1
OUTPUT_DIR=out-test-4

# Get predictions using Together
BATCH_SIZE=10
for bn in {1..8}
do
    python zeroshot.py -bs $BATCH_SIZE -bn $bn -m together:meta-llama/Llama-3.1-8B-Instruct -s $SPLIT --seed $SEED -od $OUTPUT_DIR
    # python zeroshot.py -bs $BATCH_SIZE -bn $bn -m together:meta-llama/Llama-3.1-70B-Instruct -together -s $SPLIT --seed $SEED -od $OUTPUT_DIR
    # python zeroshot.py -bs $BATCH_SIZE -bn $bn -m together:meta-llama/Llama-3.1-405B-Instruct -together -s $SPLIT --seed $SEED -od $OUTPUT_DIR
done

# # Get predictions using vLLM
BATCH_SIZE=80
BATCH_NUMBER=1
python zeroshot.py -bs $BATCH_SIZE -bn $BATCH_NUMBER -m meta-llama/Llama-3.1-8B-Instruct -s $SPLIT --seed $SEED -od $OUTPUT_DIR
# python zeroshot.py -bs $BATCH_NUMBER -bn $BATCH_SIZE -m microsoft/phi-3.5-mini-instruct -s $SPLIT --seed $SEED -od $OUTPUT_DIR
# python zeroshot.py -bs $BATCH_NUMBER -bn $BATCH_SIZE -m google/gemma-2-2b-it -s $SPLIT --seed $SEED -od $OUTPUT_DIR