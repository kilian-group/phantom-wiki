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
from ..facts.family.constants import FAMILY_RELATION_EASY


def sample(db: Database, predicate_template_list: list[str], rng: Generator, valid_only: bool = True):
    """
    Samples possible realizations of the predicate_list from the database db.
    Example:
    >>> ["<relation>_1(<name>_1, X)"]
    father(anastasia, X)
    mother(anastasia, X)
    >>> ["<relation>_1(Y, X)", "<relation>_2(<name>_1, Y)"]
    father(Y,X), mother(anastasia,Y)
    father(Y,X), father(anastasia,Y)
    mother(Y,X), mother(anastasia,Y)
    mother(Y,X), father(anastasia,Y)
    >>> ["<relation>_1(Y, X)", "<attribute_name>_1(X, <attribute_value>_1)"]
    father(Y,X), hobby(anastasia,running)
    father(Y,X), hobby(anastasia,reading)
    mother(Y,X), hobby(anastasia,running)
    mother(Y,X), hobby(anastasia,reading)

    Args:
        db: the prolog database to sample from
        predicate_list: a list of predicate templates
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

    query = copy(predicate_template_list)  # we will be modifying this list in place
    result = {}
    for i in range(len(predicate_template_list) - 1, -1, -1):  # sample backwards
        # first sample prolog atoms (e.g., name, attribute values)
        # Prolog doesn't have a good way of retrieving all atoms,
        # so we must resort to db.get_names() and db.get_attribute_values()
        # NOTE: there must exist some atoms in order to sample a query
        if match := search(r"(<name>_(\d+))", query[i]):
            names = db.get_names()
            if not names:
                return None
            choice = rng.choice(names)
            query[i] = predicate_template_list[i].replace(match, choice)
            result[match] = choice
        if match := re.search(r"(<attribute_value>_(\d+))", query[i]):
            attribute_values = db.get_attribute_values()
            if not attribute_values:
                return None
            choice = rng.choice(attribute_values)
            query[i] = predicate_template_list[i].replace(match, choice)
            result[match] = choice

        # now sample predicates
        if match := search(r"(<(relation|relation_plural)>_(\d+))", query[i]):  # relation predicates
            tmp = query[i]
            if valid_only:
                support = []
                for relation in FAMILY_RELATION_EASY:
                    # TODO: can we use predicate_template.format() instead of replace?
                    # import string
                    # formatter = string.Formatter()
                    # keys = [field_name for _, field_name, _, _ in formatter.parse(format_string) if field_name]
                    query[i] = tmp.replace(match, relation)
                    if db.query(",".join(query[i:])):
                        support.append(relation)
                if not support:
                    return None
                choice = rng.choice(support)
            else:
                choice = rng.choice(FAMILY_RELATION_EASY)
            query[i] = tmp.replace(match, choice)
            result[match] = choice
        elif match := search(r"(<attribute_name>_(\d+))", query[i]):  # attribute predicates
            tmp = query[i]
            if valid_only:
                support = []
                for attribute in ATTRIBUTE_RELATION:
                    query[i] = tmp.replace(match, attribute)
                    if db.query(",".join(query[i:])):
                        support.append(attribute)
                if not support:
                    return None
                choice = rng.choice(support)
            else:
                choice = rng.choice(ATTRIBUTE_RELATION)
            query[i] = tmp.replace(match, choice)
            result[match] = choice
    return result


#
# End WIP
#

from .parsing import match_placeholder_brackets, match_placeholders


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
                # TODO [query: list[str], answer: str] format
                # [["<attribute_value_5"], None]
                prolog_template = [[f"{item}_{depth}"], None]
            else:
                question_template = [item]
                prolog_template = [[], None]  # TODO format

            return [[question_template, prolog_template]]
    return []  # TODO


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
    #   but frag2 can be either a a subquery, <placeholder>, non<placeholder>, or end of sentence
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
                subquery = f"{placeholder}(Y_{depth}, {prolog_frag2[0][0]})"
                subquery = [subquery]
            else:
                # ...the hobby of the mother of mary ...
                subquery = f"{placeholder}(Y_{depth}, {prolog_frag2[1]})"
                subquery = [subquery] + prolog_frag2[0]
            answer = f"Y_{depth}"

        return [subquery, answer]
