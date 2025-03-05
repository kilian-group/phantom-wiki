"""
Replaces <relation>, <relation_plural>, <attribute_name>, <attribute_value>, <name> placeholders in a question
and query template with actual values derived from the database.

Example:

Input question template and query:
```python
    ["Who is", "the", "<relation>_3", "of", "the person whose", "<attribute_name>_1", "is",
    "<attribute_value>_1", "?"],
    ["<relation>_3(Y_2, Y_4)", "<attribute_name>_1(Y_2, <attribute_value>_1)"],
```

outputs one possible question and query that matches the provided template:
```python
(
    "Who is the child of the person whose age is 10?",
    ["child(Y_2, Y_4)", "age(Y_2, "10")"]
)
```
"""
import itertools
import re
from copy import copy

from numpy.random import Generator
from pyswip import Variable

from ..utils import decode
from .attributes.constants import ATTRIBUTE_ALIASES, ATTRIBUTE_TYPES
from .database import Database
from .family.constants import FAMILY_RELATION_ALIAS, FAMILY_RELATION_DIFFICULTY, FAMILY_RELATION_PLURAL_ALIAS
from .friends.constants import (
    FRIENDSHIP_RELATION,
    FRIENDSHIP_RELATION_ALIAS,
    FRIENDSHIP_RELATION_PLURAL_ALIAS,
)

FAMILY_RELATION_EASY = [k for k, v in FAMILY_RELATION_DIFFICULTY.items() if v < 2]
FAMILY_RELATIONS = [k for k, v in FAMILY_RELATION_DIFFICULTY.items()]

RELATION_ALIAS = FAMILY_RELATION_ALIAS | FRIENDSHIP_RELATION_ALIAS
RELATION_PLURAL_ALIAS = FAMILY_RELATION_PLURAL_ALIAS | FRIENDSHIP_RELATION_PLURAL_ALIAS

RELATION_EASY = FAMILY_RELATION_EASY + FRIENDSHIP_RELATION
RELATION = FAMILY_RELATIONS + FRIENDSHIP_RELATION


def get_vals_and_update_cache(
    cache: dict[str, list[tuple[str, str]]],
    key: str,
    db: Database,
    query_bank: list[str],
) -> list[tuple[str, str]]:
    """
    Returns the values for a key from the cache if it exists
    Otherwise queries the database `db` with `"query(key, A)"` for all `query` in `query_bank` and returns
    the list of `(query, value of A)`, after updating the cache.

    Args:
        cache: a dictionary mapping keys to lists of values
        key: the key to query the cache with
        db: the Prolog database to query
        query_bank: a list of Prolog queries to query the database with

    Returns:
        List of `(query, value of A)` pairs
    """
    if key in cache:
        return cache[key]
    else:
        # Query the database with this key for all possible query
        query_and_answer = []
        for query in query_bank:
            r: list[dict] = db.query(f'{query}("{key}", A)')
            query_and_answer.extend((query, decode(result["A"])) for result in r)
        cache[key] = query_and_answer
        return query_and_answer


def add_to_atom_assignments(atom_assignments: dict[str, str], new_atom_val: str) -> str:
    """
    Adds a new atom variable to the atom_assignments dictionary with `new_atom_val` value.

    Returns the new atom variable.
    """
    new_atom = f"A_{len(atom_assignments)}"
    atom_assignments[new_atom] = new_atom_val
    return new_atom


