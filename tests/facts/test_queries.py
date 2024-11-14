from phantom_wiki.facts import get_database
from tests.facts.family import FAMILY_TREE_SMALL_EXAMPLE_PATH

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
