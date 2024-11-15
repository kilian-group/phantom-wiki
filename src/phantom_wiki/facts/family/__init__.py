# imports for family relations and templates
from .constants import (FAMILY_FACT_TEMPLATES,
                        FAMILY_RELATION_EASY,
                        FAMILY_RELATION_HARD)
# imports for paths to family rules
from importlib.resources import files
FAMILY_RULES_BASE_PATH = files("phantom_wiki").joinpath("facts/family/rules_base.pl")
FAMILY_RULES_DERIVED_PATH = files("phantom_wiki").joinpath("facts/family/rules_derived.pl")

# imports for family generation
from argparse import ArgumentParser
import os
import random
from .generate import (Generator,
                       family_tree_to_facts)
def db_generate_family(db, args: ArgumentParser):
    """Generates family facts for a database.
    
    args:
        db: Database
        num_people: number of people to generate
        seed: random seed
    """
    # set the random seed
    random.seed(args.seed)
    # Get the prolog family tree
    family_trees = Generator.generate(args)
    
    for i, family_tree in enumerate(family_trees):
        print(f"Adding family tree {i+1} to the database.")
        # Obtain family tree facts
        facts = family_tree_to_facts(family_tree)
        db.add(*facts)

# imports for family facts
from .facts import get_family_facts