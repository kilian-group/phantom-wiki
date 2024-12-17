from importlib.resources import files

FAMILY_TREE_SMALL_EXAMPLE_PATH = files("tests").joinpath("facts/family/family_tree_small.pl")
FACTS_SMALL_EXAMPLE_PATH = files("tests").joinpath("facts/family/facts_small_divorce_0.pl")
FACTS_SMALL_DIVORCE_EXAMPLE_PATH = files("tests").joinpath("facts/family/facts_small_divorce_1.pl")
# divorce_rate=1, remarry_rate=0
FACTS_SMALL_DIVORCE1_REMARRY0_EXAMPLE_PATH = files("tests").joinpath(
    "facts/family/2trees_divorce1_remarry0/facts_2trees_divorce1_remarry0.pl"
)
# divorce_rate=1, remarry_rate=1
FACTS_SMALL_DIVORCE1_REMARRY1_EXAMPLE_PATH = files("tests").joinpath(
    "facts/family/2trees_divorce1_remarry1/facts_2trees_divorce1_remarry1.pl"
)
