"""
Functionality to parse a prolog query and return the difficulty of the query.
Example1:
>>>
[
    "husband('kanesha', Y_2)"
]

->

1

Example2:
>>>
[
    "husband(Y_2, Y_3)",
    "wife(Y_2, 'kanesha')"
]

->

2
"""

# TODO: change to relative  import
from phantom_wiki.facts.attributes.constants import ATTRIBUTE_TYPES
from phantom_wiki.facts.family.constants import FAMILY_RELATION_DIFFICULTY
from phantom_wiki.facts.friends.constants import FRIENDSHIP_RELATION


def parse_prolog_predicate(query: str) -> str:
    """
    Parse the list of prolog queries and return a list of predicates

    Args:
        query: the prolog query

    Returns:
        predicate: the predicate of the query
    """
    predicate = query.split("(")[0]
    return predicate


def calculate_query_difficulty(queries: list[str]) -> int:
    """
    for the chain join type of questions:
    parse the list of prolog queries and return the difficulty of the query

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
        if predicate in FRIENDSHIP_RELATION:
            difficulty += 1
        if predicate in ATTRIBUTE_TYPES:
            difficulty += 1
        if predicate == "aggregate_all":
            difficulty += 1
    return difficulty
