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
            satisfying the predicate_template_list
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

    def _sample_atom(match_, bank) -> None:
        """Samples a choice from the `bank` for a <placeholder> indicated by `match_`."""

        # TODO sample for valid_only examples through atoms after the rest of the query is constructed
        if not bank:
            return None
        choice = rng.choice(bank)

        query_template_[i] = query_template_[i].replace(match_, f"\'{choice}\'")
        i_ = question_template_.index(match_)  # non-terminal index
        question_template_[i_] = question_template_[i_].replace(match_, choice)
        
        result[match_] = choice

    def _sample_predicate(match_, bank, alias_dict: dict = None) -> None:
        """Samples predicate <placeholder>s (i.e. relation/attribute types)"""
        choice = rng.choice(bank)

        i_ = question_template_.index(match_)
        question_template_[i_] = question_template_[i_].replace(match_, alias_dict[choice])
        query_template_[i] = query_template_[i].replace(match_, choice)

        # Map placeholder to the sampled predicate
        result[match_] = choice

    supports = {}
    for attribute_type in ATTRIBUTE_TYPES:
        supports[attribute_type] = set(r['Y'] for r in db.query(f"{attribute_type}(X, Y)"))
    # TODO handle the general case sampling from all possible jobs and hobbies when valid_only=False

    # Iterate through subquery templates
    # TODO sampling is done right-to-left, which might have to change with star-join support in templates
    for i in range(len(query_template_)-1, -1, -1):
        # Sample predicates
        if match := re.search(r"<relation>_(\d+)", query_template_[i]).group(0):
            assert match in question_template_
            _sample_predicate(match, bank=FAMILY_RELATION_EASY, alias_dict=FAMILY_RELATION_ALIAS)

        elif match := re.search(r"<relation_plural>_(\d+)", query_template_[i]).group(0):
            assert match in question_template_
            _sample_predicate(match, bank=FAMILY_RELATION_EASY, alias_dict=FAMILY_RELATION_PLURAL_ALIAS)

        elif match := re.search(r"<attribute_name>_(\d+)", query_template_[i]).group(0, 1):
            match_n, d = match
            assert match_n in question_template_
            _sample_predicate(match_n, bank=ATTRIBUTE_TYPES, alias_dict=ATTRIBUTE_TYPES)

            # if not valid_only:
                # if match_v := re.search(rf"<attribute_value>_{d}", query_template_[i]).group(0):
                #     assert match_v in question_template_
                #     # TODO sample from supported set vs all values vs postpone to the end with full query
                #     # TODO Fix bank definition
                #     _sample_atom(match_v, bank=supports[result[match_n]])
        
        # if not valid_only:
        # elif match := re.search(r"<name>_(\d+)", query_template_[i]).group(0):
        #     # TODO sample from all names vs supported names
        #     assert match in question_template_
        #     _sample_atom(match, bank=db.get_person_names())

        # TODO
        # else:
        #     raise NotImplementedError(f"Nothing to sample in {query_template_[i]}")
        
    if valid_only:
        # TODO stage 2 sampling names and attribute_values
        pass

        

    assert question_template_[-1] == "?", "the last term must be a question mark"

    # Avoid an extra space before the question mark by joining in the following fashion
    return result, " ".join(question_template_[:-1]) + question_template_[-1], query_template_
