# Source: https://github.com/nltk/nltk/blob/develop/nltk/parse/generate.py
# Natural Language Toolkit: Generating from a CFG
#
# Copyright (C) 2001-2024 NLTK Project
# Author: Steven Bird <stevenbird1@gmail.com>
#         Peter Ljunglöf <peter.ljunglof@heatherleaf.se>
#         Eric Kafe <kafe.eric@gmail.com>
# URL: <https://www.nltk.org/>
# For license information, see LICENSE.TXT
#

import itertools
import re
import sys
from copy import copy

from nltk import Nonterminal

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

from .parsing import match_placeholder_brackets, match_placeholders

# , match_placeholders_group


def generate_1(grammar, start=None, depth=None, n=None):
    """
    Generates an iterator of all sentences from a CFG.

    :param grammar: The Grammar used to generate sentences.
    :param start: The Nonterminal from which to start generate sentences.
    :param depth: The maximal depth of the generated tree.
    :param n: The maximum number of sentences to return.
    :return: An iterator of lists of terminal tokens.
    """
    if not start:
        start = grammar.start()
    if depth is None:
        # Safe default, assuming the grammar may be recursive:
        depth = (sys.getrecursionlimit() // 3) - 3

    iter = _generate_all_1(grammar, [start], depth)

    if n:
        iter = itertools.islice(iter, n)

    return iter


def _generate_all_1(grammar, items, depth):
    if items:
        try:
            templates = []
            for frag1 in _generate_one_1(grammar, items[0], depth):
                # Process the first fragment in the items list
                #   e.g. 'Who is' in ['Who is', R, '?']
                for frag2 in _generate_all_1(grammar, items[1:], depth):
                    # For question generation:
                    #   Recursively process the remaining fragments (e.g. [R, '?'])
                    #   this will yield all possible sentences for e.g. [R, '?'] as a list[list[str]]
                    #   for each list (possible continuation) this adds the first fragment (frag1)
                    #   to the beginning
                    #   which yields another list[list[str]] of sentences now containing the starting
                    #   fragment
                    # For prolog template generation:
                    assert len(frag1) == 2 and len(frag2) == 2
                    question_frag1, prolog_frag1 = frag1[0], frag1[1]
                    question_frag2, prolog_frag2 = frag2[0], frag2[1]

                    question_template = question_frag1 + question_frag2
                    prolog_template = combine_prolog_templates(prolog_frag1, prolog_frag2, depth)
                    templates.append([question_template, prolog_template])
        except RecursionError as error:
            # Helpful error message while still showing the recursion stack.
            raise RuntimeError(
                "The grammar has rule(s) that yield infinite recursion!\n\
                    Eventually use a lower 'depth', or a higher 'sys.setrecursionlimit()'."
            ) from error
        return templates
    else:
        # End of production: empty sentences and empty annotation [[]]
        return [[[], [[]]]]


def _generate_one_1(grammar, item, depth):
    if depth > 0:
        if isinstance(item, Nonterminal):
            generations = []
            for prod in grammar.productions(lhs=item):
                generations += _generate_all_1(grammar, prod.rhs(), depth - 1)
            return generations

        else:
            # Terminal
            # for question generation:
            #     yield the terminal as list[str] of length 1
            # for prolog query generation
            #     if item is a <placeholder>, annotate with depth (e.g. <placeholder>_depth) and return
            #     if item is another string (e.g. 'Who is') return nothing
            if match_placeholder_brackets(item):
                question_template = [f"{item}_{depth}"]
                prolog_template = [[f"{item}_{depth}"], None]
            else:
                question_template = [item]
                prolog_template = [[], None]

            return [[question_template, prolog_template]]

    return []


def combine_prolog_templates(prolog_frag1, prolog_frag2, depth):
    """Generates a subquery."""

    if prolog_frag1 == [[]]:
        return prolog_frag2

    # Non<placeholder> frag1 case (e.g. 'is', 'of', 'Who is',...)
    elif prolog_frag1 == [[], None]:
        if prolog_frag2 == [[]]:
            return prolog_frag1
        else:
            return prolog_frag2

    # <placeholder> frag1 case (e.g. '<relation>', '<name>',...)
    #   Note: the grammar currently does not allow frag1 to be a subquery,
    #   but frag2 can be either a subquery, <placeholder>, non<placeholder>, or end of sentence
    else:
        if prolog_frag2 == [[]] or prolog_frag2 == [[], None]:
            return prolog_frag1

        assert len(prolog_frag1[0]) == 1
        placeholder = prolog_frag1[0][0]
        subquery = None
        answer = None

        # Match <placeholder>
        if match_placeholders(placeholder, "relation_plural"):
            relation = placeholder.replace("_plural", "")
            if prolog_frag2[1] is None:
                # ... how many brothers does mary have ...
                assert len(prolog_frag2[0]) == 1
                subquery = f"aggregate_all(count, {relation}({prolog_frag2[0][0]}, Y_{depth}), Count_{depth})"
                subquery = [subquery]
            else:
                # ... how many brothers does the sister of mary have ...
                subquery = f"aggregate_all(count, {relation}({prolog_frag2[1]}, Y_{depth}), Count_{depth})"
                subquery = [subquery] + prolog_frag2[0]
            answer = f"Count_{depth}"
        elif match_placeholders(placeholder, "relation"):
            if prolog_frag2[1] is None:
                # ... who is the mother of mary ...
                assert len(prolog_frag2[0]) == 1
                subquery = f"{placeholder}({prolog_frag2[0][0]}, Y_{depth})"
                subquery = [subquery]
            else:
                # ... who is the mother of the mother of mary ...
                subquery = f"{placeholder}({prolog_frag2[1]}, Y_{depth})"
                subquery = [subquery] + prolog_frag2[0]
            answer = f"Y_{depth}"
        elif match_placeholders(placeholder, "attribute_name"):
            if prolog_frag2[1] is None:
                # ... whose hobby is running...
                assert len(prolog_frag2[0]) == 1
                assert placeholder.replace("name", "value") in prolog_frag2[0][0]
                subquery = f"{placeholder}(Y_{depth}, {prolog_frag2[0][0]})"
                subquery = [subquery]
            else:
                # ...the hobby of the mother of mary ...
                assert placeholder.replace("name", "value") not in prolog_frag2[0][0]
                subquery = f"{placeholder}({prolog_frag2[1]}, Y_{depth})"
                subquery = [subquery] + prolog_frag2[0]
            answer = f"Y_{depth}"

        return [subquery, answer]
