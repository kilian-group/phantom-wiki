from ..database import Database

from .constants import (ATTRIBUTE_FACT_TEMPLATES, 
                        ATTRIBUTE_RELATION)
from .generate import (generate_jobs,
                       generate_hobbies)

# resource containing the attribute rules
from importlib.resources import files
ATTRIBUTE_RULES_PATH = files("phantom_wiki").joinpath("facts/attributes/rules.pl")


# 
# Functionality to read the attributes for each person in the database.
# 
def get_attributes(db: Database, name: str):
    """
    Get attributes for each person in the database.
    """
    attributes = {}
    for attr in ATTRIBUTE_RELATION:
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
def db_generate_attributes(db: Database, seed: int = 1):
    """
    Generate attributes for each person in the database.
    """
    names = db.get_names()
    jobs = generate_jobs(names, seed)
    hobbies = generate_hobbies(names, seed)

    # add the facts to the database
    facts = []
    for name in names:
        job = jobs[name]
        facts.append(f"job(\'{name}\', \'{job}\')")
        hobby = hobbies[name]
        facts.append(f"hobby(\'{name}\', \'{hobby}\')")
    db.add(*facts)
