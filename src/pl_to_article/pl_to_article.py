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
#     display_name: dataset
#     language: python
#     name: python3
# ---

# %%
import os
import argparse
from faker import Faker
import textwrap

# %%
from CFG_utils import * 

# %%
def get_arguments():
    parser = argparse.ArgumentParser(description="Generate articles from Prolog files")
    parser.add_argument("--pl_file", type=str, default='../../tests/family_tree.pl', help="Path to the Prolog file")
    parser.add_argument("--skip_cfg", '-sc', action="store_true",
                    help="Skip CFG generation")
    parser.add_argument("--cfg_dir", '-cd', type=str, default=None,
                    help="Path to the CFG directory if not generating new CFGs")
    parser.add_argument("--output_folder", type=str, default= 'output', help="Path to the output folder")
    parser.add_argument("--rules", type=list, default=['../../tests/base_rules.pl', '../../tests/derived_rules.pl'], help="list of Path to the rules file")
    args, _ =  parser.parse_known_args() # this is useful when running the script from a notebook so that we use the default values
    return args

# %%
import re
import janus_swi as janus
from grouped_relations import ppl_2_ppl
# , ppl_2_socialconstructs, ppl_2_objs, things

# %%
def consult(predicate_path, rule_paths):
    print(f"loading predicates from {predicate_path}")
    janus.query_once(f"consult(X)", {'X': predicate_path})
    for rule_path in rule_paths:
        print(f"loading rules from {rule_path}")
        janus.query_once("consult(X)", {'X': rule_path})

# %%
def parse(line):
    """
    parses a Prolog predicate
    Examples:
        female(vanessa). -> ('female', ['vanessa', 'albert'])
        parent(anastasia, sarah). -> ('parent', ['anastasia', 'sarah'])
        
    Args:
        line (str): predicate(arg1, arg2, ..., argn).
    Returns:
        (predicate, [arg1, arg2, ..., argn])
    """
    pattern = r"^([a-z]+)\((.*)\)\.$"
    match = re.search(pattern, line)
    return match.group(1), match.group(2).split(", ")

# %%
def get_family_article(name):
    """
    Get the following relations for a given name:
    - mother
    - father
    - siblings
    - children
    - wife/husband 

    Assumes that the prolog files are loaded and the predicates are defined in the prolog files.
    This can be done using the following code:
    ```
    janus.query_once("consult('../../tests/family_tree.pl')")
    janus.query_once("consult('./family/rules.pl')")
    ```

    Ref: https://www.swi-prolog.org/pldoc/man?section=janus-call-prolog
    """
    # name = 'elias'
    relations = {}
    # get mother
    if mother := janus.query_once("mother(X, Y)", {'Y': name})['X']:
        relations['mother'] = mother
    # print(mother)
    # get father
    if father := janus.query_once("father(X, Y)", {'Y': name})['X']:
        relations['father'] = father
    # print(father)
    # get siblings
    if siblings := [sibling['X'] for sibling in janus.query("sibling(X, Y)", {'Y': name})]:
        relations['sibling'] = ', '.join(siblings)
    # print(list(siblings))
    # get children
    if children := [child['X'] for child in list(janus.query("child(X, Y)", {'Y': name}))]:
        relations['child'] = ', '.join(children)
        relations['number of children'] = len(children)
    # print(list(children))
    
    # TODO: get wife and husband
    if spouse := (janus.query_once(f"husband(X, Y)", {'X': name}) or janus.query_once(f"wife(X, Y)", {'X': name}))['Y']:
        relations['spouse'] = spouse

    facts = []
    for relation, target in relations.items():
        relation_template = ppl_2_ppl[relation]
        fact = relation_template.replace("<subject>", name) + " " + str(target) + "."
        facts.append(fact)

    article = "\n".join(facts)
    return article

# %%
# if __name__ == "__main__":
# get arguments
args = get_arguments()
print(args)
# set seed
Faker.seed(0)
fake = Faker()
#make directories
family_folder = os.path.join(args.output_folder, 'family')
bio_folder = os.path.join(args.output_folder, 'bio')
CFG_folder = os.path.join(args.output_folder, 'CFG')
article_folder = os.path.join(args.output_folder, 'article')
# TODO want to put prologs and DLVs also in the same folder
os.makedirs(family_folder, exist_ok=True)
os.makedirs(CFG_folder, exist_ok=True)
os.makedirs(bio_folder, exist_ok=True)
os.makedirs(article_folder, exist_ok=True)
# load the prolog file
consult(args.pl_file, args.rules)


# %%
# get names from the prolog file
person_list = []
with open(args.pl_file, "r") as f:
    lines = f.readlines()
    for line in lines:
        if line.startswith("female") or line.startswith("male"):
            person = match_name(line)
            person_list.append(person)
        else:
            print('skip line')
            continue

# %%
family_list = []
for person in person_list:
    # get the family article
    family = get_family_article(person)
    # write the family to a file
    family_file = os.path.join(family_folder, f"{person}_family.txt")
    print(f"writing family for {person} to {family_file}")
    with open(family_file, "w") as file:
        file.write(family)
    
    family_list.append(family)