def process__attr_name__Y__attr_val(
    m: re.Match,
    query_assignments: dict[str, str],
    question_assignments: dict[str, str],
    atom_assignments: dict[str, str],
    rng: Generator,
    db: Database,
    person_name_bank: list[str],
    person_name2attr_name_and_val: dict[str, list[tuple[str, str]]],
) -> bool:
    r"""
    Processes <attribute_name>_(\d+)(Y_\d+, <attribute_value>_\d+) ---
        only appears at the beginning or end of query template list

    Returns True if the processing is successful, False otherwise
    """

    # 0 group is the full match, 1 is the attribute_name, 2 is the Y_i placeholder, 3 is the attribute_value
    match, attribute_name, y_placeholder, attribute_value = m.group(0, 1, 2, 3)

    # This query becomes question "... the person whose <attribute_name> is <attribute_value>?"
    # or "What is the <attribute_name> of the ..."
    # In the first case, we start the graph traversal (randomly sample a person from the database)
    # In the second case, we continue the graph traversal (use the assignment of Y_i from the previous
    # queries)
    # Then finding all possible (attr name, attr value) pairs for that person
    # Selecting a random pair and using it to fill in the query

    # a. If y_placeholder is already assigned, then we continue the graph traversal
    if y_placeholder in query_assignments:
        person_name_choice = atom_assignments[query_assignments[y_placeholder]]
    else:
        # Randomly sample a name from the database for the Y_i placeholder
        # Create new atom variable for the person name
        person_name_choice = rng.choice(person_name_bank)
        query_assignments[y_placeholder] = add_to_atom_assignments(
            atom_assignments, new_atom_val=person_name_choice
        )

    # b. Find all possible (attr name, attr value) pairs for the person
    attr_name_and_vals: list[tuple[str, str]] = get_vals_and_update_cache(
        cache=person_name2attr_name_and_val,
        key=person_name_choice,
        db=db,
        query_bank=ATTRIBUTE_TYPES,
    )

    if len(attr_name_and_vals) == 0:
        # If there are no attributes for this person, dead end in the graph traversal. Break and try again
        return False

    # c. Randomly choose an attribute name and value
    attribute_name_choice, attribute_value_choice = rng.choice(attr_name_and_vals)
    query_assignments[attribute_name] = attribute_name_choice
    # Realized values, in this case <attribute_value>, should be in quotes when creating the Prolog query
    query_assignments[attribute_value] = f'"{attribute_value_choice}"'

    # Add the attribute name and value to the question assignments, could be an alias
    question_assignments[attribute_name] = ATTRIBUTE_ALIASES[attribute_name_choice]
    question_assignments[attribute_value] = attribute_value_choice
    return True


def process__relation__name__Y(
    m: re.Match,
    query_assignments: dict[str, str],
    question_assignments: dict[str, str],
    atom_assignments: dict[str, str],
    rng: Generator,
    db: Database,
    person_name_bank: list[str],
    person_name2relation_and_related: dict[str, list[tuple[str, str]]],
    relation_bank: list[str],
) -> bool:
    r"""
    Processes <relation>_(\d+)(<name>_\d+, Y_\d+) --- only appears at end of query template list

    Returns True if the processing is successful, False otherwise
    """
    # 0 group is the full match, 1 is the relation, 2 is the name, 3 is the Y_i placeholder
    match, relation, name, y_placeholder = m.group(0, 1, 2, 3)

    # This query becomes question "... the <relation> of <name>?"
    # Start the graph traversal by randomly sampling a person from the database
    # Then finding all possible (relations, related) pairs for that person
    # Selecting a random pair and using it to fill in the query

    # a. Randomly sample a name from the database for the <name> placeholder
    person_name_choice = rng.choice(person_name_bank)
    # Realized values, in this case <name>, should be in quotes when creating the Prolog query
    query_assignments[name] = f'"{person_name_choice}"'

    # b. Find all possible (relation, related) pairs for the person
    relation_and_related: list[tuple[str, str]] = get_vals_and_update_cache(
        cache=person_name2relation_and_related,
        key=person_name_choice,
        db=db,
        query_bank=relation_bank,
    )

    if len(relation_and_related) == 0:
        # If there are no relations for this person, dead end in the graph traversal. Break and try again
        return False

    # c. Randomly choose a relation and related person
    relation_choice, related_person_choice = rng.choice(relation_and_related)
    query_assignments[relation] = relation_choice

    # Create new atom variable for the related person name
    query_assignments[y_placeholder] = add_to_atom_assignments(
        atom_assignments, new_atom_val=related_person_choice
    )

    # Add the relation to the question assignments, could be an alias
    question_assignments[relation] = RELATION_ALIAS[relation_choice]
    question_assignments[name] = person_name_choice
    return True


