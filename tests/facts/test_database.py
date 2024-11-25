import os
from phantom_wiki.facts.database import Database
from phantom_wiki.facts import get_database
from tests.facts.family import FAMILY_TREE_SMALL_EXAMPLE_PATH

def test_save_database():
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
    
    assert len(result) == [{'X': 'alice'}]
    # NOTE: for some reason this test fails because there are duplicate facts in the database
    # but when you look inside test.pl, there are no duplicate facts
    # NOTE: prolog.consult() is buggy
    # if you consult "test.pl" from the SWI-Prolog console, it will show that there are no duplicate facts
    # if you consult "test.pl" from pyswipl, it will show that there are duplicate facts

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
