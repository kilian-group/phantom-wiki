"""Script for evaluating the recall of relevant documents

Example:
```bash
python eval/plot_retriever_ablation.py -od out --method zeroshot
```
"""


import re

# %%
from phantom_eval import get_parser
from phantom_eval.evaluate_utils import get_evaluation_data

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
from_local = args.from_local
# depth = args.depth
# size = args.size
# get evaluation data from the specified output directory and method subdirectory
df = get_evaluation_data(output_dir, method, dataset, from_local)
# # filter by depth and size
# df = df[(df['_depth'] == depth) & (df['_size'] == size)]


# get the retrieved articles
def get_retrieved_article_titles(row):
    """Extract the titles of the retrieved articles from the prompt."""
    prompt = row["interaction"]["messages"][0]["content"][0]["text"]
    # Step 1: get the evidence section use regex matching
    # NOTE: the evidence sections starts with (BEGIN EVIDENCE) and ends with (END EVIDENCE)
    evidence = re.search(r"\(BEGIN EVIDENCE\)(.*)\(END EVIDENCE\)", prompt, re.DOTALL).group(1)
    # Step 2: get the articles by splitting by "\n\n================\n\n"
    articles = evidence.split("\n\n================\n\n")
    # Step 3: Extract the title from each article
    titles = [re.search(r"# (.*)\n\n", article).group(1) for article in articles]
    return titles


df["titles"] = df.apply(get_retrieved_article_titles, axis=1)
df["num_titles"] = df["titles"].apply(len)

# import pdb; pdb.set_trace()

# def get_relevant_articles(row):
#     """Get the relevant articles from the intermediate answer column.

#     We define the "relevant articles" to be the smallest set of articles that
#     can be used to answer the question correctly using base predicates.
#     A predicate is a base predicate if it is stated directly in the article.
#     In our code, we use RELATION_EASY + ATTRIBUTE_TYPES to refer to base predicates.
#     TODO: refactor get_article so that you only need to pass in a list of base predicates.

#     NOTE:
#     - only atoms that are in the first argument of a predicate have corresponding articles,
#     so we only need to consider those atoms when counting relevant articles. (this is not true as both X and
#     Y have articles in father(X,Y) )
#     -

#     New definition: number of unique articles in the intermediate answers
#     """
#     intermediate_answers = row['intermediate_answers']
#     # Step 1: convert the string to a dictionary
#     intermediate_answers = json.loads(intermediate_answers)
#     # Step 2: get the unique number of values in each dictionary
#     solutions = []
#     for intermediate_answer in intermediate_answers:
#         for _, v in intermediate_answer.items():
#             solutions.extend(v)
