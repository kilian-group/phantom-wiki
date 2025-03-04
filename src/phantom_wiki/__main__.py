# Usage:
# Creating questions:
#   python -m phantom_wiki -od <output path>

# standard imports
import subprocess
import sys

from .facts import question_parser

# phantom wiki functionality
from .facts.family import fam_gen_parser
from .facts.friends import friend_gen_parser
from .generate import generate_dataset
from .utils import get_parser


def check_git_status():
    try:
        # Check for uncommitted changes
        result = subprocess.run(["git", "status", "--porcelain"], stdout=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print("Error: Unable to check Git status.")
            sys.exit(1)

        # If `git status --porcelain` output is not empty, there are uncommitted changes
        if result.stdout.strip():
            print(
                "Error: You have uncommitted or unstashed changes. "
                "Please commit or stash them before running this script."
            )
            sys.exit(1)
    except FileNotFoundError:
        print("Error: Git is not installed or not available in PATH.")
        sys.exit(1)


if __name__ == "__main__":
    # We combine a base parser with all the generators' parsers
    parser = get_parser(
        parents=[
            fam_gen_parser,
            friend_gen_parser,
            question_parser,
        ]
    )
    args = parser.parse_args()

    # Check Git status before running the main logic
    if not args.debug:
        check_git_status()
        print("Git status is clean. Running the script...")
    else:
        print("Debug mode enabled. Skipping Git status check.")

    generate_dataset(**vars(args))
