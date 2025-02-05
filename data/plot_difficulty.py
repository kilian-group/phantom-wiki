"""Script to plot the distribution of reasoning steps across splits."""

from phantom_eval.utils import load_data
from phantom_eval import plotting_utils
import matplotlib.pyplot as plt

SIZES = [
    50, 
    # 500, 
    # 5000
]
fig, axs = plt.subplots(len(SIZES), 1, figsize=(3.25, 2.5))

bins = range(1, 21)
for depth in [10, 20]:
    for size in SIZES:
        difficulty = []
        for seed in [1,2,3]:
            print(depth, size, seed)
            split = f"depth_{depth}_size_{size}_seed_{seed}"
            dataset = load_data("mlcore/phantom-wiki-v050", split)
            # plot histogram 
            difficulty.extend(dataset['qa_pairs']['difficulty'])
        # import pdb; pdb.set_trace()
        row = SIZES.index(size)    
        axs.hist(difficulty, bins=bins, alpha=0.25, label=f"$\\text{{Depth}}={depth}$", density=True)
        # axs.set_ylim(0, 1)  # Set the same y-axis limit for all subplots
        # add title to subplot
        # axs.set_title(f"Size {size}")
        # set xlim to [0, 20]

axs.legend(loc='upper right', fontsize=plotting_utils.LEGEND_FONT_SIZE)
axs.spines['left'].set_position(('outward', 1))    # Move y-axis outward
axs.spines['bottom'].set_position(('outward', 1))  # Move x-axis outward
axs.spines['right'].set_visible(False)
axs.spines['top'].set_visible(False)

# format x-axis
axs.set_xlim(min(bins), max(bins))
axs.set_xticks(bins[::5])
axs.set_xticklabels(bins[::5], fontsize=plotting_utils.TICK_FONT_SIZE)
# set x-axis label
axs.set_xlabel('Reasoning steps', fontsize=plotting_utils.LABEL_FONT_SIZE)
# format y-axis (font size)
axs.set_yticklabels(axs.get_yticks(), fontsize=plotting_utils.TICK_FONT_SIZE)

# use tight layout
fig.tight_layout()
fig.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.2)

save_path = 'difficulty.pdf'
print(f"Saving figure to {save_path}")
fig.savefig(save_path)
