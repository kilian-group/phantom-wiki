from phantom_wiki.facts.database import Database
from tests.phantom_wiki.facts import DATABASE_SMALL_PATH


def test_get_names():
    db = Database.from_disk(DATABASE_SMALL_PATH)
    names = db.get_person_names()
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
        "Wilfredo Cater",
    }
