from pyswip import Prolog
from phantom_wiki.facts.family import FAMILY_RULES_BASE_PATH

from importlib.resources import files
FAMILY_TREE_26_EXAMPLE_PATH = files("tests").joinpath("family/family_tree_26.pl")

def test_family_rules_base():
    # TODO fix the example to display a valid family tree
    prolog = Prolog()
    prolog.consult(FAMILY_RULES_BASE_PATH)
    prolog.consult(FAMILY_TREE_26_EXAMPLE_PATH)

    assert bool(list(prolog.query("mother(elias, helga)"))) == False
    assert bool(list(prolog.query("father(elias, jan)"))) == True

    # TODO make robust to orderings
    assert list(prolog.query("father(michael, X)")) == [{'X': 'elias'}]
    assert list(prolog.query("parent(michael, X)")) == [{'X': 'elena'}, {'X': 'elias'}]


# # %%
# results = janus.query_once("greatGranddaughter(natalie, anastasia)")
# print(results)  # True

# # %%
# results = janus.query_once("greatGrandson(natalie, anastasia)")
# print(results)  # False

# # %%
# results = janus.query_once("son(elias, X)")
# print(results)  # {'truth': True, 'X': 'jan'}

