# imports for paths to Prolog rules
from .family import (FAMILY_RULES_BASE_PATH,
                     FAMILY_RULES_DERIVED_PATH)
from .attributes import (ATTRIBUTE_RULES_PATH)
# Functionality to get a Prolog database with built-in rules
from .database import Database
def get_database(*data_paths) -> Database:
    """
    Get a Prolog database with built-in rules.
    Add facts to the database from data_paths if provided.
    """
    db = Database(rules=[
        FAMILY_RULES_BASE_PATH, 
        FAMILY_RULES_DERIVED_PATH,
        ATTRIBUTE_RULES_PATH,
    ])

    print(f"Consulting facts from:")
    for path in data_paths:
        print(f"- {path}")
        db.consult(path)

    return db

# Imports for generating facts
from .attributes import db_generate_attributes
from .family import db_generate_family