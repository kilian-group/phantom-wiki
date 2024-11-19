# imports for family relations and templates
from .constants import (FAMILY_FACT_TEMPLATES,
                        FAMILY_RELATION_EASY,
                        FAMILY_RELATION_HARD)

from importlib.resources import files
FAMILY_RULES_BASE_PATH = files("phantom_wiki").joinpath("facts/family/rules_base.pl")
FAMILY_RULES_DERIVED_PATH = files("phantom_wiki").joinpath("facts/family/rules_derived.pl")

# imports for family generation
from argparse import ArgumentParser
# Create parser for family tree generation
fam_gen_parser = ArgumentParser(description="Family Generator", add_help=False)
fam_gen_parser.add_argument("--max-branching-factor", type=int, default=5,
                            help="The maximum number of children that any person in a family tree may have. (Default value: 5.)")
fam_gen_parser.add_argument("--max-tree-depth", type=int, default=5,
                            help="The maximum depth that a family tree may have. (Default value: 5.)")
fam_gen_parser.add_argument("--max-tree-size", type=int, default=26,
                            help="The maximum number of people that may appear in a family tree. (Default value: 26.)")
fam_gen_parser.add_argument("--num-samples", type=int, default=1,
                            help="The size of the dataset to generate. (Default value: 1.)")
fam_gen_parser.add_argument("--output-dir", type=str, default="./out",
                            help="The directory where the Prolog trees will be saved. (Default value: ./out)")
fam_gen_parser.add_argument("--stop-prob", type=float, default=0.0,
                            help="The probability of stopping to further extend a family tree after a person has been added. (Default value: 0.)")
fam_gen_parser.add_argument("--duplicate-names", type=bool, default=False,
                        help="Used to allow/prevent duplicate names in the generation. (Default value: False.)")
# wrapper for family tree generation

import os
import random
from .generate import (Generator,
                    family_tree_to_facts,
                    PersonFactory)
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
    pf = PersonFactory()
    pf.load_names()

    gen = Generator(pf)
    family_trees = gen.generate(args)
    
    for i, family_tree in enumerate(family_trees):
        print(f"Adding family tree {i+1} to the database.")
        # Obtain family tree facts
        facts = family_tree_to_facts(family_tree)
        db.add(*facts)

# imports for family facts
from .facts import get_family_facts