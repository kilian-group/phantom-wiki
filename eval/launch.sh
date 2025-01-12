#!/bin/bash

conda activate dataset

# check that two arguments were passed
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <output directory> <email>"
    exit 1
fi

# On empire:
# sbatch --gres=gpu:1 --partition=cornell -t 1-00:00:00 --mail-user=$2 eval/zeroshot_S.sh $1
# sbatch --gres=gpu:1 --partition=cornell -t 1-00:00:00 --mail-user=$2 eval/fewshot_S.sh $1
# sbatch --gres=gpu:1 --partition=cornell -t 1-00:00:00 --mail-user=$2 eval/cot_S.sh $1
# sbatch --gres=gpu:1 --partition=cornell -t 1-00:00:00 --mail-user=$2 eval/zeroshot-sc_S.sh $1
# sbatch --gres=gpu:1 --partition=cornell -t 1-00:00:00 --mail-user=$2 eval/fewshot-sc_S.sh $1
# sbatch --gres=gpu:1 --partition=cornell -t 1-00:00:00 --mail-user=$2 eval/cot-sc_S.sh $1

# sbatch --gres=gpu:1 --partition=cornell -t 1-00:00:00 --mail-user=$2 eval/zeroshot_M.sh $1
# sbatch --gres=gpu:1 --partition=cornell -t 1-00:00:00 --mail-user=$2 eval/fewshot_M.sh $1
# sbatch --gres=gpu:1 --partition=cornell -t 1-00:00:00 --mail-user=$2 eval/cot_M.sh $1
# sbatch --gres=gpu:1 --partition=cornell -t 1-00:00:00 --mail-user=$2 eval/zeroshot-sc_M.sh $1
# sbatch --gres=gpu:1 --partition=cornell -t 1-00:00:00 --mail-user=$2 eval/fewshot-sc_M.sh $1
# sbatch --gres=gpu:1 --partition=cornell -t 1-00:00:00 --mail-user=$2 eval/cot-sc_M.sh $1

# sbatch --gres=gpu:4 --partition=cornell -t 1-00:00:00 --mail-user=$2 eval/zeroshot_L.sh $1
# sbatch --gres=gpu:4 --partition=cornell -t 1-00:00:00 --mail-user=$2 eval/fewshot_L.sh $1
# sbatch --gres=gpu:4 --partition=cornell -t 1-00:00:00 --mail-user=$2 eval/cot_L.sh $1
sbatch --gres=gpu:4 --partition=cornell -t 1-00:00:00 --mail-user=$2 eval/react_L.sh $1
sbatch --gres=gpu:4 --partition=cornell -t 1-00:00:00 --mail-user=$2 eval/act_L.sh $1