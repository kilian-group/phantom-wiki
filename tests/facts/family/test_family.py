from pyswip import Prolog

from phantom_wiki.facts.family import FAMILY_RULES_BASE_PATH, FAMILY_RULES_DERIVED_PATH
from tests.facts.family import (FAMILY_TREE_SMALL_EXAMPLE_PATH,
                                FACTS_SMALL_EXAMPLE_PATH,
                                FACTS_SMALL_DIVORCE_EXAMPLE_PATH,
                                FACTS_SMALL_DIVORCE_REMARRY_EXAMPLE_PATH)


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

def test_in_law():
    prolog = Prolog()
    prolog.consult(FACTS_SMALL_EXAMPLE_PATH)
    prolog.consult(FAMILY_RULES_DERIVED_PATH)
    assert bool(list(prolog.query("mother_in_law(deangelo, kanesha)")))
    assert bool(list(prolog.query("father_in_law(deangelo, derick)")))
    assert compare_prolog_dicts(list(prolog.query("daughter_in_law(derick, X)")), [{"X": "daisy"}, {"X": "ila"}])
    assert compare_prolog_dicts(list(prolog.query("son_in_law(derick, X)")), [{"X": "deangelo"}])
    assert compare_prolog_dicts(list(prolog.query("sister_in_law(deangelo, X)")), [{"X": "kari"}])
    assert compare_prolog_dicts(list(prolog.query("brother_in_law(deangelo, X)")), [{"X": "colby"}, {"X": "dominick"}, {"X": "alfonso"}])

def test_in_law_divorce():
    """
    Test in-law relationships with divorce.
    NOTE: none of these should be true since the divorce rate is 1.0
    """
    prolog = Prolog()
    prolog.consult(FACTS_SMALL_DIVORCE_EXAMPLE_PATH)
    prolog.consult(FAMILY_RULES_DERIVED_PATH)
    assert not bool(list(prolog.query("mother_in_law(deangelo, kanesha)")))
    assert not bool(list(prolog.query("father_in_law(deangelo, derick)")))
    assert compare_prolog_dicts(list(prolog.query("daughter_in_law(derick, X)")), [])
    assert compare_prolog_dicts(list(prolog.query("son_in_law(derick, X)")), [])
    assert compare_prolog_dicts(list(prolog.query("sister_in_law(deangelo, X)")), [])
    assert compare_prolog_dicts(list(prolog.query("brother_in_law(deangelo, X)")), [])

def test_step_parent():
    """
    Test step-parent relationships.
    """
    prolog = Prolog()
    prolog.consult(FACTS_SMALL_DIVORCE_REMARRY_EXAMPLE_PATH)
    prolog.consult(FAMILY_RULES_DERIVED_PATH)
    import pdb; pdb.set_trace()
    assert bool(list(prolog.query("step_mother(ellis, daisy)")))
    assert bool(list(prolog.query("step_father(deanna, alfonso)")))
    assert compare_prolog_dicts(list(prolog.query("step_daughter(alfonso, X)")), [{'X': 'deanna'}, {'X': 'reyna'}, {'X': 'rosalee'}])
    assert compare_prolog_dicts(list(prolog.query("step_son(daisy, X)")), [{'X': 'ellis'}])
    # TODO: Fix these tests
    assert compare_prolog_dicts(list(prolog.query("step_sister(ellis, X)")), [{'X': 'deanna'}, {'X': 'reyna'}, {'X': 'rosalee'}])
    assert compare_prolog_dicts(list(prolog.query("step_brother(reyna, X)")), [{'X': 'ellis'}])
    assert compare_prolog_dicts(list(prolog.query("step_brother(rosalle, X)")), [{'X': 'ellis'}])
    assert compare_prolog_dicts(list(prolog.query("step_brother(deanna, X)")), [{'X': 'ellis'}])


