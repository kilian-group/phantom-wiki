# 
# Functionality for printing to console with color
# NOTE: this doesn't work if writing to a file
# See possible colors here: https://pypi.org/project/termcolor/
# 
from termcolor import colored
import logging

def red(text):
    logging.info(colored(text, 'red'))
def blue(text):
    logging.info(colored(text, 'blue'))
def green(text):
    logging.info(colored(text, 'green'))
def yellow(text):
    logging.info(colored(text, 'yellow'))
def cyan(text):
    logging.info(colored(text, 'cyan'))

# 
# Functionality for generating unique IDs
# 
import uuid
def generate_unique_id():
    return str(uuid.uuid4())

# 
# Functionality for parsing arguments
# 
from argparse import ArgumentParser
def get_parser(parents=[]):
    """
    Factory for creating an argument parser.
    """
    parser = ArgumentParser(description="Generate PhantomWiki", parents=parents)
    parser.add_argument("--debug", action="store_true", 
                        help="Enable debug output (DEBUG level).")
    parser.add_argument("--quiet", action="store_true", 
                        help="Enable quiet (no) output (WARNING level).")
    parser.add_argument("--seed", "-s", default=1, type=int,
                        help="Global seed for random number generator")
    parser.add_argument("--output-dir", "-od", type=str, default="./out",
                        help="Path to the output folder")
    parser.add_argument("--article-format", type=str, default="txt",
                        help="Format to save the generated articles",
                        choices=["txt", "json"])
    parser.add_argument("--question-format", type=str, default="json_by_type",
                        help="Format to save the generated questions and answers",
                        choices=["json_by_type", "json"])
    return parser

def decode(x):
    if isinstance(x, bytes):
        return x.decode("utf-8")
    return x