"""Replaces placeholders in a question and query template with actual values derived from the database.

An example of sample function working:
############################################################################
# TODO clean up

["Who is", "the", "<relation>_3", "of", "the person whose", "<attribute_name>_1", "is",
"<attribute_value>_1", "?"],
["<relation>_3(Y_2, Y_4)", "<attribute_name>_1(Y_2, <attribute_value>_1)"],

->

(
    {"<attribute_name>_1": "age", "<relation>_3": "child"},
    "Who is the child of the person whose age is <attribute_value>_1 ?",
    ["child(Y_2, Y_4)", "age(Y_2, <attribute_value>_1)"], # TODO <attribute_value>_1 should also be sampled
)
############################################################################

Notes:

* valid_only will have to be implemented according to the tree structure of the template,
starting with the leaves and re-querying for validity when merging branches;
how should the backtracking work?
* maybe don't set any values for *atoms* and query for matches in that way

"""
import itertools
import re
from copy import copy
from numpy.random import Generator
from pyswip import Variable

from .attributes.constants import ATTRIBUTE_TYPES, ATTRIBUTE_ALIASES
from .database import Database
from .family.constants import FAMILY_RELATION_DIFFICULTY, FAMILY_RELATION_ALIAS, FAMILY_RELATION_PLURAL_ALIAS
from .friends.constants import FRIENDSHIP_RELATION, FRIENDSHIP_RELATION_ALIAS, FRIENDSHIP_RELATION_PLURAL_ALIAS
from ..utils import decode

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
            r: list[dict] = db.query(f"{query}(\"{key}\", A)")
            query_and_answer.extend((query, decode(result['A'])) for result in r)
        cache[key] = query_and_answer
        return query_and_answer


