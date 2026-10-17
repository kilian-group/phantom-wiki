# imports for paths to Prolog rules
import logging

from .attributes import ATTRIBUTE_RULES_PATH

# Functionality to get a Prolog database with built-in rules
from .database import Database
from .family import FAMILY_RULES_BASE_PATH, FAMILY_RULES_DERIVED_PATH
from .friends import FRIENDSHIP_RULES_PATH
from .inverse_relations import register_inverse_predicates


def get_database(*data_paths, register_inverses: bool = False) -> Database:
    """
    Get a Prolog database with built-in rules.
    Add facts to the database from data_paths if provided.

    Args:
        data_paths: Paths to Prolog fact files to consult.
        register_inverses: If True, register inverse predicates for
            bidirectional sampling.

    Returns:
        A Database instance with all rules and facts loaded.
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

    if register_inverses:
        register_inverse_predicates(db)

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
question_parser.add_argument(
    "--easy-mode", action="store_true", help="Sample from easy relations (hard mode is default)"
)
question_parser.add_argument(
    "--skip-solution-traces", action="store_true", help="Do not include solution traces in the dataset"
)
question_parser.add_argument(
    "--balanced",
    action="store_true",
    help="Enable difficulty-balanced question sampling (equal questions per difficulty bucket)",
)
question_parser.add_argument(
    "--min-difficulty",
    type=int,
    default=None,
    help="Filter questions to minimum difficulty (inclusive)",
)
question_parser.add_argument(
    "--max-difficulty",
    type=int,
    default=None,
    help="Filter questions to maximum difficulty (inclusive)",
)
question_parser.add_argument(
    "--question-types",
    type=str,
    default="base",
    help="Comma-separated question types to generate: base,comparison_age,comparison_count,multi_constraint,superlative (default: base)",
)
question_parser.add_argument(
    "--min-hops",
    type=int,
    default=None,
    help="Filter questions to minimum hop count (inclusive)",
)
question_parser.add_argument(
    "--max-hops",
    type=int,
    default=4,
    help="Largest hop count any generated question may have. Drives base CFG depth and chain builders. Also acts as the post-generation filter ceiling.",
)
question_parser.add_argument(
    "--min-constraints",
    type=int,
    default=None,
    help="Filter questions to minimum constraint count (inclusive)",
)
question_parser.add_argument(
    "--max-constraints",
    type=int,
    default=3,
    help="Largest attribute-constraint count any generated question may have. Determines mc-N anchor sizes and standalone multi-constraint sizes.",
)
question_parser.add_argument(
    "--sample-count",
    type=int,
    default=None,
    help="Exact number of questions to sample from the generated pool",
)
question_parser.add_argument(
    "--sample-min-steps",
    type=int,
    default=None,
    help="Minimum reasoning steps for sampling filter (inclusive)",
)
question_parser.add_argument(
    "--sample-max-steps",
    type=int,
    default=None,
    help="Maximum reasoning steps for sampling filter (inclusive)",
)
question_parser.add_argument(
    "--sample-types",
    type=str,
    default=None,
    help="Comma-separated question types to include when sampling: base,comparison,multi_constraint,superlative",
)
question_parser.add_argument(
    "--describe-pool",
    action="store_true",
    help="Print a breakdown of the question pool by difficulty and type, then exit (no sampling)",
)
question_parser.add_argument(
    "--sampling-method",
    type=str,
    default="bidirectional",
    choices=["backward", "bidirectional"],
    help="Sampling method for question generation (default: bidirectional)",
)
question_parser.add_argument(
    "--anchor-strategy",
    type=str,
    default="random",
    choices=["random", "balanced", "start", "middle", "end"],
    help="Anchor placement strategy for bidirectional sampling (default: random)",
)
question_parser.add_argument(
    "--answer-position",
    type=str,
    default="head",
    choices=["head", "tail", "random"],
    help="Position of the answer in the relation chain (default: head)",
)
