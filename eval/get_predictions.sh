#!/bin/bash
# Get predictions using Together
BATCH_SIZE=10
for bn in {1..8}
do
    python zeroshot.py -bs $BATCH_SIZE -bn $bn -m llama-3.1-8b -together
    python zeroshot.py -bs $BATCH_SIZE -bn $bn -m llama-3.1-70b -together
    python zeroshot.py -bs $BATCH_SIZE -bn $bn -m llama-3.1-405b -together
done

# # Get predictions using vLLM
# BATCH_SIZE=80
# BATCH_NUMBER=1
# python zeroshot.py -bs $BATCH_NUMBER -bn $BATCH_SIZE -m meta-llama::Llama-3.1-8B-Instruct
# python zeroshot.py -bs $BATCH_NUMBER -bn $BATCH_SIZE -m microsoft::phi-3.5-mini-instruct
# python zeroshot.py -bs $BATCH_NUMBER -bn $BATCH_SIZE -m google::gemma-2-2b-it