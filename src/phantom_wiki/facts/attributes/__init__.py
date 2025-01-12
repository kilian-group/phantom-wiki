# standard imports
from argparse import ArgumentParser
import time
import logging

# phantom wiki functionality
from ..database import Database
from .constants import (ATTRIBUTE_FACT_TEMPLATES, 
                        ATTRIBUTE_TYPES)
from .generate import (generate_jobs,
                       generate_hobbies)
# resource containing the attribute rules
from importlib.resources import files
ATTRIBUTE_RULES_PATH = files("phantom_wiki").joinpath("facts/attributes/rules.pl")

# TODO: add functionality to pass in CLI arguments

# 
# Functionality to read the attributes for each person in the database.
# 
def get_attributes(db: Database, name: str):
    """
    Get attributes for each person in the database.
    """
    attributes = {}
    for attr in ATTRIBUTE_TYPES:
        query = f"{attr}(\'{name}\', X)"
        results = [result['X'] for result in db.query(query)]
        attributes[attr] = results
    return attributes

def get_attribute_facts(db: Database, names: list[str]) -> dict[str, list[str]]:
    """
    Get attribute facts for a list of names.
    """
    facts = {}
    for name in names:
        attributes = get_attributes(db, name)
        person_facts = []
        for attr, target in attributes.items():
            if target == []:
                continue
            attr_template = ATTRIBUTE_FACT_TEMPLATES[attr]
            fact = attr_template.replace("<subject>", name) + " " + ", ".join([str(s) for s in target]) + "."
            person_facts.append(fact)

        facts[name] = person_facts

    return facts

# 
# Functionality to generate attributes for everyone in the database.
# 
def db_generate_attributes(db: Database, args: ArgumentParser):
    """
    Generate attributes for each person in the database.

    Args:
        db (Database): The database containing the facts.
        args (ArgumentParser): The command line arguments.
    """
    start_time = time.time()
    names = db.get_person_names()
    jobs = generate_jobs(names, args.seed)
    hobbies = generate_hobbies(names, args.seed)

    # add the facts to the database
    facts = []
    for name in names:
        # add jobs
        job = jobs[name]
        facts.append(f"job(\'{name}\', \'{job}\')")
        facts.append(f"attribute(\'{job}\')")
        
        # add hobbies
        hobby = hobbies[name]
        facts.append(f"hobby(\'{name}\', \'{hobby}\')")
        facts.append(f"attribute(\'{hobby}\')")

    logging.info(f"Generated attributes for {len(names)} individuals in {time.time()-start_time:.3f}s.")
    db.add(*facts)
