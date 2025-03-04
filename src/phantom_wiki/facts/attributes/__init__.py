import logging
import time
from importlib.resources import files

from ..database import Database
from .generate_attributes import generate_hobbies, generate_jobs

ATTRIBUTE_RULES_PATH = files("phantom_wiki").joinpath("facts/attributes/rules.pl")

# TODO: add functionality to pass in CLI arguments


#
# Functionality to generate attributes for everyone in the database.
#
def db_generate_attributes(db: Database, seed: int) -> None:
    """
    Generate attributes for each person in the database.

    Args:
        db (Database): The database containing the facts.
        seed (int): Global seed for random number generator.

    Returns:
        None
    """
    start_time = time.time()
    names = db.get_person_names()
    jobs = generate_jobs(names, seed)
    hobbies = generate_hobbies(names, seed)

    # add the facts to the database
    facts = []
    for name in names:
        # add jobs
        job = jobs[name]
        facts.append(f'job("{name}", "{job}")')
        facts.append(f'attribute("{job}")')

        # add hobbies
        hobby = hobbies[name]
        facts.append(f'hobby("{name}", "{hobby}")')
        facts.append(f'attribute("{hobby}")')

    logging.info(f"Generated attributes for {len(names)} individuals in {time.time()-start_time:.3f}s.")
    db.add(*facts)
