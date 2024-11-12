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

    assert compare_prolog_dicts(list(prolog.query("parent(michael, X)")), [{"X": "elena"}, {"X": "elias"}])

    assert compare_prolog_dicts(list(prolog.query("sibling(michael, X)")), [{"X": "nora"}])
    assert compare_prolog_dicts(
        list(prolog.query("sibling(lisa, X)")), [{"X": "clara"}, {"X": "fabian"}, {"X": "thomas"}]
    )
    assert compare_prolog_dicts(list(prolog.query("sibling(sarah, X)")), [])
    assert not bool(list(prolog.query("sibling(nora, elias)")))

    assert bool(list(prolog.query("married(charlotte, maximilian)")))
    assert not bool(list(prolog.query("married(charlotte, patrick)")))

    assert bool(list(prolog.query("sister(clara, lisa)")))
    assert not bool(list(prolog.query("sister(clara, thomas)")))

    assert bool(list(prolog.query("brother(fabian, thomas)")))
    assert not bool(list(prolog.query("brother(fabian, lisa)")))

    assert bool(list(prolog.query("mother(michael, elena)")))
    assert not bool(list(prolog.query("mother(elias, helga)")))

    assert bool(list(prolog.query("father(elias, jan)")))
    assert compare_prolog_dicts(list(prolog.query("father(michael, X)")), [{"X": "elias"}])

    assert bool(list(prolog.query("child(sarah, lorenz)")))
    assert compare_prolog_dicts(
        list(prolog.query("child(charlotte, X)")),
        [{"X": "clara"}, {"X": "fabian"}, {"X": "lisa"}, {"X": "thomas"}],
    )

    assert bool(list(prolog.query("son(charlotte, fabian)")))
    assert compare_prolog_dicts(list(prolog.query("son(charlotte, X)")), [{"X": "fabian"}, {"X": "thomas"}])

    assert bool(list(prolog.query("daughter(charlotte, lisa)")))
    assert compare_prolog_dicts(list(prolog.query("daughter(charlotte, X)")), [{"X": "clara"}, {"X": "lisa"}])

    assert bool(list(prolog.query("wife(maximilian, charlotte)")))
    assert bool(list(prolog.query("husband(charlotte, maximilian)")))


# TODO add derived rule tests
