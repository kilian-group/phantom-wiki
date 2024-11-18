import re
from copy import copy

# import numpy generator type
from numpy.random import Generator

# possible attribute names
from ..facts.attributes.constants import ATTRIBUTE_RELATION
from ..facts.database import Database

#
# Begin WIP:
# we can move this to some file in phantom_wiki/facts/
#
# possible relations
from ..facts.family.constants import FAMILY_RELATION_EASY, FAMILY_RELATION_EASY_PLURALS, FAMILY_RELATION_EASY_PL2SG


def sample(
    db: Database,
    question_temp_list: list[str],
    query_temp_list: list[str],
    rng: Generator,
    valid_only: bool = True,
):
    """
    Samples possible realizations of the question_list and predicate_list from the database db.
    Example:
    >>> 
    # TODO:
    "Who is the <relation>_3 of the person whose <attribute_name>_1 is <attribute_value>_1 ?",
    "<relation>_3(Y_2, Y_4), <attribute_name>_1(Y_2, <attribute_value>_1)",

    -> 

    {"<relation>_3": "father", "<attribute_name>_1": "hobby", "<attribute_value>_1": "running"},



    Args:
        db: the prolog database to sample from
        question_template: a template for the question with <placeholder> 
        query_template: a template for the prolog query with <placeholder>
        rng: a random number generator
        valid_only: whether to sample only valid realizations
            if True: we uniformly sample from the set of prolog queries
            satisfying the predicate_template_list with a non-empty answer
            if False: we uniformly sample from all possible prolog queries
            satsifying the predicate_template_list
    Returns:
        a prolog query or
        None if valid_only is True and no valid query is found
    """
    print("55> question_temp_list: ", question_temp_list)
    print("56> query_temp_list: ", query_temp_list)

    query = copy(query_temp_list)  # we will be modifying this list in place
    question = copy(question_temp_list)  # 
    result = {}

    def search(pattern: str, query: str):
        match = re.search(pattern, query)
        if match:
            return match.group(1)
        return None

    def sample_atom(bank: list[str], i: int):
        # import pdb; pdb.set_trace()
        if not bank:
            return None
        choice = rng.choice(bank)
        query[i] = query_temp_list[i].replace(match, f"\'{choice}\'")
        idx = question.index(match)
        question[idx] = question[idx].replace(match, choice)
        result[match] = choice

    def sample_predicate(
        bank: list[str],
        match: str,
        i: int, # index of the query
        mapping: dict = None, # if we need to map the predicate names from plural forms to singular,
    ):
        # import pdb; pdb.set_trace()
        tmp = copy(query[i])
        if valid_only:
            support = []
            for predicate in bank:
                query[i] = tmp.replace(match, mapping[predicate] if mapping else predicate)
                if db.query(",".join(query[i:])):
                    support.append(predicate)
            if not support:
                return None
            choice = rng.choice(support)
        else:
            choice = rng.choice(bank)

        idx = question.index(match)
        question[idx] = question[idx].replace(match, choice)
        # if we need to map the predicate names in the quesion from singular forms to plural,
        # replace the corresponding plural form in the query
        query[i] = tmp.replace(match, mapping[choice] if mapping else choice)

        # replace the predicate name in the prolog query
        result[match] = choice

    for i in range(len(query)-1,-1,-1):
        # first sample prolog atoms (e.g., name, attribute values)
        # Prolog doesn't have a good way of retrieving all atoms,
        # so we must resort to db.get_names() and db.get_attribute_values()
        # NOTE: there must exist some atoms in order to sample a query
        if match := search(r"(<name>_(\d+))", query[i]):
            assert match in question
            bank = db.get_names()
            sample_atom(bank, i)
        if match := search(r"(<attribute_value>_(\d+))", query[i]):
            assert match in question
            bank = db.get_attribute_values()
            sample_atom(bank, i)

        # now sample predicates
        # NOTE: we also need to deal with the plural forms of the predicates
        if match := search(r"(<(relation)>_(\d+))", query[i]):  # relation predicates
            assert match in question
            sample_predicate(FAMILY_RELATION_EASY, match, i, mapping=None)
        elif match := search(r"(<(relation_plural)>_(\d+))", query[i]):  # relation predicates
            assert match in question
            sample_predicate(FAMILY_RELATION_EASY_PLURALS, match, i, mapping=FAMILY_RELATION_EASY_PL2SG)
        elif match := search(r"(<attribute_name>_(\d+))", query[i]):  # attribute predicates
            assert match in question
            sample_predicate(ATTRIBUTE_RELATION, match, i, mapping=None)

    return result, " ".join(question), query


#
# End WIP
#