# %%
bio_list = []
cfg_list = []
for person in person_list:
    # get the job article
    job = fake.job()
    print(f"{person} is a {job}")
    # allow multiple tries and only write to file if a bio is successfully generated
    if args.skip_cfg:
        bio, cfg = generate_article_with_retries(None, None, CFG_file=os.path.join(args.cfg_dir, f"{person}_CFG.txt"), max_attempts=10)
    else:
        bio, cfg = generate_article_with_retries(person, job, CFG_file=None, max_attempts=10)

    # write the CFG to a file
    CFG_file = os.path.join(CFG_folder, f"{person}_CFG.txt")
    print(f"writting CFG for {person} to {person}_CFG.txt")
    with open(CFG_file, "w") as file:
        file.write(cfg)

    # write to file
    bio_file = os.path.join(bio_folder, f"{person}_bio.txt")
    print(f"writting bio for {person} to {person}_bio.txt")
    write_bio(bio, bio_file)

    bio_list.append(bio)
    cfg_list.append(cfg)

# %% [markdown]
# pass both articles to Llama
# %%
from together import Together
client = Together()

# %%
prompt = """
Using the following list of facts, please create a detailed and wordy Wikipedia-like article about the subject. The article should include sections like "Introduction," "Early Life," "Education," "Career," "Notable Works," "Personal Life," and others as appropriate. Elaborate on each point by adding relevant background, context, or general information where appropriate. Maintain a formal and encyclopedic tone, but aim for a more expansive narrative without altering or contradicting the list of facts.

### Example List of Facts:

- Joseph Klienberg is the composer of Beyond the Horizon (Mosaic).
- The mother of Joseph Klienberg is Noah Davis.
- The number of children Joseph Klienberg has is Aiden Jones.
- Joseph Klienberg's spouse is Sophia Davis.
- Joseph Klienberg attended the University of Fine Arts in Paris.
- He won the National Art Award in 2015.
- His style is often described as a fusion of classical and modern influences.

### Instructions:
1. **Introduction**: Begin the article by introducing the subject with a detailed summary. Include not only the subject’s profession and major accomplishments but also background information about their significance in their field. You may elaborate on the importance of their work (e.g., the impact of *Beyond the Horizon* and its style).

2. **Early Life**: Discuss the subject’s birth, family background, and childhood in more depth. Provide elaborative details, such as potential cultural, geographic, or familial influences. For example, explore how growing up with Noah Davis as his mother might have influenced his early development.

3. **Education**: When describing the subject’s education, delve into details about the University of Fine Arts in Paris, its significance, and how it may have shaped his career. Include any historical or general context about the institution that may be relevant to the subject's growth as an artist.

4. **Career**: Provide an in-depth narrative of the subject’s career. You can use the following sub-sections:
   - **Career Beginnings**: Describe how Joseph Klienberg started in his field. What might have inspired him to pursue a career in composing and mosaic art? Even if specific facts aren’t provided, use reasonable context to provide a more expansive description.
   - **Rise to Prominence**: Discuss key milestones or breakthroughs. How did *Beyond the Horizon* gain recognition? Provide details on its composition and reception.
   - **Notable Works**: Expand on major works, explaining their cultural or artistic significance. For example, describe *Beyond the Horizon (Mosaic)* as not just a piece of art but a work that reflects a fusion of styles and its broader impact in the artistic community.

5. **Awards and Recognition**: Elaborate on the significance of the awards the subject received, particularly the National Art Award in 2015. Provide background on the award itself, what it typically honors, and why Joseph’s work was deserving of this accolade.

6. **Philosophy/Style**: When discussing the subject’s style, go into detail about what it means to have a fusion of classical and modern influences. How might this blend of styles be perceived in the art world? What are some general characteristics of both classical and modern approaches that Joseph Klienberg successfully integrates into his work?

7. **Personal Life**: Expand on the subject’s family life, including details about their spouse Sophia Davis, mother Noah Davis, and child Aiden Jones. Discuss the possible dynamics between his personal and professional life, exploring how his relationships might influence his artistic work.

8. **Later Life**: If applicable, discuss any relevant information on the subject's later years. If the facts don’t mention his later life, include general thoughts on how his career might have evolved over time or how his contributions might continue to impact future generations.

9. **Legacy and Impact**: Summarize the subject’s broader contributions to their field, focusing on how they influenced not only their contemporaries but potentially future artists as well. Reflect on the enduring impact of works like *Beyond the Horizon* and his artistic philosophy.

10. **Conclusion**: Conclude the article with a reflective overview of Joseph Klienberg’s life, career, and lasting influence. Use the given facts to provide a detailed and thoughtful summary of his contributions.

### Article Style:
- Expand each section with relevant context and explanations, going beyond the surface-level facts.
- Maintain a neutral, third-person tone.
- Ensure coherence and flow, organizing the content logically into the given sections.
- Do not introduce speculative information that contradicts the facts, but use reasonable background and general knowledge to provide depth.

### Facts:
{}

### Article:
"""

# %%
for person, family, bio in zip(person_list, family_list, bio_list):
    facts = '\n'.join([family, bio])
    print(f"generating article for {person} with the following facts:")
    print(facts)
    print("===========================START ARTICLE==========================")
    response = client.chat.completions.create(
        model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        messages=[
            {"role": "user", "content": prompt.format(facts)},
        ],
        temperature=0.7,
        top_p=0.7,
        top_k=50,
        repetition_penalty=1,
        stop=["<|eot_id|>"],
        stream=True,
    )
    article = ""
    for chunk in response:
        s = chunk.choices[0].delta.content or ""
        print(s, end="", flush=True)
        article += s
    print("\n===========================END ARTICLE==========================")
    # save the article to a file
    article_file = os.path.join(article_folder, f"{person}_article.txt")
    print(f"writing article for {person} to {article_file}")
    with open(article_file, "w") as file:
        file.write(article)

# %%
