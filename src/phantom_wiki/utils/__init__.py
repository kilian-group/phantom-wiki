# 
# Functionality for printing to console with color
# NOTE: this doesn't work if writing to a file
# See possible colors here: https://pypi.org/project/termcolor/
# 
from termcolor import colored
def red(text):
    print(colored(text, 'red'))
def blue(text):
    print(colored(text, 'blue'))
def green(text):
    print(colored(text, 'green'))
def yellow(text):
    print(colored(text, 'yellow'))
def cyan(text):
    print(colored(text, 'cyan'))

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
    parser.add_argument("--seed", "-s", default=1, type=int,
                        help="Global seed for random number generator")
    parser.add_argument("--output_dir", "-od", type=str, default="./out",
                        help="Path to the output folder")
    return parser
