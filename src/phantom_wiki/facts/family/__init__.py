from importlib.resources import files

FAMILY_RULES_BASE_PATH = files("phantom_wiki").joinpath("facts/family/rules_base.pl")
FAMILY_RULES_DERIVED_PATH = files("phantom_wiki").joinpath("facts/family/rules_derived.pl")
