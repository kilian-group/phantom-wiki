"""Auto-generate inverse Prolog predicates for bidirectional anchor sampling.

For each relation R(X, Y), defines R_inverse(X, Y) :- R(Y, X).
For symmetric relations (where R(X,Y) ⟺ R(Y,X)), the inverse is the relation itself.
"""

import logging

from .database import Database
from .family.constants import FAMILY_RELATION_DIFFICULTY
from .friends.constants import FRIENDSHIP_RELATION

logger = logging.getLogger(__name__)

# Relations where R(X,Y) ⟺ R(Y,X) based on Prolog rule definitions.
# sibling: parent(X,A), parent(Y,A), X\=Y — symmetric
# married: parent(Child,X), parent(Child,Y), X\=Y — symmetric
# cousin: parent(X,A), parent(Y,B), sibling(A,B), X\=Y — symmetric
# friend: friend_(X,Y) ; friend_(Y,X) — symmetric
SYMMETRIC_RELATIONS = frozenset({"sibling", "married", "cousin", "friend"})

# All relation predicates used in question generation
ALL_RELATIONS = list(FAMILY_RELATION_DIFFICULTY.keys()) + list(FRIENDSHIP_RELATION)


# TODO: @anmolkabra: already defaults to ALL_RELATIONS, remove the optional None type hint
def build_inverse_relation_map(relation_list: list[str] | None = None) -> dict[str, str]:
    """Build a mapping from each relation to its inverse predicate name.

    For symmetric relations, the inverse name is the relation itself.
    For asymmetric relations, the inverse name is ``{relation}_inverse``.

    Args:
        relation_list: Relations to include. Defaults to ALL_RELATIONS.

    Returns:
        Dict mapping relation name to its inverse predicate name.
    """
    if relation_list is None:
        relation_list = ALL_RELATIONS
    inverse_map: dict[str, str] = {}
    for rel in relation_list:
        if rel in SYMMETRIC_RELATIONS:
            inverse_map[rel] = rel
        else:
            inverse_map[rel] = f"{rel}_inverse"
    return inverse_map


def register_inverse_predicates(
    db: Database, relation_list: list[str] | None = None
) -> dict[str, str]:
    """Assert inverse predicates into the Prolog database.

    For each asymmetric relation R, asserts the rule:
        ``R_inverse(X, Y) :- R(Y, X).``

    Symmetric relations do not need new predicates since their forward
    definition already handles both directions.

    Args:
        db: The Prolog database to register predicates in.
        relation_list: Relations to process. Defaults to ALL_RELATIONS.

    Returns:
        Dict mapping relation name to its inverse predicate name.
    """
    inverse_map = build_inverse_relation_map(relation_list)

    registered = []
    for rel, inv_name in inverse_map.items():
        if rel in SYMMETRIC_RELATIONS:
            continue
        # Declare as dynamic so assertz works
        db.define(f"{inv_name}/2")
        # Assert the inverse rule: inv(X, Y) :- rel(Y, X)
        db.add(f"({inv_name}(X, Y) :- {rel}(Y, X))")
        registered.append(inv_name)

    # TODO: @anmolkabra, why is this logging not showing to stdout
    # Might need to use logging.info instead of logger.info
    logger.info(
        "Registered %d inverse predicates (%d symmetric skipped)",
        len(registered),
        sum(1 for r in inverse_map if r in SYMMETRIC_RELATIONS),
    )
    return inverse_map


def get_inverse_name(relation: str) -> str:
    """Return the inverse predicate name for a relation.

    Args:
        relation: The forward relation name.

    Returns:
        The relation itself if symmetric, otherwise ``{relation}_inverse``.
    """
    if relation in SYMMETRIC_RELATIONS:
        return relation
    return f"{relation}_inverse"
