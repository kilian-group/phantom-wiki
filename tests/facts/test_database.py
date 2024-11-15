import os
from phantom_wiki.facts.database import Database

def test_save_database():
    file = "test.pl"
    # create a database and safe to file
    db1 = Database()
    db1.define("female/2")
    db1.add("female(alice)", "female(charlotte)")
    db1.save_to_disk(file)
    assert os.path.exists(file)
    # load the database from the file
    db2 = Database.from_disk(file)
    result = db2.query("female(X)")
    
    # clean up
    os.remove(file)
    
    assert len(result) == [{'X': 'alice'}, {'X': 'charlotte'}]
    # NOTE: for some reason this test fails because there are duplicate facts in the database
    # but when you look inside test.pl, there are no duplicate facts
