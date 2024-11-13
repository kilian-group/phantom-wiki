from phantom_wiki.facts.queries import get_names
from tests.facts.family import FAMILY_TREE_SMALL_EXAMPLE_PATH


def test_get_names():
    names = get_names(FAMILY_TREE_SMALL_EXAMPLE_PATH)
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
