"""Replaces placeholders in a question and query template with actual values derived from the database.

An example of sample function working:
############################################################################
# TODO clean up

[
    "Who is",
    "the",
    "<relation>_3",
    "of",
    "the person whose",
    "<attribute_name>_1",
    "is",
    "<attribute_value>_1",
    "?",
],    ,
["<relation>_3(Y_2, Y_4)", "<attribute_name>_1(Y_2, <attribute_value>_1)"],

-> 

(
    {"<attribute_name>_1": "age", "<relation>_3": "child"},
    "Who is the child of the person whose age is <attribute_value>_1 ?",
    ["child(Y_2, Y_4)", "age(Y_2, <attribute_value>_1)"],
)
############################################################################

Notes:

* valid_only will have to be implemented according to the tree structure of the template,
starting with the leaves and re-querying for validity when merging branches;
how should the backtracking work?
* maybe don't set any values for *atoms* and query for matches in that way

"""

import re
from copy import copy
from numpy.random import Generator

# TODO query from the database vs use the default constant
from .attributes.constants import ATTRIBUTE_TYPES
from .database import Database
from .family.constants import FAMILY_RELATION_DIFFICULTY, FAMILY_RELATION_ALIAS, FAMILY_RELATION_PLURAL_ALIAS

FAMILY_RELATION_EASY = [k for k, v in FAMILY_RELATION_DIFFICULTY.items() if v < 3]


def sample(
    db: Database,
    question_template: list[str],
    query_template: list[str],
    rng: Generator,
    valid_only: bool = True,
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
            satisfying the predicate_template_list with a non-empty answer
            if False: we uniformly sample from all possible prolog queries
            satsifying the predicate_template_list
    Returns:
        * a dictionary mapping each placeholder to its realization,
        # TODO consider not returning these for simplicity and doing the replacement elsewhere?
        * the completed question as a single string,
        * the completed Prolog query as a list of Prolog statements,
        # TODO None if valid_only is True and no valid query is found
    """
    query_template_ = copy(query_template)  # we will be modifying this list in place
    question_template_ = copy(question_template)  # we will be modifying this list in place

    # Mapping each <placeholder> to the sampled value
    result = {}

    def _search(pattern: str, query: str):
        match = re.search(pattern, query)
        if match:
            return match.group(0)
        return None

    def _sample_atom(bank: list[str], match: str, i: int):
        """Samples a choice from the `bank` for a placeholder indicated by `match`."""

        # TODO sample for valid_only examples through atoms after the rest of the query is constructed
        if not bank:
            return None
        choice = rng.choice(bank)

        query_template_[i] = query_template_[i].replace(match, f"\'{choice}\'")
        idx = question_template_.index(match) # nonterminal index
        question_template_[idx] = question_template_[idx].replace(match, choice)
        
        result[match] = choice

    def _sample_predicate(
        bank: list[str],
        match: str,
        i: int, # index of the subquery (i-th statement in the conjunction)? 
        alias_dict: dict = None, # predicate -> alias mapping
    ):  
        """Samples predicate <placeholder>s (i.e. relation or attribute types)"""
        tmp = copy(query_template_[i])
        # TODO postpone to after the rest of the query is formed
        if valid_only:
            support = []
            for predicate in bank:
                query_template_[i] = tmp.replace(match, predicate)
                #   instead will need to obtain a subquery
                if db.query(",".join(query_template_[i:])):
                    support.append(predicate)
            if not support:
                return None
            choice = rng.choice(support)
        else:
            choice = rng.choice(bank)

        idx = question_template_.index(match)
        question_template_[idx] = question_template_[idx].replace(match, alias_dict[choice])
        query_template_[i] = tmp.replace(match, choice)

        # replace the predicate name in the prolog query
        # TODO ???
        result[match] = choice

    # Iterate through subquery templates
    # TODO sampling is done right-to-left, which might have to change with star-join support in templates
    for i in range(len(query_template_)-1, -1, -1):
        # Sample possible values for Prolog atoms (such as names, attribute values)
        # using db.get_person_names() and db.get_attribute_values() since Prolog does not
        # have a good way to do this
        # NOTE: there must exist some atoms in order to sample a query

        if match := _search(r"(<name>_(\d+))", query_template_[i]):
            assert match in question_template_
            bank = db.get_person_names()
            _sample_atom(bank, match, i)

        if match := _search(r"(<attribute_name>_(\d+))", query_template_[i]):  
            # Process attribute names and values together
            assert match in question_template_

            # TODO make sure attribute name and value have a matching type
            _sample_predicate(ATTRIBUTE_TYPES, match, i, alias_dict=None)

        if match := _search(r"(<attribute_value>_(\d+))", query_template_[i]):
            assert match in question_template_

            # TODO sample matching attribute names and values from this
            bank = db.get_attribute_values()

            _sample_atom(bank, match, i)

        # now sample predicates
        if match := _search(r"(<(relation)>_(\d+))", query_template_[i]):  # relation predicates
            assert match in question_template_
            _sample_predicate(FAMILY_RELATION_EASY, match, i, alias_dict=FAMILY_RELATION_ALIAS)
        elif match := _search(r"(<(relation_plural)>_(\d+))", query_template_[i]):  
            # relation predicates
            assert match in question_template_
            _sample_predicate(FAMILY_RELATION_EASY, match, i, alias_dict=FAMILY_RELATION_PLURAL_ALIAS)
        else:
            raise NotImplementedError(f"Nothing to sample in {query_template_[i]}")

    assert question_template_[-1] == "?", "the last term must be a question mark"
    # avoid an extra space before the question mark by joining in the following fashion
    return result, " ".join(question_template_[:-1]) + question_template_[-1], query_template_