def process__relation__Y__Y(
    m: re.Match,
    query_assignments: dict[str, str],
    question_assignments: dict[str, str],
    atom_assignments: dict[str, str],
    rng: Generator,
    db: Database,
    person_name2relation_and_related: dict[str, list[tuple[str, str]]],
    relation_bank: list[str],
) -> bool:
    r"""
    Processes <relation>_(\d+)(Y_\d+, Y_\d+) --- does not appear at the end of query template list

    Returns True if the processing is successful, False otherwise
    """
    # 0 group is the full match, 1 is the relation, 2 is the Y_i placeholder, 3 is the Y_j placeholder
    match, relation, y_placeholder_1, y_placeholder_2 = m.group(0, 1, 2, 3)

    # This query becomes question "... the <relation> of Y_1 of ...?"
    # Continue the graph traversal by using the assignment of Y_1 from the previous queries
    # Then finding all possible (relations, related) pairs for that person
    # Selecting a random pair and using it to fill in the query

    # a. Assume that y_placeholder_1 is already assigned
    assert y_placeholder_1 in query_assignments, f"{y_placeholder_1} should be assigned already"
    assert y_placeholder_2 not in query_assignments, f"{y_placeholder_2} should not be assigned already"

    person_1_name_choice = atom_assignments[query_assignments[y_placeholder_1]]

    # b. Find all possible (relation, related) pairs for the person
    relation_and_related: list[tuple[str, str]] = get_vals_and_update_cache(
        cache=person_name2relation_and_related,
        key=person_1_name_choice,
        db=db,
        query_bank=relation_bank,
    )

    if len(relation_and_related) == 0:
        # If there are no relations for this person, dead end in the graph traversal. Break and try again
        return False

    # c. Randomly choose a relation and related person
    relation_choice, related_person_choice = rng.choice(relation_and_related)
    query_assignments[relation] = relation_choice

    # Create new atom variable for the related person name
    query_assignments[y_placeholder_2] = add_to_atom_assignments(
        atom_assignments, new_atom_val=related_person_choice
    )

    # Add the relation to the question assignments, could be an alias
    question_assignments[relation] = RELATION_ALIAS[relation_choice]
    return True


def process__attr_name__Y__Y(
    m: re.Match,
    query_assignments: dict[str, str],
    question_assignments: dict[str, str],
    atom_assignments: dict[str, str],
    rng: Generator,
    db: Database,
    person_name2attr_name_and_val: dict[str, list[tuple[str, str]]],
) -> bool:
    r"""
    Processes <attribute_name>_(\d+)(Y_\d+, Y_\d+) --- TERMINAL query: only appears at end of query template
    list

    Returns True if the processing is successful, False otherwise
    """
    # 0 group is the full match, 1 is the attribute_name, 2 is the Y_i placeholder, 3 is the Y_i placeholder
    match, attribute_name, y_placeholder_1, y_placeholder_2 = m.group(0, 1, 2, 3)

    # This query becomes question "What is the <attribute_name> of the ...?"
    # End the graph traversal by using the assignment of Y_i from the previous queries
    # Then finding all possible (attr name, attr value) pairs for that person
    # Selecting a random pair and using it to fill in the query

    # a. Assume that y_placeholder_1 is already assigned
    assert y_placeholder_1 in query_assignments, f"{y_placeholder_1} should be assigned already"
    assert y_placeholder_2 not in query_assignments, f"{y_placeholder_2} should not be assigned already"

    person_name_choice = atom_assignments[query_assignments[y_placeholder_1]]

    # b. Find all possible (attr name, attr value) pairs for the person
    attr_name_and_vals: list[tuple[str, str]] = get_vals_and_update_cache(
        cache=person_name2attr_name_and_val,
        key=person_name_choice,
        db=db,
        query_bank=ATTRIBUTE_TYPES,
    )

    if len(attr_name_and_vals) == 0:
        # If there are no attributes for this person, dead end in the graph traversal. Break and try again
        return False

    # c. Randomly choose an attribute name and value
    # NOTE: The attribute_value_choice is 'one possible' answer of the question "What is the ..."
    attribute_name_choice, attribute_value_choice = rng.choice(attr_name_and_vals)
    query_assignments[attribute_name] = attribute_name_choice

    # Add the attribute name and value to the question assignments, could be an alias
    question_assignments[attribute_name] = ATTRIBUTE_ALIASES[attribute_name_choice]
    return True


