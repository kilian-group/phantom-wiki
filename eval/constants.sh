#!/bin/bash

# TODO add get_inf_seed_list function that takes in temperature and returns inf_seed_list

# TODO add L models
# TODO add M models
# TODO add S models
# TODO add CPU models

# Define SPLIT_LIST for dataset v0.3
for seed in 1 2 3
do
    for size in 50 100 200 300 400 500
    do
        SPLIT_LIST+="depth_10_size_${size}_seed_${seed} "
    done
done