def sample(
    db: Database,
    question_template: list[str],
    query_template: list[str],
    rng: Generator,
    valid_only: bool = True,
    hard_mode: bool = False,
) -> list[dict, str, list[str]]:
    """Samples possible realizations of the question template and query template lists
    from the database `db`.

    Implements a backward sampling algorithm, where we hop between people in the universe
    creating a query.

    TODO: Implement valid_only

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
        hard_mode: whether to sample from hard relations 
            if True: we sample the relation predicates from all FAMILY_RELATIONS
            if False: we sample the relation predicates from FAMILY_RELATIONS with difficulty = 1
    Returns:
        * a dictionary mapping each placeholder to its realization,
        # TODO consider not returning these for simplicity and doing the replacement elsewhere?
        * the completed question as a single string,
        * the completed Prolog query as a list of Prolog statements,
    """

    query_template_ = copy(query_template)  # we will be modifying this list in place
    question_template_ = copy(question_template)  # we will be modifying this list in place

    atom_variables = {}  # Maps <placeholder> to the temporary variable if sampled value is unavailable
    query_assignments = {}  # Maps each <placeholder> to the sampled (value, alias) pair
    question_assignments = {}

    # Maintain a cache (dictionary) of person -> all possible attributes
    # e.g. "John" -> [("dob", "1990-01-01"), ("job", "teacher"), ("hobby", "reading"), ("hobby", "swimming"), ...]
    # Invariant: (attr name, attr value) pairs are unique
    person_name2attr_name_and_val: dict[str, list[tuple[str, str]]] = {}

    # Maintain a cache (dictionary) of person -> all possible relations
    # e.g. "John" -> [("child", "Alice"), ("child", "Bob"), ("friend", "Charlie"), ...]
    # Invariant: (relation, related person) pairs are unique
    person_name2relation_and_related: dict[str, list[tuple[str, str]]] = {}

    # Maintain a cache (dictionary) of attribute name -> all possible attribute values
    # e.g. "job" -> ["teacher", "doctor", "engineer", ...], "hobby" -> ["reading", "swimming", ...]
    attr_name2attr_vals = {}
    for attribute_type in ATTRIBUTE_TYPES: # NOTE: attribute_type and attribute_name are the same
        attr_name2attr_vals[attribute_type] = list(set(decode(r['Y']) for r in db.query(f"{attribute_type}(X, Y)")))
    person_name_bank: list[str] = db.get_person_names()

    # Possible queries in query template list:
    # 1. <attribute_name>_(\d+)(Y_\d+, <attribute_value>_\d+) --- only appears at the beginning or end of query template list
    # 2. <relation>_(\d+)(<name>_\d+, Y_\d+) --- only appears at end of query template list
    # 3. <relation>_(\d+)(Y_\d+, Y_\d+) --- does not appear at the end of query template list
    # 4. <relation>_(\d+)(Y_\d+) --- TERMINAL query: only appears at beginning of query template list
    # 5. <relation_plural>_(\d+)(Y_\d+) --- TERMINAL query: only appears at beginning of query template list

    for i in range(len(query_template_) - 1, -1, -1):
        # 1. <attribute_name>_(\d+)(Y_\d+, <attribute_value>_\d+) --- only appears at the beginning or end of query template list
        if m := re.search(r"(<attribute_name>_\d+)\((Y_\d+), (<attribute_value>_\d+)\)", query_template_[i]):
            # 0 group is the full match, 1 is the attribute_name, 2 is the Y_i placeholder, 3 is the attribute_value
            match, attribute_name, y_placeholder, attribute_value = m.group(0, 1, 2, 3)

            # This query becomes question "... the person whose <attribute_name> is <attribute_value>?"
            # or "What is the <attribute_name> of the ..."
            # In the first case, we start the graph traversal (randomly sample a person from the database)
            # In the second case, we continue the graph traversal (use the assignment of Y_i from the previous queries)
            # Then finding all possible (attr name, attr value) pairs for that person
            # Selecting a random pair and using it to fill in the query

            # a. If y_placeholder is already assigned, then we continue the graph traversal
            if y_placeholder in query_assignments:
                person_name_choice = query_assignments[y_placeholder]
            else:
                # Randomly sample a name from the database for the Y_i placeholder
                person_name_choice = rng.choice(person_name_bank)
                query_assignments[y_placeholder] = person_name_choice

            # b. Find all possible (attr name, attr value) pairs for the person
            attr_name_and_vals: list[tuple[str, str]] = get_vals_and_update_cache(
                cache=person_name2attr_name_and_val,
                key=person_name_choice,
                db=db,
                query_bank=ATTRIBUTE_TYPES,
            )
            
            if len(attr_name_and_vals) == 0:
                # If there are no attributes for this person, raise an exception
                raise ValueError(f"No attributes found for person {person_name_choice}")

            # c. Randomly choose an attribute name and value
            attribute_name_choice, attribute_value_choice = rng.choice(attr_name_and_vals)
            query_assignments[attribute_name] = attribute_name_choice
            query_assignments[attribute_value] = attribute_value_choice

            # Add the attribute name to the question assignments, could be an alias
            question_assignments[attribute_name] = ATTRIBUTE_ALIASES[attribute_name_choice]

        # 2. <relation>_(\d+)(<name>_\d+, Y_\d+) --- only appears at end of query template list
        elif m := re.search(r"(<relation>_\d+)\((<name>_\d+), (Y_\d+)\)", query_template_[i]):
            # 0 group is the full match, 1 is the relation, 2 is the name, 3 is the Y_i placeholder
            match, relation, name, y_placeholder = m.group(0, 1, 2, 3)
            
            # This query becomes question "... the <relation> of <name>?"
            # Start the graph traversal by randomly sampling a person from the database
            # Then finding all possible (relations, related) pairs for that person
            # Selecting a random pair and using it to fill in the query

            # a. Randomly sample a name from the database for the Y_i placeholder
            person_name_choice = rng.choice(person_name_bank)
            query_assignments[name] = person_name_choice

            # b. Find all possible (relation, related) pairs for the person
            relation_and_related: list[tuple[str, str]] = get_vals_and_update_cache(
                cache=person_name2relation_and_related,
                key=person_name_choice,
                db=db,
                query_bank=RELATION if hard_mode else RELATION_EASY,
            )

            if len(relation_and_related) == 0:
                # If there are no relations for this person, raise an exception
                raise ValueError(f"No relations found for person {person_name_choice}")

            # c. Randomly choose a relation and related person
            relation_choice, related_person_choice = rng.choice(relation_and_related)
            query_assignments[relation] = relation_choice
            query_assignments[y_placeholder] = related_person_choice

            # Add the relation to the question assignments, could be an alias
            question_assignments[relation] = RELATION_ALIAS[relation_choice]

            # NOTE: Raphael might be doing the right thing below, but I want to try a different approach
            # # 2. Sample a relation that exists for the name choice
            # while True: # TODO: We need to put a ceiling on the number of attempts -> if it fails, we backtrack
            #     if hard_mode: # Choose relation to test based on difficulty
            #         relation_choice = rng.choice(RELATION)
            #     else:
            #         relation_choice = rng.choice(RELATION_EASY)

            #     r: list[dict] = db.query(f"{relation_choice}({person_name_choice}, {y_placeholder})")
            #     if r: # If we have found a relation that exists for the name -> Done
            #         break
            
            # # Save relation and y_placeholder
            # query_assignments[relation] = relation_choice
            # query_assignments[y_placeholder] = decode(rng.choice(r)[y_placeholder])

        # 3. <relation>_(\d+)(Y_\d+, Y_\d+) --- does not appear at the end of query template list
        elif m := re.search(r"(<relation>_\d+)\((Y_\d+), (Y_\d+)\)", query_template_[i]):
            # 0 group is the full match, 1 is the relation, 2 is the name, 3 is the Y_i placeholder
            match, relation, y_placeholder_1, y_placeholder_2 = m.group(0, 1, 2, 3)
            
            # This query becomes question "... the <relation> of Y_1 of ...?"
            # Continue the graph traversal by using the assignment of Y_1 from the previous queries
            # Then finding all possible (relations, related) pairs for that person
            # Selecting a random pair and using it to fill in the query

            # a. Assume that y_placeholder_1 is already assigned
            assert y_placeholder_1 in query_assignments, f"{y_placeholder_1} should be assigned already: {query_template_[i]} in {query_template_}"
            assert y_placeholder_2 not in query_assignments, f"{y_placeholder_2} should not be assigned already: {query_template_[i]} in {query_template_}"
            person_1_name_choice = query_assignments[y_placeholder_1]

            # b. Find all possible (relation, related) pairs for the person
            relation_and_related: list[tuple[str, str]] = get_vals_and_update_cache(
                cache=person_name2relation_and_related,
                key=person_1_name_choice,
                db=db,
                query_bank=RELATION if hard_mode else RELATION_EASY,
            )

            if len(relation_and_related) == 0:
                # If there are no relations for this person, raise an exception
                raise ValueError(f"No relations found for person {person_1_name_choice}")
            
            # c. Randomly choose a relation and related person
            relation_choice, related_person_choice = rng.choice(relation_and_related)
            query_assignments[relation] = relation_choice
            query_assignments[y_placeholder_2] = related_person_choice

            # Add the relation to the question assignments, could be an alias
            question_assignments[relation] = RELATION_ALIAS[relation_choice]

            # NOTE: Raphael might be doing the right thing below, but I want to try a different approach
            # # 1. y_placeholder_1 is already assigned
            # name = query_assignments[y_placeholder_1]

            # # 2. Sample a relation that exists for the name
            # while True: # TODO: We need to put a ceiling on the number of attempts -> if it fails, we backtrack
            #     if hard_mode:
            #         relation_choice = rng.choice(RELATION)
            #     else:
            #         relation_choice = rng.choice(RELATION_EASY)

            #     r: list[dict] = db.query(f"{relation_choice}({name}, {y_placeholder_2})")
            #     if r:
            #         query_assignments[relation] = relation_choice
            #         break
            
            # query_assignments[relation] = relation_choice
            # query_assignments[y_placeholder_2] = decode(rng.choice(r)[y_placeholder_2])

        # 4. <relation>_(\d+)(Y_\d+) --- TERMINAL query: only appears at beginning of query template list
        elif m := re.search(r"(<relation>_\d+)\((Y_\d+)\)", query_template_[i]):
            # 0 group is the full match, 1 is the relation, 2 is the Y_i placeholder
            match, relation, y_placeholder = m.group(0, 1, 2)

            # This query becomes question "Who is the <relation> of ...?"
            # End the graph by using the assignment of Y_i from the previous queries
            # Then finding all possible (relations, related) pairs for that person
            # Selecting a random pair and using it to fill in the query

            # a. Assume that y_placeholder is already assigned
            assert y_placeholder in query_assignments, f"{y_placeholder} should be assigned already: {query_template_[i]} in {query_template_}"
            person_name_choice = query_assignments[y_placeholder]

            # b. Find all possible (relation, related) pairs for the person
            relation_and_related: list[tuple[str, str]] = get_vals_and_update_cache(
                cache=person_name2relation_and_related,
                key=person_name_choice,
                db=db,
                query_bank=RELATION if hard_mode else RELATION_EASY,
            )

            if len(relation_and_related) == 0:
                # If there are no relations for this person, raise an exception
                raise ValueError(f"No relations found for person {person_name_choice}")

            # c. Randomly choose a relation and related person
            # NOTE: The related_person_choice is 'one possible' answer of the question "Who is the ..."
            relation_choice, related_person_choice = rng.choice(relation_and_related)
            query_assignments[relation] = relation_choice

            # Add the relation to the question assignments, could be an alias
            question_assignments[relation] = RELATION_ALIAS[relation_choice]

        # 5. <relation_plural>_(\d+)(Y_\d+) --- TERMINAL query: only appears at beginning of query template list
        elif m := re.search(r"(<relation_plural>_\d+)\((Y_\d+)\)", query_template_[i]):
            # 0 group is the full match, 1 is the relation, 2 is the Y_i placeholder
            match, relation_plural, y_placeholder = m.group(0, 1, 2)

            # This query becomes question "Who are the <relation_plural> of ...?"
            # End the graph by using the assignment of Y_i from the previous queries
            # Then finding all possible (relations, related) pairs for that person
            # Selecting a random pair and using it to fill in the query

            # a. Assume that y_placeholder is already assigned
            assert y_placeholder in query_assignments, f"{y_placeholder} should be assigned already: {query_template_[i]} in {query_template_}"
            person_name_choice = query_assignments[y_placeholder]

            # b. Find all possible (relation, related) pairs for the person
            # NOTE: Use the plural bank
            relation_and_related: list[tuple[str, str]] = get_vals_and_update_cache(
                cache=person_name2relation_and_related,
                key=person_name_choice,
                db=db,
                query_bank=RELATION if hard_mode else RELATION_EASY,
            )

            if len(relation_and_related) == 0:
                # If there are no relations for this person, raise an exception
                raise ValueError(f"No relations found for person {person_name_choice}")
            
            # c. Randomly choose a relation and related person
            # NOTE: The related_person_choice is 'one possible' answer of the question "Who are the ..."
            relation_choice, related_person_choice = rng.choice(relation_and_related)
            query_assignments[relation_plural] = relation_choice

            # Add the relation to the question assignments, could be an alias
            question_assignments[relation_plural] = RELATION_PLURAL_ALIAS[relation_choice]

        else:
            # Template is not recognized
            raise ValueError(f"Template not recognized: {query_template_[i]} in {query_template_}")

    # We have found a valid query template, we need to prepare the query and question
    joined_query: str = ",,".join(query_template_)
    for placeholder, sampled_value in query_assignments.items():
        joined_query = joined_query.replace(placeholder, sampled_value)
    query: list[str] = joined_query.split(",,")

    # Last value in question template is always "?", so we join all but the last value and add the "?"
    # This avoids a space before the "?"
    question = " ".join(question_template_[:-1]) + question_template_[-1]
    for placeholder, sampled_value in question_assignments.items():
        question = question.replace(placeholder, sampled_value)

    # for i in range(len(question_template_)):
    #     if question_template_[i] in query_assignments:
    #         # TODO: Actually here, instead of putting the query assignment, we should put the alias of the query assignment
    #         # e.g. instead of putting "dob" we put "date of birth"
    #         # Maybe this is something we do earlier so we don't have to worry about it here. In Kamile's sample function 
    #         # she uses question_assignments to track the aliases of the query assignments
    #         question_template_[i] = query_assignments[question_template_[i]] 

    # Don't need this
    # for atom_placeholder_, atom_variable_ in atom_variables.items():
    #     query = query.replace(atom_placeholder_, atom_variable_)

    # NOTE: We talked about this with Anmol but we also noted that it is possible that there could be a lot of cycles in these questions.
    # This is something we need to test once everything is done -> if that is the case, we need to add check, e.g. name bank to ensure 
    # that we don’t revisit the same person more than once. Not too complicated but if unnecessary, then we shouldn't do it
    
    return query_assignments, question, query
    

