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
import sys

from nltk import CFG, Nonterminal


# 
# Begin WIP: 
# we can move this to some file in phantom_wiki/facts/
# 
# possible relations
from ..facts.family.constants import FAMILY_RELATION_EASY
# possible attribute names
from ..facts.attributes.constants import ATTRIBUTE_RELATION
from ..facts.database import Database
# import numpy generator type
from numpy.random import Generator
def sample(db: Database, predicate_template_list: list[str], rng: Generator, valid_only: bool = True):
    """
    Samples possible realizations of the predicate_list from the database db.

    Args:
    - db: the prolog database to sample from
    - predicate_list: a list of predicate templates
    - rng: a random number generator
    - valid_only: whether to sample only valid realizations
        if True: we uniformly sample from the set of prolog queries 
        satisfying the predicate_template_list with a non-empty answer 
        if False: we uniformly sample from all posssible prolog queries
        satsifying the predicate_template_list
    """
    query = []
    for i in range(len(predicate_template_list)-1, -1, -1):
        predicate_template = predicate_template_list[i]
        if valid_only:
            support = []
            for relation in FAMILY_RELATION_EASY:
                # TODO: can we use predicate_template.format() instead of replace?
                # import string
                # formatter = string.Formatter()
                # keys = [field_name for _, field_name, _, _ in formatter.parse(format_string) if field_name]
                if db.query(predicate_template.replace("<relation>", relation)):
                    support.append(relation)
            if not support:
                return None
            choice = rng.choice(support)
            query.append(predicate_template.replace("<relation>", choice))
        else:
            query.append(predicate_template.replace("<relation>", rng.choice(FAMILY_RELATION_EASY)))
    return query
# 
# End WIP
# 

from .parsing import match_placeholder_brackets, match_placeholders

# TODO: RN_p map to <relation> vs <relation_plural>
QA_PROLOG_TEMPLATE_STRING = """
S -> R | A | RN_p R_c
R -> RN R | RN N | AN AV
R_c -> R | N
A -> AN R
RN -> '<relation>'
RN_p -> '<relation>'
AN -> '<attribute_name>'
AV -> '<attribute_value>'
N -> '<name>'
"""

nonterminal_map = {
    ('the', Nonterminal('RN'), 'of', Nonterminal('R')): ["<relation>", "X", "Y"],
    ('the', Nonterminal('RN'), 'of', Nonterminal('N')): "<relation>(X,Y)",
    ('the person whose', Nonterminal('AN'), 'is', Nonterminal('AV')): "<attributename>(X,Y)",
    ('the', Nonterminal('AN'), 'of', Nonterminal('R')): "<attributename>(X,Y)",
    ('How many', Nonterminal('RN_p'), 'does', Nonterminal('R_c'), 'have?'): 'aggregate_all(count, <relation>(Z, Y), X)',
}

def generate(grammar, start=None, depth=None, n=None):
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

    iter = _generate_all(grammar, [start], depth)

    if n:
        iter = itertools.islice(iter, n)

    return iter


def _generate_all(grammar, items, depth):
    if items:
        try:
            for frag1 in _generate_one(grammar, items[0], depth):
                # Process the first fragment in the items list 
                #   e.g. 'Who is' in ['Who is', R, '?']
                for frag2 in _generate_all(grammar, items[1:], depth):
                    # For question generation:
                        # Recursively process the remaining fragments (e.g. [R, '?'])
                        # this will yield all possible sentences for e.g. [R, '?'] as a list[list[str]]
                        # for each list (possible continuation) this adds the first fragment (frag1)
                        # to the beginning
                        # which yields another list[list[str]] of sentences now containing the starting 
                        # fragment
                    # For prolog template generation:
                        # TODO: annotation contents
                    question_frag1, question_frag2 = frag1[0], frag1[1]
                    prolog_frag1, prolog_frag2 = frag2[0], frag2[1]

                    question_template = question_frag1 + question_frag2
                    prolog_template = combine_prolog_templates(prolog_frag1, prolog_frag2, depth) 
                    yield [question_template, prolog_template]
        except RecursionError as error:
            # Helpful error message while still showing the recursion stack.
            raise RuntimeError(
                "The grammar has rule(s) that yield infinite recursion!\n\
                    Eventually use a lower 'depth', or a higher 'sys.setrecursionlimit()'."
            ) from error
    else:
        # End of production: empty sentences and empty annotation
        yield [[], [[], None]] # TODO vs [[]]

