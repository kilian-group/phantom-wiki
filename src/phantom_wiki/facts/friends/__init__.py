from ..database import Database
from .generate import create_friendship_graph

# 
# Functionality to read the friendship facts for each person in the database.
#
# NOTE: moved this functionality to phantom_wiki/core/article.py.
# Instead of writing separate functions to get friendship facts,
# we can use the get_relation_facts function to get friendship facts
# after providing the relations to query and templates for constructing sentences.
from .constants import (FRIENDSHIP_RELATION,
                        FRIENDSHIP_FACT_TEMPLATES)

# 
# Functionality to add friendships for everyone in the database.
# 
def db_generate_friendships(db: Database, seed: int = 1):
    """
    Generate friendship facts for each person in the database.
    
    Args:
        db (Database): The database to add the friendship facts to.
        seed (int): The seed for the random number generator.
    """
    names = db.get_names()
    friendship_facts, _ = create_friendship_graph(names, friendship_threshold=20)
    db.add(*friendship_facts)

from importlib.resources import files
FRIENDSHIP_RULES_PATH = files("phantom_wiki").joinpath("facts/friends/rules.pl")
