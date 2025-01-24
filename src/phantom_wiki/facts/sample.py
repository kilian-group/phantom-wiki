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
        query_ = ",,".join(query_template)
        for placeholder, sampled_value in query_assignments.items():
            query_ = query_.replace(placeholder, sampled_value)
        if use_atom_variables:
            for atom_placeholder_, atom_variable_ in atom_variables.items():
                query_ = query_.replace(atom_placeholder_, atom_variable_)
        return query_.split(",,")

    def _prepare_question():
        # Joining this way avoids space before the "?"
        assert question_template[-1] == "?"
        question_ = " ".join(question_template[:-1]) + question_template[-1]
        for placeholder, sampled_value in question_assignments.items():
            question_ = question_.replace(placeholder, sampled_value)

        return question_

    def _valid_result(result):
        # TODO this is a *hack* around the infinitely recursive Prolog queries
        return all(not isinstance(value, Variable) for value in result.values())

    query_assignments = {}  # Maps each <placeholder> to the sampled value
    atom_variables = {}  # Maps <placeholder> to the temporary variable
    question_assignments = {}

    supports = {}
    for attribute_type in ATTRIBUTE_TYPES:
        supports[attribute_type] = list(set(decode(r['Y']) for r in db.query(f"{attribute_type}(X, Y)")))
    name_bank = db.get_person_names()

    print(query_template)
    # Iterate through subquery templates
    # TODO sampling is done right-to-left, which might have to change with star-join support in templates
    for i in range(len(query_template) - 1, -1, -1):

        while True: # Repeat sampling until a valid result is found (if valid_only=True)
            if m := re.search(r"<attribute_name>_(\d+)", query_template[i]):
                match, d = m.group(0, 1)
                assert match in question_template
                _sample_predicate(match, bank=ATTRIBUTE_TYPES, alias_dict=ATTRIBUTE_ALIASES)

                if m := re.search(rf"<attribute_value>_{d}", query_template[i]):
                    match_v = m.group(0)
                    assert match_v in question_template
                    if valid_only:
                        _set_atom_variable(match_v)
                    else:
                        # TODO bank may include randomly generated attribute values (of matching type)
                        #  outside the universe
                        _sample_atom(match_v, bank=supports[query_assignments[match]])

            if m := re.search(r"<name>_(\d+)", query_template[i]):
                match = m.group(0)
                assert match in question_template
                if valid_only:
                    _set_atom_variable(match)
                else:
                    # TODO bank may include randomly generated names outside the universe
                    _sample_atom(match, bank=name_bank)

            if m := re.search(r"<relation>_(\d+)", query_template[i]):
                match = m.group(0)
                assert match in question_template
                if hard_mode:
                    _sample_predicate(match, bank=RELATION, alias_dict=RELATION_ALIAS)
                else: 
                    _sample_predicate(match, bank=RELATION_EASY, alias_dict=RELATION_ALIAS)
            
            if m := re.search(r"<relation_plural>_(\d+)", query_template[i]):
                match = m.group(0)
                assert match in question_template
                if hard_mode:
                    _sample_predicate(match, bank=RELATION, alias_dict=RELATION_PLURAL_ALIAS)
                else:
                    _sample_predicate(match, bank=RELATION_EASY, alias_dict=RELATION_PLURAL_ALIAS)

            if valid_only:
                q = _prepare_query(use_atom_variables=True)[i:]
                print("hello", q)
                query_results = list(itertools.islice(db.query(",".join(q)), 50))  # TODO limit choices for now
                print("gee", query_results)
                if query_results:
                    j = rng.choice(len(query_results))
                    choice = query_results[j]  # atom_variable -> sample
                    print(choice)
                    # TODO this is a hack to overcome the unfortunately infinite recursion-prone design of Prolog
                    #  predicates :(
                    if _valid_result(choice):
                        for atom_placeholder, atom_variable in atom_variables.items():
                            print(atom_placeholder, atom_variable)
                            query_assignments[atom_placeholder] = f"\"{decode(choice[atom_variable])}\""
                            # Atoms do not have aliases
                            question_assignments[atom_placeholder] = decode(choice[atom_variable])
                        break
            else:
                break

    question, query = _prepare_question(), _prepare_query()
    return query_assignments, question, query
