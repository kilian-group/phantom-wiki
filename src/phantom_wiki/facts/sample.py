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


def sample_WIP(
    db: Database,
    question_template: list[str],
    query_template: list[str],
    rng: Generator,
    valid_only: bool = True,
    hard_mode: bool = False,
) -> list[dict, str, list[str]]:
    """Samples possible realizations of the question template and query template lists
    from the database `db`.

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

    # supports is a dict from {job -> all_possible_jobs, dob -> all_possible_dobs, ...}
    supports = {}
    for attribute_type in ATTRIBUTE_TYPES:
        supports[attribute_type] = list(set(decode(r['Y']) for r in db.query(f"{attribute_type}(X, Y)")))
    name_bank = db.get_person_names()

    for i in range(len(query_template_) - 1, -1, -1):
        if m := re.search(r"(<attribute_name>_\d+)\((Y_\d+), (<attribute_value>_\d+)\)", query_template_[i]):
            # 0 group is the full match, 1 is the attribute_name, 2 is the Y_i placeholder, 3 is the attribute_value
            match, attribute_name, y_placeholder, attribute_value = m.group(0, 1, 2, 3)

            # 1. Randomly sample a name from the database for the Y_i placeholder
            name_choice = rng.choice(name_bank)
            query_assignments[y_placeholder] = name_choice

            # 2. Sample the attribute type. Everyone has a dob, job, etc. so we can sample
            # uniformly from the set of attribute types
            attribute_name_choice = rng.choice(ATTRIBUTE_TYPES)
            query_assignments[attribute_name] = attribute_name_choice
            # TODO: Do we need question_assignments dict?
            # question_assignments[match] = ATTRIBUTE_ALIASES[choice] if ATTRIBUTE_ALIASES else choice

            # 3. Now create a temporary variable for the attribute value
            # and query the db
            tmp_attribute_value_placeholder = f"A_{len(atom_variables)}"
            atom_variables[attribute_value] = tmp_attribute_value_placeholder
            r: list[dict] = db.query(f"{attribute_name_choice}({name_choice}, {tmp_attribute_value_placeholder})")
            if r:
                # 4. Randomly choose an attribute value from r
                attribute_value_choice: str = decode(rng.choice(r)[tmp_attribute_value_placeholder])
                query_assignments[attribute_value] = attribute_value_choice

        elif m := re.search(r"(<relation>_\d+)\((<name>_\d+), (Y_\d+)\)", query_template_[i]):
            # 0 group is the full match, 1 is the relation, 2 is the name, 3 is the Y_i placeholder
            match, relation, name, y_placeholder = m.group(0, 1, 2, 3)
            
            # 1. Sample the name
            name_choice = rng.choice(name_bank)
            query_assignments[name] = name_choice

            # 2. Sample a relation that exists for the name choice
            while True: # TODO: We need to put a ceiling on the number of attempts -> if it fails, we backtrack
                if hard_mode: # Choose relation to test based on difficulty
                    relation_choice = rng.choice(RELATION)
                else:
                    relation_choice = rng.choice(RELATION_EASY)

                r: list[dict] = db.query(f"{relation_choice}({name_choice}, {y_placeholder})")
                if r: # If we have found a relation that exists for the name -> Done
                    break
            
            # Save relation and y_placeholder
            query_assignments[relation] = relation_choice
            query_assignments[y_placeholder] = decode(rng.choice(r)[y_placeholder])

        elif m := re.search(r"(<relation>_\d+)\((Y_\d+), (Y_\d+)\)", query_template_[i]):
            # 0 group is the full match, 1 is the relation, 2 is the name, 3 is the Y_i placeholder
            match, relation, y_placeholder_1, y_placeholder_2 = m.group(0, 1, 2, 3)
            
            # 1. y_placeholder_1 is already assigned
            name = query_assignments[y_placeholder_1]

            # 2. Sample a relation that exists for the name
            while True: # TODO: We need to put a ceiling on the number of attempts -> if it fails, we backtrack
                if hard_mode:
                    relation_choice = rng.choice(RELATION)
                else:
                    relation_choice = rng.choice(RELATION_EASY)

                r: list[dict] = db.query(f"{relation_choice}({name}, {y_placeholder_2})")
                if r:
                    query_assignments[relation] = relation_choice
                    break
            
            query_assignments[relation] = relation_choice
            query_assignments[y_placeholder_2] = decode(rng.choice(r)[y_placeholder_2])

        elif m := re.search(r"<relation_plural>_(\d+)", query_template_[i]):
            raise ValueError("I don't know what this is and I don't know how to handle it.")
        
        else:
            raise ValueError("We have a bug -> we thought we were exhaustive and didn't think this was possible.")

        # TODO: If we didn't find something that worked -> back track
        # NOTE: This is why I said we should use a while loop, if we don't then we can't backtrack more than once since
        # for loops use iterators and we can't reset them. 

    # We have found a valid query template, we need to parse everything
    for i in range(len(question_template_)):
        if question_template_[i] in query_assignments:
            # TODO: Actually here, instead of putting the query assignment, we should put the alias of the query assignment
            # e.g. instead of putting "dob" we put "date of birth"
            # Maybe this is something we do earlier so we don't have to worry about it here. In Kamile's sample function 
            # she uses question_assignments to track the aliases of the query assignments
            question_template_[i] = query_assignments[question_template_[i]] 

    # From what I understand the output "query" is the list of queries
    query = ",,".join(query_template_)
    for placeholder, sampled_value in query_assignments.items():
        query = query.replace(placeholder, sampled_value)
    for atom_placeholder_, atom_variable_ in atom_variables.items():
        query = query.replace(atom_placeholder_, atom_variable_)

    return query_assignments, " ".join(question_template_), query
    

def sample(
    db: Database,
    question_template: list[str],
    query_template: list[str],
    rng: Generator,
    valid_only: bool = True,
    hard_mode: bool = False,
):
    # TODO output type
    """Samples possible realizations of the question template and query template lists
    from the database `db`.

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
