from phantom_wiki.facts.queries import get_names

FACTS_FILE_PATH = "tests/family/family_tree.pl"

def test_get_names():
    names = get_names(FACTS_FILE_PATH)
    assert names == [
    "anastasia",
    "angelina",
    "charlotte",
    "clara",
    "elena",
    "helga",
    "lena",
    "lisa",
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
    "lorenz",
    "maximilian",
    "michael",
    "oskar",
    "patrick",
    "simon",
    "thomas",
    "vincent"
]