def sample_forward(
    db: Database,
    question_template: list[str],
    query_template: list[str],
    rng: Generator,
    valid_only: bool = True,
    hard_mode: bool = False,
):
    """Samples possible realizations of the question template and query template lists
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
        hard_mode: whether to sample from hard relations 
            if True: we sample the relation predicates from all FAMILY_RELATIONS
            if False: we sample the relation predicates from FAMILY_RELATIONS with difficulty = 1
    Returns:
        * a dictionary mapping each placeholder to its realization,
        # TODO consider not returning these for simplicity and doing the replacement elsewhere?
        * the completed question as a single string,
        * the completed Prolog query as a list of Prolog statements,
    """

    def _sample_atom(match_, bank) -> None:
        """Samples a choice from the `bank` for a <placeholder> indicated by `match_`."""
        choice_ = rng.choice(bank)
        query_assignments[match_] = f"\"{choice_}\""
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
        return all(not isinstance(value, Variable) for value in result.values())

    query_assignments = {}  # Maps each <placeholder> to the sampled value

    supports = {}
    for attribute_type in ATTRIBUTE_TYPES:
        supports[attribute_type] = list(set(decode(r['Y']) for r in db.query(f"{attribute_type}(X, Y)")))
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
                if hard_mode:
                    _sample_predicate(match, bank=RELATION, alias_dict=RELATION_ALIAS)
                else: 
                    _sample_predicate(match, bank=RELATION_EASY, alias_dict=RELATION_ALIAS)

            if m := re.search(r"<relation_plural>_(\d+)", query_template_[i]):
                match = m.group(0)
                assert match in question_template_
                if hard_mode:
                    _sample_predicate(match, bank=RELATION, alias_dict=RELATION_PLURAL_ALIAS)
                else:
                    _sample_predicate(match, bank=RELATION_EASY, alias_dict=RELATION_PLURAL_ALIAS)

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
                        query_assignments[atom_placeholder] = f"\"{decode(choice[atom_variable])}\""
                        # Atoms do not have aliases
                        question_assignments[atom_placeholder] = decode(choice[atom_variable])
                    valid_result = True
                else:
                    valid_result = False
        else:
            valid_result = True

    if not valid_result:
        # This template may not have a valid placeholder assignment in this universe
        return None

    question, query = _prepare_question(), _prepare_query()
    return query_assignments, question, query
