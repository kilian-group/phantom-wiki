# standard imports
from argparse import ArgumentParser

from ...utils.movies import get_names_from_SQL

# phantom wiki functionality
from ..database import Database


def db_generate_movies(db: Database, args: ArgumentParser):
    """
    Generate attributes for each person in the database.

    Args:
        db (Database): The database containing the facts.
        args (ArgumentParser): The command line arguments.
    """
    names = db.get_names()
    # TODO: add parser for movie dataset
    hollywood_names = get_names_from_SQL(args.movies_dataset)

    # add the facts to the database
    facts = []
    # TODO: sustitute SQL with Prolog

    db.add(*facts)
