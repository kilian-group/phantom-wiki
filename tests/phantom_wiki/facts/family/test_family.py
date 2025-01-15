from pyswip import Prolog

from tests.phantom_wiki.facts.family import FAMILY_TREE_SMALL_EXAMPLE_PATH


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
    prolog.consult(FAMILY_TREE_SMALL_EXAMPLE_PATH)

    assert compare_prolog_dicts(
        list(prolog.query("parent('Dirk Donohue', X)")), [{"X": "Mason Donohue"}, {"X": "Therese Donohue"}]
    )

    assert compare_prolog_dicts(
        list(prolog.query("sibling('Dirk Donohue', X)")),
        [{"X": "Pedro Donohue"}, {"X": "Ty Donohue"}, {"X": "Veronica Donohue"}],
    )
    assert compare_prolog_dicts(list(prolog.query("sibling('Ella Cater', X)")), [])

    assert compare_prolog_dicts(
        list(prolog.query("sibling('Dirk Donohue', X)")),
        [{"X": "Pedro Donohue"}, {"X": "Ty Donohue"}, {"X": "Veronica Donohue"}],
    )
    assert not bool(list(prolog.query("sibling('Dirk Donohue', 'Ella Cater')")))

    assert bool(list(prolog.query("married('Therese Donohue', 'Mason Donohue')")))
    assert not bool(list(prolog.query("married('Therese Donohue', 'Ella Cater')")))

    assert bool(list(prolog.query("sister('Dirk Donohue', 'Veronica Donohue')")))
    assert not bool(list(prolog.query("sister('Dirk Donohue', 'Ella Cater')")))

    assert bool(list(prolog.query("brother('Veronica Donohue', 'Dirk Donohue')")))
    assert not bool(list(prolog.query("brother('Veronica Donohue', 'Ella Cater')")))

    assert bool(list(prolog.query("mother('Dirk Donohue', 'Therese Donohue')")))
    assert not bool(list(prolog.query("mother('Dirk Donohue', 'Ella Cater')")))

    assert bool(list(prolog.query("father('Dirk Donohue', 'Mason Donohue')")))
    assert compare_prolog_dicts(list(prolog.query("father('Dirk Donohue', X)")), [{"X": "Mason Donohue"}])

    assert bool(list(prolog.query("child('Mason Donohue', 'Dirk Donohue')")))
    assert compare_prolog_dicts(
        list(prolog.query("child('Mason Donohue', X)")),
        [{"X": "Dirk Donohue"}, {"X": "Pedro Donohue"}, {"X": "Ty Donohue"}, {"X": "Veronica Donohue"}],
    )

    assert bool(list(prolog.query("son('Mason Donohue', 'Dirk Donohue')")))
    assert compare_prolog_dicts(
        list(prolog.query("son('Mason Donohue', X)")),
        [{"X": "Dirk Donohue"}, {"X": "Pedro Donohue"}, {"X": "Ty Donohue"}],
    )

    assert bool(list(prolog.query("daughter('Mason Donohue', 'Veronica Donohue')")))
    assert compare_prolog_dicts(
        list(prolog.query("daughter('Mason Donohue', X)")), [{"X": "Veronica Donohue"}]
    )

    assert bool(list(prolog.query("wife('Mason Donohue', 'Therese Donohue')")))
    assert bool(list(prolog.query("husband('Therese Donohue', 'Mason Donohue')")))


