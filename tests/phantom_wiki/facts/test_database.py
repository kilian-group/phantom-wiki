import os

from phantom_wiki.facts.database import Database
from tests.facts.family import FACTS_SMALL_EXAMPLE_PATH


def test_save_database():
    # TODO use python tempfiles
    file = "test.pl"
    # create a database and safe to file
    db1 = Database()
    # db1.define("female/1")
    db1.add("type(\'alice\', person)")
    db1.save_to_disk(file)
    assert os.path.exists(file)
    # load the database from the file
    db2 = Database.from_disk(file)
    result = db2.query("distinct(type(X, person))")
    
    # clean up
    os.remove(file)
    
    assert result == [{'X': 'alice'}]
    # NOTE: for some reason this test fails because there are duplicate facts in the database
    # but when you look inside test.pl, there are no duplicate facts
    # NOTE: prolog.consult() is buggy
    # if you consult "test.pl" from the SWI-Prolog console, it will show that there are no duplicate facts
    # if you consult "test.pl" from pyswipl, it will show that there are duplicate facts

def test_get_names():
    db = Database.from_disk(FACTS_SMALL_EXAMPLE_PATH)
    names = db.get_names()
    assert set(names) == set(['alfonso', 'alton', 'antionette', 'colby', 'daisy', 'deangelo', 'deanna', 'derick', 'dixie', 'dominick', 'ellis', 'ila', 'johnna', 'kanesha', 'kari', 'lyndia', 'maggie', 'matt', 'meghann', 'miki', 'reyna', 'rosalee', 'scotty', 'tanner', 'thomasine', 'vicente'])
