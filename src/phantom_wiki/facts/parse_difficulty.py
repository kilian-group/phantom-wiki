"""parse a prolog query and return the difficulty of the query

TODO: add docs

"""
# TODO: change to relative  import
from phantom_wiki.facts.attributes.constants import ATTRIBUTE_RELATION
from phantom_wiki.facts.family.constants import FAMILY_RELATION_DIFFICULTY


def parse_prolog_predicate(query: str) -> str:
    """
    Parse the prolog query and return the predicate

    Args:
        query: the prolog query 

    Returns:
        predicate: the predicate of the query
    """
    predicate = query.split("(")[0]
    return predicate

def parse_query_difficulty(queries: list[str]) -> int:
    """
    for the chain join type of questions: 
    parse the prolog query and return the difficulty of the query

    Args:
        queries: the prolog query 

    Returns:
        difficulty: the difficulty of the query
    """
    predicates = [parse_prolog_predicate(q) for q in queries]
    difficulty = 0
    for predicate in predicates:
        if predicate in FAMILY_RELATION_DIFFICULTY.keys():
            difficulty += FAMILY_RELATION_DIFFICULTY[predicate]
        if predicate in ATTRIBUTE_RELATION:
            difficulty += 1
        # TODO: not sure about the difficulty of this type because theoreticaly you should search all the articles
        if predicate == "aggregate_all":
            difficulty += 1
    return difficulty