def test_family_rules_derived():
    prolog = Prolog()
    prolog.consult(FAMILY_TREE_SMALL_EXAMPLE_PATH)

    assert bool(list(prolog.query("niece('Veronica Donohue', 'Vita Cater')")))
    assert compare_prolog_dicts(list(prolog.query("niece('Veronica Donohue', X)")), [{"X": "Vita Cater"}])

    assert bool(list(prolog.query("nephew('Veronica Donohue', 'Gerry Donohue')")))
    assert compare_prolog_dicts(list(prolog.query("nephew('Veronica Donohue', X)")), [{"X": "Gerry Donohue"}])

    assert compare_prolog_dicts(
        list(prolog.query("grandparent('Gerry Donohue', X)")),
        [{"X": "Mason Donohue"}, {"X": "Therese Donohue"}],
    )
    assert compare_prolog_dicts(
        list(prolog.query("grandmother('Gerry Donohue', X)")), [{"X": "Therese Donohue"}]
    )
    assert compare_prolog_dicts(
        list(prolog.query("grandfather('Gerry Donohue', X)")), [{"X": "Mason Donohue"}]
    )

    assert bool(list(prolog.query("great_aunt('Alton Cater', 'Veronica Donohue')")))
    assert compare_prolog_dicts(
        list(prolog.query("great_uncle('Alton Cater', X)")),
        [{"X": "Dirk Donohue"}, {"X": "Ty Donohue"}, {"X": "Dirk Donohue"}],
    )

    assert compare_prolog_dicts(
        list(prolog.query("grandchild('Therese Donohue', X)")), [{"X": "Gerry Donohue"}, {"X": "Vita Cater"}]
    )
    assert compare_prolog_dicts(
        list(prolog.query("granddaughter('Therese Donohue', X)")), [{"X": "Vita Cater"}]
    )
    assert compare_prolog_dicts(
        list(prolog.query("grandson('Therese Donohue', X)")), [{"X": "Gerry Donohue"}]
    )

    assert compare_prolog_dicts(
        list(prolog.query("great_grandparent('Adele Ervin', X)")),
        [{"X": "Delpha Donohue"}, {"X": "Pedro Donohue"}],
    )

    assert compare_prolog_dicts(
        list(prolog.query("great_grandmother('Adele Ervin', X)")), [{"X": "Delpha Donohue"}]
    )

    assert compare_prolog_dicts(
        list(prolog.query("great_grandfather('Adele Ervin', X)")), [{"X": "Pedro Donohue"}]
    )

    assert compare_prolog_dicts(
        list(prolog.query("great_grandchild('Pedro Donohue', X)")),
        [{"X": "Adele Ervin"}, {"X": "Jewel Backus"}, {"X": "Lisha Leibowitz"}, {"X": "Wilfredo Cater"}],
    )

    assert compare_prolog_dicts(
        list(prolog.query("great_granddaughter('Pedro Donohue', X)")),
        [{"X": "Adele Ervin"}, {"X": "Jewel Backus"}, {"X": "Lisha Leibowitz"}],
    )

    assert compare_prolog_dicts(
        list(prolog.query("great_grandson('Pedro Donohue', X)")), [{"X": "Wilfredo Cater"}]
    )

    assert bool(list(prolog.query("second_aunt('Adele Ervin', 'Veronica Donohue')")))
    assert bool(list(prolog.query("second_uncle('Adele Ervin', 'Dirk Donohue')")))

    assert compare_prolog_dicts(list(prolog.query("aunt('Adele Ervin', X)")), [])
    assert compare_prolog_dicts(list(prolog.query("uncle('Adele Ervin', X)")), [{"X": "Alton Cater"}])

    assert compare_prolog_dicts(
        list(prolog.query("cousin('Adele Ervin', X)")), [{"X": "Jewel Backus"}, {"X": "Wilfredo Cater"}]
    )
    assert compare_prolog_dicts(
        list(prolog.query("female_cousin('Adele Ervin', X)")), [{"X": "Jewel Backus"}]
    )
    assert compare_prolog_dicts(
        list(prolog.query("male_cousin('Adele Ervin', X)")), [{"X": "Wilfredo Cater"}]
    )

    assert compare_prolog_dicts(list(prolog.query("female_second_cousin('Adele Ervin', X)")), [])
    assert compare_prolog_dicts(
        list(prolog.query("male_second_cousin('Derick Backus', X)")), [{"X": "Gustavo Leibowitz"}]
    )

    assert compare_prolog_dicts(
        list(prolog.query("female_first_cousin_once_removed('Gerry Donohue', X)")), [{"X": "Karen Ervin"}]
    )
    assert compare_prolog_dicts(
        list(prolog.query("male_first_cousin_once_removed('Wilfredo Cater', X)")),
        [{"X": "Gustavo Leibowitz"}],
    )


def test_family_rules_inlaws():
    prolog = Prolog()
    prolog.consult(FAMILY_TREE_SMALL_EXAMPLE_PATH)

    assert compare_prolog_dicts(
        list(prolog.query("father_in_law('Alton Cater', X)")), [{"X": "Tyler Ussery"}]
    )
    assert compare_prolog_dicts(
        list(prolog.query("mother_in_law('Alton Cater', X)")), [{"X": "Margarite Ussery"}]
    )
    assert compare_prolog_dicts(list(prolog.query("son_in_law('Alton Cater', X)")), [{"X": "Wes Backus"}])
    assert compare_prolog_dicts(list(prolog.query("daughter_in_law('Alton Cater', X)")), [])
    assert compare_prolog_dicts(list(prolog.query("brother_in_law('Alton Cater', X)")), [])
    assert compare_prolog_dicts(list(prolog.query("sister_in_law('Alton Cater', X)")), [])

    assert compare_prolog_dicts(
        list(prolog.query("father_in_law('Aubrey Leibowitz', X)")), [{"X": "Boris Ervin"}]
    )
    assert compare_prolog_dicts(
        list(prolog.query("mother_in_law('Aubrey Leibowitz', X)")), [{"X": "Karen Ervin"}]
    )
    assert compare_prolog_dicts(list(prolog.query("son_in_law('Aubrey Leibowitz', X)")), [])
    assert compare_prolog_dicts(list(prolog.query("daughter_in_law('Aubrey Leibowitz', X)")), [])
    assert compare_prolog_dicts(list(prolog.query("brother_in_law('Aubrey Leibowitz', X)")), [])
    assert compare_prolog_dicts(
        list(prolog.query("sister_in_law('Aubrey Leibowitz', X)")), [{"X": "Adele Ervin"}]
    )
