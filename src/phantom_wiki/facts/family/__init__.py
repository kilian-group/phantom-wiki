from .constants import (FAMILY_FACT_TEMPLATES,
                        FAMILY_RELATION_EASY,
                        FAMILY_RELATION_HARD)
from .. import Database

def get_family_relationships(db: Database, name: str) -> dict:
    # TODO make sure a proper Prolog query is present for each template in FAMILY_FACT_TEMPLATES
    """
    Get the results for all family relations in 
    - FAMILY_RELATION_EASY
    - FAMILY_RELATION_HARD
    """
    relations = {}
    for relation in FAMILY_RELATION_EASY + FAMILY_RELATION_HARD:
        query = f"{relation}({name}, X)"
        results = [result['X'] for result in db.query(query)]
        relations[relation] = results

    return relations

def get_family_facts(db: Database, names: list[str]) -> dict[str, list[str]]:
    """
    Get family facts for a list of names.
    """
    # TODO: add an argument to regulate depth/complexity of the facts
    #   (e.g. how many (types of) relations to include)
    facts = {}
    for name in names:
        relations = get_family_relationships(db, name)

        person_facts = []
        for relation, target in relations.items():
            relation_template = FAMILY_FACT_TEMPLATES[relation]
            fact = relation_template.replace("<subject>", name) + " " + str(target) + "."
            person_facts.append(fact)

        facts[name] = person_facts

    return facts
