import os

from phantom_wiki.facts.database import Database
from tests.phantom_wiki.facts import DATABASE_SMALL_PATH


def test_save_database():
    file = "test.pl"
    # create a database and safe to file
    db1 = Database()
    # db1.define("female/1")
    db1.add("type('alice', person)")
    db1.save_to_disk(file)
    assert os.path.exists(file)
    # load the database from the file
    db2 = Database.from_disk(file)
    result = db2.query("distinct(type(X, person))")

    # clean up
    os.remove(file)

    assert result == [{"X": "alice"}]
    # NOTE: for some reason this test fails because there are duplicate facts in the database
    # but when you look inside test.pl, there are no duplicate facts
    # NOTE: prolog.consult() is buggy
    # if you consult "test.pl" from the SWI-Prolog console, it will show that there are no duplicate facts
    # if you consult "test.pl" from pyswipl, it will show that there are duplicate facts


def test_get_names():
    db = Database.from_disk(DATABASE_SMALL_PATH)
    names = db.get_names()
    with open("names.json", "w") as f:
        import json
        json.dump(names, f, indent=4)
    assert set(names) == {
        "Adele Ervin",
        "Alton Cater",
        "Aubrey Leibowitz",
        "Boris Ervin",
        "Bruce Cater",
        "Delpha Donohue",
        "Derick Backus",
        "Dirk Donohue",
        "Ella Cater",
        "Gerry Donohue",
        "Gustavo Leibowitz",
        "Jewel Backus",
        "Karen Ervin",
        "Lisha Leibowitz",
        "Margarite Ussery",
        "Mason Donohue",
        "Pedro Donohue",
        "Rigoberto Bode",
        "Staci Donohue",
        "Therese Donohue",
        "Tiffany Bode",
        "Ty Donohue",
        "Tyler Ussery",
        "Veronica Donohue",
        "Vita Cater",
        "Wes Backus",
        "Wilfredo Cater"
    }
