"""Script to plot the distribution of number of solutions across splits."""

from datasets import load_dataset
import matplotlib.pyplot as plt
import re

dataset = load_dataset("mlcore/phantom-wiki-v0.3", name='question-answer')
# print the splits
print(dataset)
# make a figure with 30 subplots (10 rows, 3 columns)
fig, axs = plt.subplots(10, 3, figsize=(10, 20))

for split in dataset:
    # get depth, size, seed from split
    match = re.search(r'depth_(\d+)_size_(\d+)_seed_(\d+)', split)
    depth, size, seed = int(match.group(1)), int(match.group(2)), int(match.group(3))
    if size == 25:
        continue
    print(depth, size, seed)
    # plot histogram 
    solutions = [len(a) for a in dataset[split]['answer']]
    row = size // 50 - 1
    col = seed - 1
    print(row, col)
    axs[row, col].hist(solutions, bins=20, alpha=0.5, label=split, density=True)
    # axs[row, col].set_ylim(0, 100)  # Set the same y-axis limit for all subplots
    # add title to subplot
    axs[row, col].set_title(f"Depth {depth}, Size {size}, Seed {seed}")
    # set xlim to [0, 20]
    # axs[row, col].set_xlim(0, 20)

fig.text(0.5, 0.0, 'Solutions', ha='center')
fig.text(0.0, 0.5, 'Number of Questions', va='center', rotation='vertical')
fig.suptitle('Distribution of Solution Count in the Dataset')
# fig.legend()
# use tight layout
fig.tight_layout(rect=[0, 0.03, 1, 0.95])
save_path = 'solutions_distribution.png'
print(f"Saving figure to {save_path}")
fig.savefig(save_path)