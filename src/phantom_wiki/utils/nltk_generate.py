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
from ..facts.family.constants import FAMILY_RELATION_EASY, FAMILY_RELATION_EASY_SG2PL


def sample(
    db: Database,
    question_template_list: list[str],
    predicate_template_list: list[str],
    rng: Generator,
    valid_only: bool = True,
):
    """
    Samples possible realizations of the question_list and predicate_list from the database db.
    Example:
    >>> ["Who is",
        "the",
        "<relation>_3",
        "of",
        "the person whose",
        "<attribute_name>_1",
        "is",
        "<attribute_value>_1",
        "?",
    ],
    ["<relation>_3(Y_2, Y_4)", "<attribute_name>_1(Y_2, <attribute_value>_1)."]

    father(anastasia, X)
    mother(anastasia, X)
    >>> ["How many", "<relation_plural>_4", "does", "the", "<relation>_2", "of", "<name>_1", "have?"],
    ["aggregate_all(count, <relation>_4(Y_3, Y_5), Count_5", "<relation>_2(<name>_1, Y_3)."],


    Args:
        db: the prolog database to sample from
        question_template_list: a list of words in question templates
        predicate_template_list: a list of predicate templates
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

    def search(pattern: str, query: str):
        match = re.search(pattern, query)
        if match:
            return match.group(1)
        return None

    def sample_from_bank(bank: list[str], rng: Generator):
        if not bank:
            return None
        choice = rng.choice(bank)
        query[i] = predicate_template_list[i].replace(match, choice)
        question_match_index = question_template_list.index(match)
        question[question_match_index] = choice
        result[match] = choice

    def get_support(
        predicate_name_list: list[str],
        match: str,
        tmp: str,
        # if we need to map the predicate names from plural forms to singular,
        mapping: dict = None,
    ):
        if valid_only:
            support = []
            for predicate in predicate_name_list:
                query[i] = tmp.replace(match, predicate)
                if db.query(",".join(query[i:])):
                    support.append(predicate)
            if not support:
                return None
            choice = rng.choice(support)
        else:
            choice = rng.choice(predicate_name_list)
        # if there is no mapping,
        # replace the predicate name in the question
        if mapping is None:
            question_match_index = question_template_list.index(match)
            question[question_match_index] = choice
        else:
            # if we need to map the predicate names in the quesion from singular forms to plural,
            # replace the corresponding plural form in the question
            question_match_index = question_template_list.index(match.replace("relation", "relation_plural"))
            question[question_match_index] = mapping[choice]

        # replace the predicate name in the prolog query
        query[i] = tmp.replace(match, choice)
        result[match] = choice

    query = copy(predicate_template_list)  # we will be modifying this list in place
    question = copy(question_template_list)  # TODO: Check: What is the exact output from generate function?
    result = {}

    for i in range(len(predicate_template_list) - 1, -1, -1):  # sample backwards
        # first sample prolog atoms (e.g., name, attribute values)
        # Prolog doesn't have a good way of retrieving all atoms,
        # so we must resort to db.get_names() and db.get_attribute_values()
        # NOTE: there must exist some atoms in order to sample a query
        if match := search(r"(<name>_(\d+))", query[i]):
            assert match in question_template_list
            bank = db.get_names()
            sample_from_bank(bank, rng)

        # if match := re.search(r"(<attribute_value>_(\d+))", query[i]):
        #     assert match.group(1) in question_template_list
        #     bank = db.get_attribute_values()
        #     sample_from_bank(bank, rng)

        # now sample predicates
        if match := search(r"(<(relation)>_(\d+))", query[i]):  # relation predicates
            assert (match in question_template_list) or (
                match.replace("relation", "relation_plural") in question_template_list
            )
            if match in question_template_list:
                get_support(FAMILY_RELATION_EASY, match, query[i])
            else:
                get_support(FAMILY_RELATION_EASY, match, query[i], mapping=FAMILY_RELATION_EASY_SG2PL)

        elif match := search(r"(<attribute_name>_(\d+))", query[i]):  # attribute predicates
            assert match in question_template_list
            get_support(ATTRIBUTE_RELATION, match, query[i])

    return result, " ".join(question), query


#
# End WIP
#
