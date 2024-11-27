#!/bin/bash
SPLIT=depth_8_size_26_seed_1
# SPLIT=depth_6_size_100_seed_1
# Get predictions using Together
BATCH_SIZE=10
for bn in {1..14}
do
    python zeroshot.py -bs $BATCH_SIZE -bn $bn -m llama-3.1-8b -together -s $SPLIT
    python zeroshot.py -bs $BATCH_SIZE -bn $bn -m llama-3.1-70b -together -s $SPLIT
    python zeroshot.py -bs $BATCH_SIZE -bn $bn -m llama-3.1-405b -together -s $SPLIT
done

# # Get predictions using vLLM
# BATCH_SIZE=80
# BATCH_NUMBER=1
# python zeroshot.py -bs $BATCH_NUMBER -bn $BATCH_SIZE -m meta-llama::Llama-3.1-8B-Instruct
# python zeroshot.py -bs $BATCH_NUMBER -bn $BATCH_SIZE -m microsoft::phi-3.5-mini-instruct
# python zeroshot.py -bs $BATCH_NUMBER -bn $BATCH_SIZE -m google::gemma-2-2b-it