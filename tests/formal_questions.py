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
import janus_swi as janus
import re


# %%
def consult(predicate_path, *rule_paths):
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
    pattern = r"^([a-zA-Z_]+)\((.*)\) :-\n$"
    match = re.search(pattern, line)
    return match.group(1), [s.strip() for s in match.group(2).split(",")]


# %%
consult("family_tree.pl", "base_rules.pl", "derived_rules.pl")

# %%
print("Who is the son of Elias?")
result = janus.query_once("son(X, elias)")
print(result)

# %%
# Question 2: How many children does Bob have?
print("Who is the wife of the son of Elias?")
result = janus.query_once("wife(X, Y), son(Y, elias)")
print(result)

# %%
# Question 3: How many grandchildren does Elias have?
print("How many grandchildren does Elias have?")
# result = janus.query_once("findall(X, grandparent(elias, X), L)") #note: query works in swipl, but not in Python
result = list(janus.query("grandParent(elias,X)"))
print(result)


# %% [markdown]
# # Getting all rules

# %%
def get_rules(filename):
    rules = []
    with open(filename, "r") as file:
        for line in file:
            # print(line)
            # if the line is a predicate, print it
            if line.endswith(":-\n"):
                # print(parse(line))
                rules.append(parse(line))
    return rules
def get_question_answers(atom_val, atom_name, rules):
    question_answers = []
    for predicate, args in rules:
        if atom_name in args:
            # print(predicate, args)
            query = f"{predicate}({','.join(args)})"
            # print(query)
            result = janus.query_once(query, {atom_name: atom_val})
            # print(result)

            question = "{atom} is the {predicate} of who?".format(predicate=predicate, atom=atom_val)
            # print("Question: ", question)
            answer = result['Y']
            # print("Answer: ", answer)
            question_answers.append((question, answer))
    return question_answers


# %%
# get all predicates in base_rules.pl
print("All predicates in base_rules.pl")
# read each line of the file
base_rules = get_rules("base_rules.pl")
print(base_rules)
print("All predicates in derived_rules.pl")
derived_rules = get_rules("derived_rules.pl")
print(derived_rules)

# %%
# given X, query all predicates in base_rules.pl that contain X
atom_val = "elias"
atom_name = 'X'
print("Getting base questions for X={}".format(atom_val))
base_question_answers = get_question_answers(atom_val, atom_name, base_rules)
print("Getting derived questions for X={}".format(atom_val))
derived_question_answers = get_question_answers(atom_val, atom_name, derived_rules)

# %%
base_question_answers

# %% [markdown]
# Expected output
# ```
# [('elias is the married of who?', 'elena'),
#  ('elias is the sister of who?', None),
#  ('elias is the brother of who?', None),
#  ('elias is the father of who?', 'michael'),
#  ('elias is the son of who?', 'jan'),
#  ('elias is the daughter of who?', None),
#  ('elias is the wife of who?', None)]
# ```

# %%
derived_question_answers

# %% [markdown]
# Expected output
# ```
# [('elias is the niece of who?', None),
#  ('elias is the nephew of who?', None),
#  ('elias is the grandParent of who?', 'simon'),
#  ('elias is the grandmother of who?', None),
#  ('elias is the grandFather of who?', 'simon'),
#  ('elias is the greatAunt of who?', None),
#  ('elias is the greatUncle of who?', None),
#  ('elias is the grandChild of who?', None),
#  ('elias is the grandDaughter of who?', None),
#  ('elias is the grandSon of who?', None),
#  ('elias is the greatGrandparent of who?', 'felix'),
#  ('elias is the greatGrandmother of who?', None),
#  ('elias is the greatGrandfather of who?', 'felix'),
#  ('elias is the greatGrandchild of who?', None),
#  ('elias is the greatGranddaughter of who?', None),
#  ('elias is the greatGrandson of who?', None),
#  ('elias is the secondAunt of who?', None),
#  ('elias is the secondUncle of who?', None),
#  ('elias is the aunt of who?', None),
#  ('elias is the uncle of who?', None),
#  ('elias is the cousin of who?', None),
#  ('elias is the girlCousin of who?', None),
#  ('elias is the boyCousin of who?', None),
#  ('elias is the girlSecondCousin of who?', None),
#  ('elias is the boySecondCousin of who?', None),
#  ('elias is the girlFirstCousinOnceRemoved of who?', None),
#  ('elias is the boyFirstCousinOnceRemoved of who?', None)]
# ```

# %%
