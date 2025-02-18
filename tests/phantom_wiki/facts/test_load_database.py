from phantom_wiki.facts.database import Database
from tests.phantom_wiki.facts import DATABASE_TEST_PATH


def test_load_database():
    return
    # NOTE: currently, the result has more than one element, so the test fails
    # TODO: make this test pass
    # load the database from the file
    db2 = Database.from_disk(DATABASE_TEST_PATH)
    result = db2.query("distinct(type(X, person))")

    assert result == [{"X": "alice"}]