def _generate_one(grammar, item, depth):
    if depth > 0:
        if isinstance(item, Nonterminal):
            # generations = []
            for prod in grammar.productions(lhs=item):
                # TODO potentially need to do something here for the prolog template
                yield from _generate_all(grammar, prod.rhs(), depth - 1)
                # generations.append(_generate_all(grammar, prod.rhs(), depth - 1))
            # return generations
                
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
                prolog_template = [[[f"{item}_{depth}"],  None]] 
            else:
                question_template = [item]
                prolog_template = [[[], None]] # TODO format
            

            return [question_template, prolog_template]


def combine_prolog_templates(prolog_frag1, prolog_frag2, depth):
    """Generates a subquery."""

    # Non<placeholder> frag1 case (e.g. 'is', 'of', 'Who is',...)
    #   TODO second condition probably superfluous
    if prolog_frag1[0] == [] and prolog_frag1[1] is None:
        return prolog_frag2
    
    # Productions where frag1 is the last <placeholder> 
    # in the subsentence:
    #     N / <name>
    #     AV / <attribute_value>
    # -> frag2 must be either [[]] or [[], None]
    elif prolog_frag2 == [[]] or prolog_frag2 == [[], None]:
        return prolog_frag1
    
    # Productions where both frag1 and frag2 are <placeholder>s
    # Our grammar currently does not allow frag1 to be a subquery,
    # but frag2 can be either a <placeholder> or a subquery
    # -> frag1 is either:
    #     RN / <relation>_*
    #     RN_p / <relation_plural>_*
    #     AN / <attribute_name>_*
    # -> frag2 is either:
    #     [["subq1",...], Y_d+1]
    #     [["<placeholder>"], None]
    # -> frag1[0] is combined with frag2[0], frag2[1]
    # -> return ["combined subquery containing frag2[1]" + frag2[0],
    #            f"Y_{depth}"]
    elif prolog_frag1[0] != [] and prolog_frag1[1] is None:
        assert len(prolog_frag1[0]) == 1
        placeholder = prolog_frag1[0][0]
        # Match <placeholder>
        if match_placeholders(placeholder, "relation>"):
            if prolog_frag2[1] is None:
                # ... who is the mother of mary ...
                assert len(prolog_frag2[0]) == 1
                subquery = f"{placeholder}({prolog_frag2[0][0]}, Y_{depth})"
            else:
                # ... who is the mother of the mother of mary ...
                subquery = f"{placeholder}({prolog_frag2[1]}, Y_{depth})"
            answer = f"Y_{depth}"
        elif match_placeholders(placeholder, "attribute_name"):
            if prolog_frag2[1] is None:
                # ... whose hobby is running...
                assert len(prolog_frag2[0]) == 1
                subquery = f"{placeholder}(Y_{depth}, {prolog_frag2[0][0]})"
            else:
                # ...the hobby of the mother of mary ...
                subquery = f"{placeholder}(Y_{depth}, {prolog_frag2[1]})"
            answer = f"Y_{depth}"
        elif match_placeholders(placeholder, "relation_plural"):
            relation = placeholder.replace("_plural", "")
            if prolog_frag2[1] is None:
                # ... how many brothers does mary have ...
                assert len(prolog_frag2[0]) == 1
                subquery = f"aggregate_all(count, {relation}({prolog_frag2[0][0]}, Y_{depth}), Count_{depth})"
            else:
                # ... how many brothers does the sister of mary have ...
                subquery = f"aggregate_all(count, {relation}({prolog_frag2[1]}, Y_{depth}), Count_{depth})"
            answer = f"Count_{depth}"
                
        return [[subquery] + prolog_frag2[0], answer] 

    # TODO return [[]]
    assert False, "Not implemented"
