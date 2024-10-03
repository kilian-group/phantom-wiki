# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     custom_cell_magics: kql
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.11.2
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %%
# # !conda install -y conda-build
# # !conda develop .
# # !pip install together

# %%
import random
# from wikidata.relations import relation2phrase
from .grouped_relations import ppl_2_ppl, ppl_2_socialconstructs, ppl_2_objs

# %%
ppl = random.sample(range(1, 100), 10)
socialconstructs = random.sample(range(100, 200), 10)
objs = random.sample(range(200, 300), 10)
all_entities = {"ppl":ppl, "socialconstructs":socialconstructs, "objs":objs}

# %%
article_facts = []
cur_entity = 0
for _ in range(15):
  target_type = random.choice(list(all_entities.keys()))
  target = random.choice(all_entities[target_type])
  
  if target_type == "ppl":
    relation = ppl_2_ppl[random.choice(list(ppl_2_ppl.keys()))]
  if target_type == "socialconstructs":
    relation = ppl_2_socialconstructs[random.choice(list(ppl_2_socialconstructs.keys()))]
  if target_type == "objs":
    relation = ppl_2_objs[random.choice(list(ppl_2_objs.keys()))]

  relation = relation.replace("<subject>", str(cur_entity))
  relation = relation + " " + str(target)
  article_facts.append(relation)

# %%
# print(article_facts)

# %%
prompt = """
Given the following list of facts, generate an article in the style of Wikipedia. The article MUST be consistent with the facts in the list: 
"""

# %%
prompt2 = """
Given the following list of facts, generate an article in the style of Wikipedia. Include the sections "Early life and work", "Legacy" and other appropriate sections. Feel free to make up facts as long as it does not clash with the list of facts below. The article MUST be consistent with the facts in the list:
"""

# %%
# #together.xyz is down rn

# from together import Together

# client = Together()

# completion = client.chat.completions.create(
#   model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
#   messages=[{"role": "user", "content": prompt + str(article_facts)}],
# )

# %%
