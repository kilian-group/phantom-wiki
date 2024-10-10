# -*- coding: utf-8 -*-
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
#     display_name: arxiv_kernel
#     language: python
#     name: arxiv_kernel
# ---

# %%
# # !conda install -y conda-build
# # !conda develop .
# # !pip install together

# %%
import random
# from wikidata.relations import relation2phrase
from grouped_relations import ppl_2_ppl, ppl_2_socialconstructs, ppl_2_objs

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
print(article_facts)

# %%
prompt = """
Given the following list of facts, generate an article in the style of Wikipedia. The article MUST be consistent with the facts in the list: 
"""

# %%
prompt2 = """
Given the following list of facts, generate an article in the style of Wikipedia. Include the sections "Early life and work", "Legacy" and other appropriate sections. Feel free to make up facts as long as it does not clash with the list of facts below. The article MUST be consistent with the facts in the list:
"""

# %%
from API_KEY import TOGETHER_API_KEY

# %%
# # !pip install together

# %%
#together.xyz is blocked by cornell firewall
#https://docs.together.ai/docs/quickstart

from together import Together

client = Together(api_key=TOGETHER_API_KEY)

# %%
response = client.chat.completions.create(
  model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
  messages=[{"role": "user", "content": prompt + str(article_facts)},
            {"role": "assistant", "content":prompt + str(article_facts)}],
  temperature=0.7,
  top_p=0.7,
  top_k=50,
  repetition_penalty=1,
  stop=["<|eot_id|>"],
  truncate=7680,
  max_tokens=512,
  stream=True,
)

# %%
for chunk in response:
  print(chunk.choices[0].delta.content or "", end="", flush=True)

# %%
"""
what I get in this response is different from the UI. The UI is:
Given the following list of facts, generate an article in the style of Wikipedia. The article MUST be consistent with the facts in the list: 
["0's siblings are 36", 'The eye color of 0 is 211', 'The religion which 0 is associated with is 176', "0's spouse is 70", 'The city in which 0 was born is 116', "0's sexual orientation is 253", "0's gender is 298", 'The mother tongue of 0 is 203', 'The mother tongue of 0 is 253', 'The city in which 0 died is 156', 'The uncle of 0 is 22', 'The country which 0 is associated with is 164', 'The child of 0 is 36', 'The date in which 0 was born in is 253', 'The mother of 0 is 70']
Article: 0

0 is a notable individual with a unique set of characteristics and associations. Born in 116, 0 has had a life marked by various connections and affiliations.

Early Life and Family

0 was born in the city of 116, and is the child of 70. The mother tongue of 0 is 203, and it is also reported that 0's mother tongue is 253. This suggests that 0 may have been raised speaking multiple languages from a young age.

Personal Life

0 is married to 70, and has one child, 36. The relationship between 0 and 70 is not publicly disclosed, but it is known that 0's spouse is 70. Additionally, 0's gender is 298, indicating a non-binary or genderqueer identity.

Religious Affiliations

0 is associated with the religion of 176, which is not a widely recognized or established faith. It is unclear what specific beliefs or practices are associated with this religion, but it is known that 0 is affiliated with it.

Uncle and Country of Association

0's uncle is 22, and 0 is also associated with the country of 164. This country is not a well-known or widely recognized nation, and it is unclear what specific connection 0 has to it.

Death and Legacy

0 passed away in the city of 156, although the exact date of death is not publicly known. 0's life and legacy are not well-documented, but it is clear that 0 had a complex and multifaceted existence.

Physical Characteristics

0's eye color is 211, which is an unusual and distinctive shade. It is unclear what other physical characteristics 0 may have had, as there is limited information available about their physical appearance.

Sexual Orientation

0's sexual orientation is 253, which is not a widely recognized or accepted orientation. It is unclear what this means for 0's personal life and relationships, but it is clear that 0's sexual orientation is not aligned with traditional binary norms.
"""