def process__agg__relation_plural__name__Y(
    m: re.Match,
    query_assignments: dict[str, str],
    question_assignments: dict[str, str],
    atom_assignments: dict[str, str],
    rng: Generator,
    db: Database,
    person_name_bank: list[str],
    person_name2relation_and_related: dict[str, list[tuple[str, str]]],
    relation_bank: list[str],
) -> bool:
    r"""
    Processes
        aggregate_all\(count, distinct\((<relation_plural>_\d+)\((<name>_\d+), (Y_\d+)\)\), (Count_\d+)\)
        --- TERMINAL query: only appears at end of query template list

    Returns True if the processing is successful, False otherwise
    """
    # 0 group is the full match, 1 is the relation, 2 is the name, 3 is the Y_i placeholder, 4 is the
    # Count_i placeholder
    match, relation_plural, name, y_placeholder, count_placeholder = m.group(0, 1, 2, 3, 4)

    # This query becomes question "How many <relation_plural> does <name> have?"
    # Start the graph traversal by randomly sampling a person from the database
    # Then finding all possible (relations, related) pairs for that person
    # Selecting a random pair and using it to fill in the query

    # a. Randomly sample a name from the database for the <name> placeholder
    person_name_choice = rng.choice(person_name_bank)
    # Realized values, in this case <name>, should be in quotes when creating the Prolog query
    query_assignments[name] = f'"{person_name_choice}"'

    # b. Find all possible (relation, related) pairs for the person
    relation_and_related: list[tuple[str, str]] = get_vals_and_update_cache(
        cache=person_name2relation_and_related,
        key=person_name_choice,
        db=db,
        query_bank=relation_bank,
    )

    if len(relation_and_related) == 0:
        # If there are no relations for this person, dead end in the graph traversal. Break and try again
        return False

    # c. Randomly choose a relation and related person
    # NOTE: The related_person_choice is 'one possible' answer of the question "How many ..."
    relation_choice, related_person_choice = rng.choice(relation_and_related)
    query_assignments[relation_plural] = relation_choice

    # Add the relation to the question assignments, could be an alias
    question_assignments[relation_plural] = RELATION_PLURAL_ALIAS[relation_choice]
    question_assignments[name] = person_name_choice
    return True


def process__agg__relation_plural__Y__Y(
    m: re.Match,
    query_assignments: dict[str, str],
    question_assignments: dict[str, str],
    atom_assignments: dict[str, str],
    rng: Generator,
    db: Database,
    person_name2relation_and_related: dict[str, list[tuple[str, str]]],
    relation_bank: list[str],
) -> bool:
    r"""
    Processes aggregate_all\(count, distinct\((<relation_plural>_\d+)\((Y_\d+), (Y_\d+)\)\), (Count_\d+)\)
        --- TERMINAL query: only appears at end of query template list

    Args:
        m: TODO
        query_assignments: TODO
        ...


    Returns True if the processing is successful, False otherwise
    """

    # 0 group is the full match, 1 is the relation, 2 is the Y_i placeholder, 3 is the Y_j placeholder, 4 is
    # the Count_i placeholder
    match, relation_plural, y_placeholder_1, y_placeholder_2, count_placeholder = m.group(0, 1, 2, 3, 4)

    # This query becomes question "How many <relation_plural> does the ...?"
    # Continue the graph traversal by using the assignment of Y_i from the previous queries
    # Then finding all possible (relations, related) pairs for that person
    # Selecting a random pair and using it to fill in the query

    # a. Assume that y_placeholder_1 is already assigned
    assert y_placeholder_1 in query_assignments, f"{y_placeholder_1} should be assigned already"
    assert y_placeholder_2 not in query_assignments, f"{y_placeholder_2} should not be assigned already"

    person_1_name_choice = atom_assignments[query_assignments[y_placeholder_1]]

    # b. Find all possible (relation, related) pairs for the person
    relation_and_related: list[tuple[str, str]] = get_vals_and_update_cache(
        cache=person_name2relation_and_related,
        key=person_1_name_choice,
        db=db,
        query_bank=relation_bank,
    )

    if len(relation_and_related) == 0:
        # If there are no relations for this person, dead end in the graph traversal. Break and try again
        return False

    # c. Randomly choose a relation and related person
    # NOTE: The related_person_choice is 'one possible' answer of the question "How many ..."
    relation_choice, related_person_choice = rng.choice(relation_and_related)
    query_assignments[relation_plural] = relation_choice

    # Create new atom variable for the related person name
    query_assignments[y_placeholder_2] = add_to_atom_assignments(
        atom_assignments, new_atom_val=related_person_choice
    )

    # Add the relation to the question assignments, could be an alias
    question_assignments[relation_plural] = RELATION_PLURAL_ALIAS[relation_choice]
    return True


