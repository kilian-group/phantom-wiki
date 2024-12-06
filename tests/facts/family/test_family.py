from pyswip import Prolog

from phantom_wiki.facts.family import FAMILY_RULES_BASE_PATH, FAMILY_RULES_DERIVED_PATH
from tests.facts.family import FAMILY_TREE_SMALL_EXAMPLE_PATH


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
    prolog.consult(FAMILY_TREE_SMALL_EXAMPLE_PATH)

    assert compare_prolog_dicts(list(prolog.query("parent(michael, X)")), [{"X": "elena"}, {"X": "elias"}])

    assert compare_prolog_dicts(list(prolog.query("sibling(michael, X)")), [{"X": "nora"}])
    assert compare_prolog_dicts(
        list(prolog.query("sibling(lisa, X)")), [{"X": "clara"}, {"X": "fabian"}, {"X": "thomas"}]
    )
    assert compare_prolog_dicts(list(prolog.query("sibling(sarah, X)")), [])
    assert not bool(list(prolog.query("sibling(nora, elias)")))

    # assert bool(list(prolog.query("married(charlotte, maximilian)")))
    # assert not bool(list(prolog.query("married(charlotte, patrick)")))

    assert bool(list(prolog.query("sister(clara, lisa)")))
    assert not bool(list(prolog.query("sister(clara, thomas)")))

    assert bool(list(prolog.query("brother(fabian, thomas)")))
    assert not bool(list(prolog.query("brother(fabian, lisa)")))

    assert bool(list(prolog.query("mother(michael, elena)")))
    assert not bool(list(prolog.query("mother(elias, helga)")))

    assert bool(list(prolog.query("father(elias, jan)")))
    assert compare_prolog_dicts(list(prolog.query("father(michael, X)")), [{"X": "elias"}])

    assert bool(list(prolog.query("child(sarah, angelina)")))
    assert compare_prolog_dicts(
        list(prolog.query("child(charlotte, X)")),
        [{"X": "clara"}, {"X": "fabian"}, {"X": "lisa"}, {"X": "thomas"}],
    )

    assert bool(list(prolog.query("son(charlotte, fabian)")))
    assert compare_prolog_dicts(list(prolog.query("son(charlotte, X)")), [{"X": "fabian"}, {"X": "thomas"}])

    assert bool(list(prolog.query("daughter(charlotte, lisa)")))
    assert compare_prolog_dicts(list(prolog.query("daughter(charlotte, X)")), [{"X": "clara"}, {"X": "lisa"}])

    # assert bool(list(prolog.query("wife(maximilian, charlotte)")))
    # assert bool(list(prolog.query("husband(charlotte, maximilian)")))


def test_family_rules_derived():
    prolog = Prolog()
    prolog.consult(FAMILY_RULES_BASE_PATH)
    prolog.consult(FAMILY_RULES_DERIVED_PATH)
    prolog.consult(FAMILY_TREE_SMALL_EXAMPLE_PATH)

    assert bool(list(prolog.query("niece(clara, angelina)")))
    assert compare_prolog_dicts(list(prolog.query("niece(fabian, X)")), [{"X": "angelina"}])

    assert bool(list(prolog.query("nephew(thomas, simon)")))
    assert compare_prolog_dicts(list(prolog.query("nephew(clara, X)")), [{"X": "simon"}])

    assert compare_prolog_dicts(
        list(prolog.query("grandparent(michael, X)")),
        [{"X": "oskar"}, {"X": "vanessa"}, {"X": "jan"}, {"X": "lena"}],
    )
    assert compare_prolog_dicts(
        list(prolog.query("grandmother(michael, X)")), [{"X": "vanessa"}, {"X": "lena"}]
    )
    assert compare_prolog_dicts(list(prolog.query("grandfather(michael, X)")), [{"X": "oskar"}, {"X": "jan"}])

    assert bool(list(prolog.query("great_aunt(angelina, mary)")))
    assert bool(list(prolog.query("great_uncle(angelina, jonas)")))

    assert compare_prolog_dicts(
        list(prolog.query("grandchild(maximilian, X)")), [{"X": "simon"}, {"X": "angelina"}]
    )

    assert compare_prolog_dicts(list(prolog.query("granddaughter(maximilian, X)")), [{"X": "angelina"}])

    assert compare_prolog_dicts(
        list(prolog.query("great_grandparent(gabriel, X)")),
        [{"X": "elena"}, {"X": "elias"}, {"X": "charlotte"}, {"X": "maximilian"}],
    )

    assert compare_prolog_dicts(
        list(prolog.query("great_grandmother(gabriel, X)")), [{"X": "elena"}, {"X": "charlotte"}]
    )

    assert compare_prolog_dicts(
        list(prolog.query("great_grandfather(gabriel, X)")), [{"X": "elias"}, {"X": "maximilian"}]
    )

    assert compare_prolog_dicts(
        list(prolog.query("great_grandchild(elena, X)")), [{"X": "gabriel"}, {"X": "felix"}]
    )

    assert compare_prolog_dicts(list(prolog.query("great_granddaughter(patrick, X)")), [{"X": "natalie"}])

    assert compare_prolog_dicts(
        list(prolog.query("great_grandson(elias, X)")), [{"X": "gabriel"}, {"X": "felix"}]
    )

    assert bool(list(prolog.query("second_aunt(natalie, mary)")))
    assert bool(list(prolog.query("second_uncle(natalie, jonas)")))

    assert compare_prolog_dicts(list(prolog.query("aunt(angelina, X)")), [{"X": "clara"}, {"X": "lisa"}])
    assert compare_prolog_dicts(list(prolog.query("uncle(angelina, X)")), [{"X": "fabian"}])

    assert compare_prolog_dicts(list(prolog.query("cousin(angelina, X)")), [{"X": "simon"}])
    assert compare_prolog_dicts(list(prolog.query("female_cousin(simon, X)")), [{"X": "angelina"}])
    assert compare_prolog_dicts(list(prolog.query("male_cousin(angelina, X)")), [{"X": "simon"}])

    assert compare_prolog_dicts(list(prolog.query("female_second_cousin(gabriel, X)")), [{"X": "natalie"}])
    assert compare_prolog_dicts(
        list(prolog.query("male_second_cousin(natalie, X)")), [{"X": "gabriel"}, {"X": "felix"}]
    )

    assert compare_prolog_dicts(
        list(prolog.query("female_first_cousin_once_removed(simon, X)")), [{"X": "natalie"}]
    )
    assert compare_prolog_dicts(
        list(prolog.query("male_first_cousin_once_removed(angelina, X)")), [{"X": "gabriel"}, {"X": "felix"}]
    )
