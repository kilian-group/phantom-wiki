from importlib.resources import files

from pyswip import Prolog

from phantom_wiki.facts.family import FAMILY_RULES_BASE_PATH

FAMILY_TREE_26_EXAMPLE_PATH = files("tests").joinpath("facts/family/family_tree_26.pl")


def prolog_result_set(prolog_dict: list[dict]) -> set[list[tuple]]:
    # Convert each dictionary to a list of tuples
    list_of_tuples = [list(d.items()) for d in prolog_dict]
    # Convert the list of tuples to a set of tuples
    set_of_tuples = set(map(tuple, list_of_tuples))
    return set_of_tuples


def compare_prolog_dicts(prolog_dict_1: list[dict], prolog_dict_2: list[dict]) -> bool:
    set_1 = prolog_result_set(prolog_dict_1)
    set_2 = prolog_result_set(prolog_dict_2)
    return set_1 == set_2


def test_family_rules_base():
    prolog = Prolog()
    prolog.consult(FAMILY_RULES_BASE_PATH)
    prolog.consult(FAMILY_TREE_26_EXAMPLE_PATH)

    assert compare_prolog_dicts(list(prolog.query("sibling(michael, X)")), [{"X": "nora"}])
    assert compare_prolog_dicts(
        list(prolog.query("sibling(lisa, X)")), [{"X": "clara"}, {"X": "fabian"}, {"X": "thomas"}]
    )
    assert compare_prolog_dicts(list(prolog.query("sibling(sarah, X)")), [])
    assert not bool(list(prolog.query("sibling(nora, elias)")))

    assert not bool(list(prolog.query("mother(elias, helga)")))
    assert bool(list(prolog.query("father(elias, jan)")))

    assert compare_prolog_dicts(list(prolog.query("father(michael, X)")), [{"X": "elias"}])
    assert compare_prolog_dicts(list(prolog.query("parent(michael, X)")), [{"X": "elena"}, {"X": "elias"}])


# TODO test each family relation
# TODO add derived rule tests

# # %%
# results = janus.query_once("greatGranddaughter(natalie, anastasia)")
# print(results)  # True

# # %%
# results = janus.query_once("greatGrandson(natalie, anastasia)")
# print(results)  # False

# # %%
# results = janus.query_once("son(elias, X)")
# print(results)  # {'truth': True, 'X': 'jan'}