def sample_question(
    question_template: list[str],
    query_template: list[str],
    rng: Generator,
    db: Database,
    person_name_bank: list[str],
    person_name2attr_name_and_val: dict[str, list[tuple[str, str]]],
    person_name2relation_and_related: dict[str, list[tuple[str, str]]],
    easy_mode: bool = False,
    num_sampling_attempts: int = 100,
) -> list[str, list[str]]:
    """
    Samples possible realizations of the question template and query template lists
    from the database `db`.

    Implements a random walk over the universe of people to create a query.
    Equivalent to chaining the queries in the query template list "backwards", i.e. realizing
    values of the placeholders in the query in a reverse order.

    Args:
        question_template (list[str]): question template as list of CFG terminals containing <placeholder>s
        query_template (list[str]): query template as a list of Prolog statements containing <placeholder>s
        rng (`Generator`): random number generator
        db (`Database`): the Prolog database to sample from
        person_name_bank (list[str]): list of all person names in the database
        person_name2attr_name_and_val (dict[str, list[tuple[str, str]]]): cache of person -> all possible
        (attr name, attr value) pairs
            e.g. "John" -> [("dob", "1990-01-01"), ("job", "teacher"), ("hobby", "reading"),
            ("hobby", "swimming"), ...]
            NOTE: Invariant: (attr name, attr value) pairs are unique
        person_name2relation_and_related (dict[str, list[tuple[str, str]]]): cache of person -> all possible
        (relation, related person) pairs
            e.g. "John" -> [("child", "Alice"), ("child", "Bob"), ("friend", "Charlie"), ...]
            NOTE: Invariant: (relation, related person) pairs are unique
        easy_mode: whether to sample from easy relations
            if False: we sample the relation predicates from all FAMILY_RELATIONS
            if True: we sample the relation predicates from FAMILY_RELATIONS with difficulty = 1
        num_samplng_attempts (int): number of attempts to sample a valid question
    Returns:
        * the completed question as a single string,
        * the completed Prolog query as a list of Prolog statements,
    """

    atom_assignments: dict[str, str] = {}  # Maps temporary variable A_i to the sampled value
    query_assignments: dict[
        str, str
    ] = (
        {}
    )  # Maps placeholder Y_i to the temporary variable A_i (or sampled value in case of terminal question)
    question_assignments: dict[str, str] = {}

    valid_result = False
    n_attempts = 0
    while not valid_result and n_attempts < num_sampling_attempts:
        n_attempts += 1

        # Reinitialize the assignments for each new attempt
        atom_assignments = {}
        query_assignments = {}
        question_assignments = {}

        # Possible queries in query template list:
        # 1. <attribute_name>_(\d+)(Y_\d+, <attribute_value>_\d+)
        #   --- only appears at the beginning or end of query template list
        # 2. <relation>_(\d+)(<name>_\d+, Y_\d+)
        #   --- only appears at end of query template list
        # 3. <relation>_(\d+)(Y_\d+, Y_\d+)
        #   --- does not appear at the end of query template list
        # 4. <attribute_name>_(\d+)(Y_\d+, Y_\d+)
        #   --- TERMINAL query: only appears at end of query template list
        # 5. aggregate_all\(count, distinct\((<relation_plural>_\d+)\((<name>_\d+), (Y_\d+)\)\), (Count_\d+)\)
        #   --- TERMINAL query: only appears at end of query template list
        # 6. aggregate_all\(count, distinct\((<relation_plural>_\d+)\((Y_\d+), (Y_\d+)\)\), (Count_\d+)\)
        #   --- TERMINAL query: only appears at end of query template list

        for i in range(len(query_template) - 1, -1, -1):
            # NOTE: Invariances:
            # - Every value of assignments[Y_i] that is an atom variable (A_i) should be a key in
            #   atom_assignments

            relation_bank = RELATION_EASY if easy_mode else RELATION

            # 1. <attribute_name>_(\d+)(Y_\d+, <attribute_value>_\d+)
            # -- only appears at the beginning or end of query template list
            if m := re.search(
                r"(<attribute_name>_\d+)\((Y_\d+), (<attribute_value>_\d+)\)", query_template[i]
            ):
                is_success = process__attr_name__Y__attr_val(
                    m,
                    query_assignments,
                    question_assignments,
                    atom_assignments,
                    rng,
                    db,
                    person_name_bank,
                    person_name2attr_name_and_val,
                )
                if not is_success:
                    break

            # 2. <relation>_(\d+)(<name>_\d+, Y_\d+) --- only appears at end of query template list
            elif m := re.search(r"(<relation>_\d+)\((<name>_\d+), (Y_\d+)\)", query_template[i]):
                is_success = process__relation__name__Y(
                    m,
                    query_assignments,
                    question_assignments,
                    atom_assignments,
                    rng,
                    db,
                    person_name_bank,
                    person_name2relation_and_related,
                    relation_bank,
                )
                if not is_success:
                    break

            # 3. <relation>_(\d+)(Y_\d+, Y_\d+) --- does not appear at the end of query template list
            elif m := re.search(r"(<relation>_\d+)\((Y_\d+), (Y_\d+)\)", query_template[i]):
                is_success = process__relation__Y__Y(
                    m,
                    query_assignments,
                    question_assignments,
                    atom_assignments,
                    rng,
                    db,
                    person_name2relation_and_related,
                    relation_bank,
                )
                if not is_success:
                    break

            # 4. <attribute_name>_(\d+)(Y_\d+, Y_\d+)
            # --- TERMINAL query: only appears at end of query template list
            elif m := re.search(r"(<attribute_name>_\d+)\((Y_\d+), (Y_\d+)\)", query_template[i]):
                is_success = process__attr_name__Y__Y(
                    m,
                    query_assignments,
                    question_assignments,
                    atom_assignments,
                    rng,
                    db,
                    person_name2attr_name_and_val,
                )
                if not is_success:
                    break

            # 5. aggregate_all\(count, distinct\((<relation_plural>_\d+)\((<name>_\d+), (Y_\d+)\)\),
            # (Count_\d+)\)
            # --- TERMINAL query: only appears at end of query template list
            elif m := re.search(
                r"aggregate_all"
                r"\(count, distinct\((<relation_plural>_\d+)\((<name>_\d+), (Y_\d+)\)\), (Count_\d+)\)",
                query_template[i],
            ):
                is_success = process__agg__relation_plural__name__Y(
                    m,
                    query_assignments,
                    question_assignments,
                    atom_assignments,
                    rng,
                    db,
                    person_name_bank,
                    person_name2relation_and_related,
                    relation_bank,
                )
                if not is_success:
                    break

            # 6. aggregate_all\(count, distinct\((<relation_plural>_\d+)\((Y_\d+), (Y_\d+)\)\), (Count_\d+)\)
            # --- TERMINAL query: only appears at end of query template list
            elif m := re.search(
                r"aggregate_all"
                r"\(count, distinct\((<relation_plural>_\d+)\((Y_\d+), (Y_\d+)\)\), (Count_\d+)\)",
                query_template[i],
            ):
                is_success = process__agg__relation_plural__Y__Y(
                    m,
                    query_assignments,
                    question_assignments,
                    atom_assignments,
                    rng,
                    db,
                    person_name2relation_and_related,
                    relation_bank,
                )
                if not is_success:
                    break

            else:
                # Template is not recognized
                raise ValueError(f"Template not recognized: {query_template[i]} in {query_template}")

        # If we reached the end of the loop, we have a valid query template and can exit the while loop
        if i == 0:
            valid_result = True

    # We have found a valid query template, we need to prepare the query and question
    # print(f"{query_template_=}")
    joined_query: str = ",,".join(query_template)  # join by ,, because , is used in Prolog queries
    for placeholder, sampled_value in query_assignments.items():
        # When placeholder is in atom_assignments, placeholder is Y_i and sampled_value is A_i
        # In these cases, we don't want to replace the placeholder with the sampled value
        # Retain Y_i in the query because output of sample() need Y_i
        if sampled_value not in atom_assignments:
            joined_query = joined_query.replace(placeholder, sampled_value)
    query: list[str] = joined_query.split(",,")
    # print(f"{query=}")

    # Last value in question template is always "?", so we join all but the last value and add the "?"
    # This avoids a space before the "?"
    # print(f"{question_template_=}")
    question = " ".join(question_template[:-1]) + question_template[-1]
    for placeholder, sampled_value in question_assignments.items():
        question = question.replace(placeholder, sampled_value)
    # print(f"{question=}")

    return question, query