# %%
"""
whereas with the API I get

However, I must point out that the given list of facts appears to be inconsistent and nonsensical. Many of the facts seem to be unrelated to the typical information found in a Wikipedia article about a person, and some of the values appear to be numbers rather than words or phrases.

Assuming that the list is intended to be interpreted in a more abstract or metaphorical sense, I will attempt to generate an article in the style of Wikipedia. However, please note that the resulting article may not be entirely coherent or meaningful.

Zero
================

Zero is a unique individual with a complex and multifaceted identity. The sister of Zero is Fifty-six, a person with whom Zero shares a close bond.

Birth and Death
-------------

Zero was born in the year 232, an event that marked the beginning of a long and storied life. Unfortunately, Zero's life was cut short in the city of 132, where they ultimately passed away.

Family
------

Zero's family is a diverse and interesting one. Their mother tongue is 226, a language that reflects their unique cultural heritage. Zero's uncle, 83, played an important role in their upbringing, while their other uncle, 6, also had a significant impact on their life.

Zero's relationships with others are also noteworthy. They have a number of siblings, including Fifty-six, and have been in a number of romantic relationships throughout their life. Their sexual orientation is complex and multifaceted, with various sources indicating that they are attracted to both 240 and 262. Zero's gender identity is 257, a unique and non-binary expression.

Occupation and Legacy
---------------------
...
Zero's occupation is 109, a profession that reflects their creative and innovative spirit. They have also had 67 children, a testament to their fertility and reproductive abilities.

In terms of their personal relationships, Zero's stepmother is 26, a woman who played an important role in their life. Zero's relationships with others are also marked by a sense of following, with 67 being a significant figure in their life.

"""

# %%
"""
note that the UI tab of the API is:

import os
from together import Together

client = Together(api_key=os.environ.get('TOGETHER_API_KEY'))

response = client.chat.completions.create(
    model="meta-llama/Meta-Llama-3-8B-Instruct-Lite",
    messages=[
        {
                "role": "user",
                "content": "Given the following list of facts, generate an article in the style of Wikipedia. The article MUST be consistent with the facts in the list: \n[\"0‛s siblings are 36\", ‛The eye color of 0 is 211‛, ‛The religion which 0 is associated with is 176‛, \"0‛s spouse is 70\", ‛The city in which 0 was born is 116‛, \"0‛s sexual orientation is 253\", \"0‛s gender is 298\", ‛The mother tongue of 0 is 203‛, ‛The mother tongue of 0 is 253‛, ‛The city in which 0 died is 156‛, ‛The uncle of 0 is 22‛, ‛The country which 0 is associated with is 164‛, ‛The child of 0 is 36‛, ‛The date in which 0 was born in is 253‛, ‛The mother of 0 is 70‛]\n"
        },
        {
                "role": "assistant",
                "content": "**Article: 0**\n\n0 is a notable individual with a unique set of characteristics and associations. Born in 116, 0 has had a life marked by various connections and affiliations.\n\n**Early Life and Family**\n\n0 was born in the city of 116, and is the child of 70. The mother tongue of 0 is 203, and it is also reported that 0‛s mother tongue is 253. This suggests that 0 may have been raised speaking multiple languages from a young age.\n\n**Personal Life**\n\n0 is married to 70, and has one child, 36. The relationship between 0 and 70 is not publicly disclosed, but it is known that 0‛s spouse is 70. Additionally, 0‛s gender is 298, indicating a non-binary or genderqueer identity.\n\n**Religious Affiliations**\n\n0 is associated with the religion of 176, which is not a widely recognized or established faith. It is unclear what specific beliefs or practices are associated with this religion, but it is known that 0 is affiliated with it.\n\n**Uncle and Country of Association**\n\n0‛s uncle is 22, and 0 is also associated with the country of 164. This country is not a well-known or widely recognized nation, and it is unclear what specific connection 0 has to it.\n\n**Death and Legacy**\n\n0 passed away in the city of 156, although the exact date of death is not publicly known. 0‛s life and legacy are not well-documented, but it is clear that 0 had a complex and multifaceted existence.\n\n**Physical Characteristics**\n\n0‛s eye color is 211, which is an unusual and distinctive shade. It is unclear what other physical characteristics 0 may have had, as there is limited information available about their physical appearance.\n\n**Sexual Orientation**\n\n0‛s sexual orientation is 253, which is not a widely recognized or accepted orientation. It is unclear what this means for 0‛s personal life and relationships, but it is clear that 0‛s sexual orientation is not aligned with traditional binary norms."
        }
],
    max_tokens=512,
    temperature=0.7,
    top_p=0.7,
    top_k=50,
    repetition_penalty=1,
    stop=["<|eot_id|>"],
    truncate=7680,
    stream=True
)
print(response.choices[0].message.content)
"""

# %%
# also note that the API can't be run on school wifi, needs to be hotspotted
