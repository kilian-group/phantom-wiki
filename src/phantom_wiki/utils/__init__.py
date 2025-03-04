#
# Functionality for printing to console with color
# NOTE: this doesn't work if writing to a file
# See possible colors here: https://pypi.org/project/termcolor/
#
import logging

from termcolor import colored


def red(text):
    logging.info(colored(text, "red"))


def blue(text):
    logging.info(colored(text, "blue"))


def green(text):
    logging.info(colored(text, "green"))


def yellow(text):
    logging.info(colored(text, "yellow"))


def cyan(text):
    logging.info(colored(text, "cyan"))


#
# Functionality for generating unique IDs
#
import uuid


def generate_unique_id():
    return str(uuid.uuid4())


#
# Functionality for parsing arguments
#
import argparse


def get_parser(parents: list) -> argparse.ArgumentParser:
    """
    Factory for creating an argument parser.
    """
    parser = argparse.ArgumentParser(description="Generate a PhantomWiki instance", parents=parents)
    parser.add_argument("--debug", action="store_true", help="Enable debug output (DEBUG level).")
    parser.add_argument("--quiet", action="store_true", help="Enable quiet (no) output (WARNING level).")
    parser.add_argument(
        "--visualize", action="store_true", help="Whether or not to visualize the friendship & family graphs."
    )
    parser.add_argument(
        "--use-multithreading",
        action="store_true",
        help=(
            "Use multithreading for querying the database when generating questions/answers. "
            "Note: This flag worked for windows and Linux, but not for MacOS."
            "Also very intensive for high universe size."
        ),
    )
    parser.add_argument("--seed", "-s", default=1, type=int, help="Global seed for random number generator")
    parser.add_argument("--output-dir", "-od", type=str, default="./out", help="Path to the output folder")
    parser.add_argument(
        "--article-format",
        type=str,
        default="txt",
        help="Format to save the generated articles",
        choices=["txt", "json"],
    )
    parser.add_argument(
        "--question-format",
        type=str,
        default="json_by_type",
        help="Format to save the generated questions and answers",
        choices=["json_by_type", "json"],
    )
    return parser


def decode(x):
    if isinstance(x, bytes):
        return x.decode("utf-8")
    return x
