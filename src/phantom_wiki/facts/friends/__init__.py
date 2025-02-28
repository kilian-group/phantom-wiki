from argparse import ArgumentParser

from ..database import Database
from .generate import create_friendship_graph

#
# Functionality to read the friendship facts for each person in the database.
#
# NOTE: moved this functionality to phantom_wiki/core/article.py.
# Instead of writing separate functions to get friendship facts,
# we can use the get_relation_facts function to get friendship facts
# after providing the relations to query and templates for constructing sentences.

friend_gen_parser = ArgumentParser(description="Friendship Generator", add_help=False)

friend_gen_parser.add_argument(
    "--friendship-k", type=int, default=3, help="Average degree in friendship graph."
)
friend_gen_parser.add_argument(
    "--friendship-seed", type=int, default=1, help="Seed for friendship generation."
)

#
# Functionality to add friendships for everyone in the database.
#
def db_generate_friendships(db: Database, args: ArgumentParser):
    """
    Generate friendship facts for each person in the database.

    Args:
        db (Database): The database to add the friendship facts to.
        args (ArgumentParser): arguments from the CLI.
    """
    names = db.get_person_names()
    friendship_facts = create_friendship_graph(
        names, args.friendship_k, args.friendship_seed, args.visualize, args.output_dir
    )
    # import pdb; pdb.set_trace()
    db.add(*friendship_facts)


from importlib.resources import files

FRIENDSHIP_RULES_PATH = files("phantom_wiki").joinpath("facts/friends/rules.pl")
