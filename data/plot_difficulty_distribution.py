"""Script to plot the distribution of reasoning steps across splits."""

from datasets import load_dataset
import matplotlib.pyplot as plt
import re

dataset = load_dataset("mlcore/phantom-wiki-v0.5", name='question-answer')
# print the splits
print(dataset)
# make a figure with 30 subplots (10 rows, 3 columns)
SIZES = [50, 500, 5000]
fig, axs = plt.subplots(3, len(SIZES), figsize=(6.75, 6))

for split in dataset:
    # get depth, size, seed from split
    match = re.search(r'depth_(\d+)_size_(\d+)_seed_(\d+)', split)
    depth, size, seed = int(match.group(1)), int(match.group(2)), int(match.group(3))
    if size not in SIZES:
        continue
    print(depth, size, seed)
    # plot histogram 
    difficulty = dataset[split]['difficulty']
    row = seed - 1
    col = SIZES.index(size)
    print(row, col)
    axs[row, col].hist(difficulty, bins=20, alpha=0.25, label=split)
    axs[row, col].set_ylim(0, 100)  # Set the same y-axis limit for all subplots
    if row == 0:
        # add title to subplot
        axs[row, col].set_title(f"Size {size}")
    # set xlim to [0, 20]
    axs[row, col].set_xlim(0, 20)

fig.text(0.5, 0.0, 'Reasoning steps', ha='center')
fig.text(0.0, 0.5, 'Number of questions', va='center', rotation='vertical')
fig.suptitle('Distribution of reasoning steps in the dataset')
# fig.legend()
# use tight layout
# fig.tight_layout(rect=[0, 0.03, 1, 0.95])
save_path = 'difficulty_distribution.png'
print(f"Saving figure to {save_path}")
fig.savefig(save_path)
