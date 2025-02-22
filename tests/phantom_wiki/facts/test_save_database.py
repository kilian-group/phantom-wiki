import os

from phantom_wiki.facts.database import Database


def test_save_database():
    # TODO use python tempfiles
    file = "test.pl"
    # create a database and save to file
    db1 = Database()
    db1.add("type('alice', person)")
    db1.save_to_disk(file)
    assert os.path.exists(file)
    os.remove(file)
