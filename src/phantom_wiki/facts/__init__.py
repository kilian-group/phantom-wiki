# imports for paths to Prolog rules
import logging

from .attributes import ATTRIBUTE_RULES_PATH

# Functionality to get a Prolog database with built-in rules
from .database import Database
from .family import FAMILY_RULES_BASE_PATH, FAMILY_RULES_DERIVED_PATH
from .friends import FRIENDSHIP_RULES_PATH


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

    if data_paths:
        logging.info("Consulting facts from:")
        for path in data_paths:
            logging.info(f"- {path}")
            db.consult(path)

    return db


# Imports for generating facts

#
# Question generation arguments
#
# TODO: move this into one of the question generation modules
from argparse import ArgumentParser

question_parser = ArgumentParser(add_help=False)
question_parser.add_argument(
    "--num-questions-per-type",
    type=int,
    default=10,
    help="Number of questions to generate per question type (i.e., template)",
)
question_parser.add_argument(
    "--num-sampling-attempts", type=int, default=100, help="Number of attempts to sample a valid question"
)
question_parser.add_argument("--question-depth", type=int, default=6, help="Depth of the question template")
question_parser.add_argument(
    "--easy-mode", action="store_true", help="Sample from easy relations (hard mode is default)"
)
question_parser.add_argument(
    "--skip-solution-traces", action="store_true", help="Do not include solution traces in the dataset"
)
