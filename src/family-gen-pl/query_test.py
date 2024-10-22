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
def consult(predicate_path, rule_path):
    janus.query_once(f"consult(X)", {'X': predicate_path})
    janus.query_once("consult(X)", {'X': rule_path})
# load the prolog files
consult('../../tests/family_tree.pl', './family/rules.pl')

# %%
results = janus.query_once("mother(elias, helga)")
print(results) # False
results = janus.query_once("father(elias, michael)")
print(results) # True

# %%
results = janus.query_once("greatGranddaughter(natalie, anastasia)")
print(results) # True

# %%
results = janus.query_once("greatGrandson(natalie, anastasia)")
print(results) # False

# %%
janus.query_once("son(elias, X)")


# %%
def get_family_table(name):
    """
    Get the following relations for a given name:
    - mother
    - father
    - siblings
    - children
    - wife/husband (TODO: need to add married predicate to the prolog)

    Assumes that the prolog files are loaded and the predicates are defined in the prolog files.
    This can be done using the following code:
    ```
    janus.query_once("consult('../../tests/family_tree.pl')")
    janus.query_once("consult('./family/rules.pl')")
    ```

    Ref: https://www.swi-prolog.org/pldoc/man?section=janus-call-prolog
    """
    # name = 'elias'
    # get mother
    if mother := janus.query_once("mother(X, Y)", {'Y': name}):
        mother = mother['X']
    # print(mother)
    # get father
    if father := janus.query_once("father(X, Y)", {'Y': name}):
        father = father['X']
    # print(father)
    # get siblings
    if siblings := janus.query("sibling(X, Y)", {'Y': name}):
        siblings = [sibling['X'] for sibling in siblings]
    # print(list(siblings))
    # get children
    if children := list(janus.query("child(X, Y)", {'Y': name})):
        children = [child['X'] for child in children]
    # print(list(children))
    
    # TODO: get wife and husband
    # wife = janus.query_once(f"wife(X, Y)", {'X': 'nora'})
    wife = None
    # husband = janus.query_once(f"husband(X, Y)", {'X': 'nora'})
    husband = None
    
    return {
        'mother': mother,
        'father': father,
        'siblings': siblings,
        'children': children,
        'wife': wife,
        'husband': husband,
    }


# %%
name = 'natalie'
table = get_family_table(name)
print("Table for {}: ".format(name))
print(table)

# %%
