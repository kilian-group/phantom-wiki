from .constants import (FAMILY_FACT_TEMPLATES,
                        FAMILY_RELATION_EASY,
                        FAMILY_RELATION_HARD)
from .facts import get_family_facts

from importlib.resources import files
FAMILY_RULES_BASE_PATH = files("phantom_wiki").joinpath("facts/family/rules_base.pl")
FAMILY_RULES_DERIVED_PATH = files("phantom_wiki").joinpath("facts/family/rules_derived.pl")