def sample_forward(
    db: Database,
    question_template: list[str],
    query_template: list[str],
    rng: Generator,
    valid_only: bool = True,
    easy_mode: bool = False,
) -> tuple[str, list[str]]:
    """
    DEPRECATED: Use sample_question instead, which implements a (much faster) random walk over the universe
    of people to create a query.

    Samples possible realizations of the question template and query template lists
    from the database `db`.

    Implements a forward sampling strategy, where we construct a query first then check prolog for validity.

    Args:
        db: the Prolog database to sample from
        question_template: question template as list of CFG terminals containing <placeholder>s
        query_template: query template as a list of Prolog statements containing <placeholder>s
        rng: random number generator
        valid_only: whether to sample only valid realizations
            if True: we uniformly sample from the set of prolog queries
            satisfying the query_template with a non-empty answer
            if False: we uniformly sample from all possible prolog queries
            satisfying the query_template
        easy_mode: whether to sample from easy relations
            if False: we sample the relation predicates from all FAMILY_RELATIONS
            if True: we sample the relation predicates from FAMILY_RELATIONS with difficulty = 1
    Returns:
        * a dictionary mapping each placeholder to its realization,
        # TODO consider not returning these for simplicity and doing the replacement elsewhere?
        * the completed question as a single string,
        * the completed Prolog query as a list of Prolog statements,
    """

    def _sample_atom(match_, bank) -> None:
        """Samples a choice from the `bank` for a <placeholder> indicated by `match_`."""
        choice_ = rng.choice(bank)
        query_assignments[match_] = f'"{choice_}"'
        question_assignments[match_] = choice_

    def _set_atom_variable(match_) -> None:
        """Sets a Prolog variable for a <placeholder> indicated by `match_`."""
        # NOTE refactoring placeholders to not have brackets will set this to be obsolete.
        atom_variable_id = f"A_{len(atom_variables)}"
        atom_variables[match_] = atom_variable_id

    def _sample_predicate(match_, bank, alias_dict: dict = None) -> None:
        """Samples predicate <placeholder>s (i.e. relation/attribute types)"""
        choice_ = rng.choice(bank)
        query_assignments[match_] = choice_
        question_assignments[match_] = alias_dict[choice_] if alias_dict else choice_

    def _prepare_query(use_atom_variables=False):
        query_ = ",,".join(query_template_)
        for placeholder, sampled_value in query_assignments.items():
            query_ = query_.replace(placeholder, sampled_value)
        if use_atom_variables:
            for atom_placeholder_, atom_variable_ in atom_variables.items():
                query_ = query_.replace(atom_placeholder_, atom_variable_)
        return query_.split(",,")

    def _prepare_question():
        # Joining this way avoids space before the "?"
        assert question_template_[-1] == "?"
        question_ = " ".join(question_template_[:-1]) + question_template_[-1]
        for placeholder, sampled_value in question_assignments.items():
            question_ = question_.replace(placeholder, sampled_value)

        return question_

    def _valid_result(result):
        # TODO this is a *hack* around the infinitely recursive Prolog queries
        # the variable responsible for the aggregation query is allowed to be a Variable type
        result = all(
            not isinstance(value, Variable) for key, value in result.items() if key not in count_variables
        )
        return result

    query_assignments = {}  # Maps each <placeholder> to the sampled value

    supports = {}
    for attribute_type in ATTRIBUTE_TYPES:
        supports[attribute_type] = list({decode(r["Y"]) for r in db.query(f"{attribute_type}(X, Y)")})
    name_bank = db.get_person_names()

    valid_result = False
    n_attempts = 0
    while not valid_result and n_attempts < 100:  # TODO limit to 100 attempts per template for now
        n_attempts += 1

        query_template_ = copy(query_template)  # we will be modifying this list in place
        question_template_ = copy(question_template)  # we will be modifying this list in place

        atom_variables = {}  # Maps <placeholder> to the temporary variable if sampled value is unavailable
        query_assignments = {}  # Maps each <placeholder> to the sampled (value, alias) pair
        question_assignments = {}
        count_variables = []  # keep track of count variables
        # since e.g. aggregate_all(count, distinct(<relation_plural>_2(Y_3, Y_1)), Count_1) will return
        # 'Y_1':Variable

        # Iterate through subquery templates
        # TODO sampling is done right-to-left, which might have to change with star-join support in templates
        for i in range(len(query_template_) - 1, -1, -1):
            if m := re.search(r"<attribute_name>_(\d+)", query_template_[i]):
                match, d = m.group(0, 1)
                assert match in question_template_
                _sample_predicate(match, bank=ATTRIBUTE_TYPES, alias_dict=ATTRIBUTE_ALIASES)

                if m := re.search(rf"<attribute_value>_{d}", query_template_[i]):
                    match_v = m.group(0)
                    assert match_v in question_template_
                    if valid_only:
                        _set_atom_variable(match_v)
                    else:
                        # TODO bank may include randomly generated attribute values (of matching type)
                        #  outside the universe
                        _sample_atom(match_v, bank=supports[query_assignments[match]])

            if m := re.search(r"<name>_(\d+)", query_template_[i]):
                if "aggregate_all" not in query_template_[i]:  # skip aggregate queries
                    match = m.group(0)
                    assert match in question_template_
                    if valid_only:
                        _set_atom_variable(match)
                    else:
                        # TODO bank may include randomly generated names outside the universe
                        _sample_atom(match, bank=name_bank)

            if m := re.search(r"<relation>_(\d+)", query_template_[i]):
                match = m.group(0)
                assert match in question_template_
                if easy_mode:
                    _sample_predicate(match, bank=RELATION_EASY, alias_dict=RELATION_ALIAS)
                else:
                    _sample_predicate(match, bank=RELATION, alias_dict=RELATION_ALIAS)

            if m := re.search(r"<relation_plural>_(\d+)", query_template_[i]):
                match = m.group(0)
                assert match in question_template_
                # check if the query type is aggregation
                # For this query type, only the 3rd match can be a Variable once Prolog query returns
                if match_agg := re.findall(
                    r"aggregate_all"
                    r"\(count, distinct\((<relation_plural>_\d+)\((Y_\d+), (Y_\d+)\)\), (Count_\d+)\)",
                    query_template_[i],
                ):
                    count_variables.append(match_agg[0][2])
                # For this type of aggregation query, instantiate the atom in the 2nd match and allow the
                # 3rd match to be Variable
                elif match_agg := re.findall(
                    r"aggregate_all"
                    r"\(count, distinct\((<relation_plural>_\d+)\((<name>_\d+), (Y_\d+)\)\), (Count_\d+)\)",
                    query_template_[i],
                ):
                    count_variables.append(match_agg[0][2])
                    # hack to avoid returning a Variable type
                    _sample_atom(match_agg[0][1], bank=name_bank)
                if easy_mode:
                    _sample_predicate(match, bank=RELATION_EASY, alias_dict=RELATION_PLURAL_ALIAS)
                else:
                    _sample_predicate(match, bank=RELATION, alias_dict=RELATION_PLURAL_ALIAS)

        if valid_only:
            q = _prepare_query(use_atom_variables=True)
            query_results = list(itertools.islice(db.query(",".join(q)), 50))  # TODO limit choices for now
            if query_results:
                j = rng.choice(len(query_results))
                choice = query_results[j]  # atom_variable -> sample
                # TODO this is a hack to overcome the unfortunately infinite recursion-prone design of Prolog
                #  predicates :(
                if _valid_result(choice):
                    for atom_placeholder, atom_variable in atom_variables.items():
                        query_assignments[atom_placeholder] = f'"{decode(choice[atom_variable])}"'
                        # Atoms do not have aliases
                        question_assignments[atom_placeholder] = decode(choice[atom_variable])
                    valid_result = True
                else:
                    valid_result = False
        else:
            valid_result = True

    if not valid_result:
        if n_attempts >= 100:
            print(f"Failed to sample a valid query after {n_attempts} attempts.")
        # This template may not have a valid placeholder assignment in this universe
        return None

    question, query = _prepare_question(), _prepare_query()
    return question, query
