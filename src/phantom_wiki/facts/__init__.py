from ..utils.prolog import Database
from .family import (FAMILY_RULES_BASE_PATH,
                     FAMILY_RULES_DERIVED_PATH)

def get_database(*data_paths) -> Database:
    """
    Get a Prolog database with built-in rules.
    Add facts to the database from data_paths if provided.
    """
    db = Database(rules=[FAMILY_RULES_BASE_PATH, FAMILY_RULES_DERIVED_PATH])

    print(f"Consulting facts from:")
    for path in data_paths:
        print(f"- {path}")
        db.consult(path)

    return db
