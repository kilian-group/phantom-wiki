# imports for paths to Prolog rules
from .family import (FAMILY_RULES_BASE_PATH,
                     FAMILY_RULES_DERIVED_PATH)
from .friends import (FRIENDSHIP_RULES_PATH)
from .attributes import (ATTRIBUTE_RULES_PATH)
# Functionality to get a Prolog database with built-in rules
from .database import Database
def get_database(*data_paths) -> Database:
    """
    Get a Prolog database with built-in rules.
    Add facts to the database from data_paths if provided.
    """
    db = Database(
        FAMILY_RULES_BASE_PATH, 
        FAMILY_RULES_DERIVED_PATH,
        FRIENDSHIP_RULES_PATH,
        ATTRIBUTE_RULES_PATH,
    )

    print(f"Consulting facts from:")
    for path in data_paths:
        print(f"- {path}")
        db.consult(path)

    return db

# Imports for generating facts
from .attributes import db_generate_attributes
from .family import db_generate_family
from .person import db_generate_population
from .friends import db_generate_friendships

# 
# Question generation arguments
# 
# TODO: move this into one of the question generation modules
from argparse import ArgumentParser
question_parser = ArgumentParser(add_help=False)
question_parser.add_argument("--num-questions-per-type", type=int, default=10,
                             help="Number of questions to generate per question type (i.e., template)")
question_parser.add_argument("--valid-only", action="store_true",
                                help="Only generate valid questions")
question_parser.add_argument("--depth", type=int, default=6,
                                help="Depth of the question template")