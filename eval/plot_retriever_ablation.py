"""Script for evaluating the recall of relevant documents 

Example:
```bash
python eval/plot_retriever_ablation.py -od out --method zeroshot
```
"""


# %%
import os
from phantom_eval import get_parser
from phantom_eval.evaluate_utils import get_evaluation_data, COLORS, LINESTYLES, pivot_mean_std, mean, std
import matplotlib.pyplot as plt
import re

parser = get_parser()
# parser.add_argument(
#     '--depth', 
#     type=int, 
#     default=20, 
#     help='Depth to plot accuracies for'
# )
# parser.add_argument(
#     '--size',
#     type=int,
#     default=50,
#     help='Size to plot accuracies for'
# )
args = parser.parse_args()
output_dir = args.output_dir
method = args.method
dataset = args.dataset
# depth = args.depth
# size = args.size
# get evaluation data from the specified output directory and method subdirectory
df = get_evaluation_data(output_dir, method, dataset)
# # filter by depth and size
# df = df[(df['_depth'] == depth) & (df['_size'] == size)]

# get the retrieved articles
def get_retrieved_article_titles(row):
    """Extrac the titles of the retrieved articles from the prompt.
    """
    prompt = row['interaction']['messages'][0]['content'][0]['text']
    # Step 1: get the evidence section use regex matching
    # NOTE: the evidence sections starts with (BEGIN EVIDENCE) and ends with (END EVIDENCE)
    evidence = re.search(r'\(BEGIN EVIDENCE\)(.*)\(END EVIDENCE\)', prompt, re.DOTALL).group(1)
    # Step 2: get the articles by splitting by "\n\n================\n\n"
    articles = evidence.split('\n\n================\n\n')
    # Step 3: Extract the title from each article
    titles = [re.search(r'# (.*)\n\n', article).group(1) for article in articles]
    return titles
df['titles'] = df.apply(get_retrieved_article_titles, axis=1)
df['num_titles'] = df['titles'].apply(len)
import pdb; pdb.set_trace()