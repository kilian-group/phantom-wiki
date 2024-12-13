from importlib.resources import files

FAMILY_TREE_SMALL_EXAMPLE_PATH = files("tests").joinpath("facts/family/family_tree_small.pl")
FACTS_SMALL_EXAMPLE_PATH = files("tests").joinpath("facts/family/facts_small_divorce_0.pl")
FACTS_SMALL_DIVORCE_EXAMPLE_PATH = files("tests").joinpath("facts/family/facts_small_divorce_1.pl")
# divorce_rate=1, remarry_rate=0.5
FACTS_SMALL_DIVORCE_REMARRY_EXAMPLE_PATH = files("tests").joinpath(
    "facts/family/facts_small_divorce_remarry_1.pl"
)
