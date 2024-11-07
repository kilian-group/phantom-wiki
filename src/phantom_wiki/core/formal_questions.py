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

# %%
def consult(predicate_path, *rule_paths):
    print(f"loading predicates from {predicate_path}")
    janus.query_once(f"consult(X)", {'X': predicate_path})
    for rule_path in rule_paths:
        print(f"loading rules from {rule_path}")
        janus.query_once("consult(X)", {'X': rule_path})

# %%
# consult("family_tree.pl", "base_rules.pl", "derived_rules.pl")

# %%
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
            question_answers.append({'question':question, 'answer':answer})
    return question_answers
