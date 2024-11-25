#!/bin/bash
# This script is used to get predictions for multiple batches
MODEL=llama-3.1-405b
BATCH_SIZE=10
# the train split has a total of 80 samples
for bn in {1..8}
do
    python zeroshot.py -bs $BATCH_SIZE -bn $bn -m $MODEL
done