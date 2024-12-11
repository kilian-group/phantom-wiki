import os

from phantom_wiki.facts import get_database
from phantom_wiki.facts.database import Database
from phantom_wiki.utils.prolog import get_prolog_result_set
from tests.facts.family import FAMILY_TREE_SMALL_EXAMPLE_PATH


def test_save_database():
    # TODO use python tempfiles
    file = "test.pl"
    # create a database and safe to file
    db1 = Database()
    db1.define("female/1")
    db1.add("female(alice)")
    db1.save_to_disk(file)
    assert os.path.exists(file)
    # load the database from the file
    db2 = Database.from_disk(file)
    result = db2.query("female(X)")

    # clean up
    os.remove(file)

    # NOTE: prolog.consult() is buggy
    # if you consult "test.pl" from the SWI-Prolog console, it will show that there are no duplicate facts
    # if you consult "test.pl" from pyswipl, it will show that there are duplicate facts
    #   get_prolog_result_set is a workaround for pyswip's duplicate result sets.
    assert get_prolog_result_set(result) == get_prolog_result_set({"X": "alice"})


def test_get_names():
    db = get_database(FAMILY_TREE_SMALL_EXAMPLE_PATH)
    names = db.get_names()
    assert names == [
        "anastasia",
        "angelina",
        "charlotte",
        "clara",
        "elena",
        "helga",
        "lena",
        "lisa",
        "mary",
        "mia",
        "natalie",
        "nora",
        "sarah",
        "vanessa",
        "elias",
        "fabian",
        "felix",
        "gabriel",
        "jan",
        "jonas",
        "lorenz",
        "maximilian",
        "michael",
        "oskar",
        "patrick",
        "simon",
        "thomas",
        "vincent",
    ]
