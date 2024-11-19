from .database import Database
# imports to files containing Prolog rules
from .family import (FAMILY_RULES_BASE_PATH,
                     FAMILY_RULES_DERIVED_PATH)
from .friends import (FRIENDSHIP_RULES_PATH)
from .attributes import (ATTRIBUTE_RULES_PATH)

def get_database(*data_paths) -> Database:
    """
    Get a Prolog database with built-in rules.
    Add facts to the database from data_paths if provided.
    """
    db = Database(rules=[
        FAMILY_RULES_BASE_PATH, 
        FAMILY_RULES_DERIVED_PATH,
        FRIENDSHIP_RULES_PATH,
        ATTRIBUTE_RULES_PATH,
    ])

    print(f"Consulting facts from:")
    for path in data_paths:
        print(f"- {path}")
        db.consult(path)

    return db

from .person import db_generate_population
from .attributes import db_generate_attributes
from .friends import db_generate_friendships