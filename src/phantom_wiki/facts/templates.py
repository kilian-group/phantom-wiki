"""Generates formal question templates and corresponding Prolog queries using a context-free grammar (CFG).


*Question templates* are based on the QA_GRAMMAR_STRING and can be generated at varying recursion depths.
The templates are not complete questions or valid queries, as they contain the <placeholder> tokens intended
to be replaced with their instantiations that depend on their type and the Prolog database. 

For example, at a low recursion depth the grammar string may generate two questions:

    > Question: Who is the person whose hobby is reading?
    > Template: Who is the person whose <attribute_name>_1 is <attribute_value>_1 ?

    > Question: How many childern does John have?
    > Template: How many <relation_plural>_2 does <name>_1 have?

Therefore a template of a question is an abstraction of many possible questions of the same type.

Note the exact numbering of the <placeholder> tokens may differ based on the chosen recursion depth, and is 
there to distinguish tokens potentially generated at the same recursion depth but representing different
tokens.

Each question template has a corresponding template for Prolog query used to obtain the ground truth answer.
For example:

    > Template: Who is the person whose <attribute_name>_1 is <attribute_value>_1 ?
    > Query: <attribute_name>_1(Y_2, <attribute_value>_1).
    > Answer: Y_2

    > Template: How many <relation_plural>_2 does <name>_1 have?
    > Query: aggregate_all(count, <relation>_2(<name>_1, Y_3), Count_3).
    > Answer: Count_3


`phantom_wiki.facts.templates.generate_templates` generates tuples of all possible question and Prolog query
templates at a particular recursion depth from the context-free grammar as defined by QA_GRAMMAR_STRING.

This template generation is based on the `nltk.parse.generate` function from the NLTK project, see:
    Source: https://github.com/nltk/nltk/blob/develop/nltk/parse/generate.py
    Natural Language Toolkit: Generating from a CFG

    Copyright (C) 2001-2024 NLTK Project
    Author: Steven Bird <stevenbird1@gmail.com>
            Peter Ljunglöf <peter.ljunglof@heatherleaf.se>
            Eric Kafe <kafe.eric@gmail.com>
    URL: https://www.nltk.org/
    For license information, see https://github.com/nltk/nltk/blob/develop/LICENSE.txt
"""


import itertools
import sys

from nltk import CFG, Nonterminal

from ..utils.parsing import match_placeholder_brackets, match_placeholders


QA_GRAMMAR_STRING = """
S -> 'Who is' R '?' | 'What is' A '?' | 'How many' RN_p 'does' R_c 'have?'
R -> 'the' RN 'of' R_c | 'the person whose' AN 'is' AV
R_c -> R | N
A -> 'the' AN 'of' R
RN -> '<relation>'
RN_p -> '<relation_plural>'
AN -> '<attribute_name>'
AV -> '<attribute_value>'
N -> '<name>'
"""


def generate_templates(depth=4, n=None):
    """Generates an iterator of all question templates and corresponding Prolog queries from a CFG.

    Args:
        depth: The maximal depth of the generated tree. Default value 4, minimum depth of QA_GRAMMAR_STRING.
        n: The maximum number of sentences to return. If None, returns all sentences.

    Returns:
        An iterator of lists of the form [question_template, prolog_template], where
            question_template is a list of strings of non-terminal tokens, and
            prolog_tempalte is of the form [list of query statements: list[str], query answer: str]
    """
    grammar = CFG.fromstring(QA_GRAMMAR_STRING)

    if not start:
        start = grammar.start()
    if depth is None:
        # Safe default, assuming the grammar may be recursive:
        depth = (sys.getrecursionlimit() // 3) - 3

    iter = _generate_tail_template_fragments(grammar, [start], depth)

    if n:
        iter = itertools.islice(iter, n)

    return iter


def _generate_tail_template_fragments(grammar, items, depth):
    if items:
        try:
            templates = []
            for frag1 in _generate_head_template_fragments(grammar, items[0], depth):
                # Process the first fragment in the items list
                #   e.g. 'Who is' in ['Who is', R, '?']
                for frag2 in _generate_tail_template_fragments(grammar, items[1:], depth):
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
                    prolog_template = _combine_prolog_fragments(prolog_frag1, prolog_frag2, depth)
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


def _generate_head_template_fragments(grammar, item, depth):
    if depth > 0:
        if isinstance(item, Nonterminal):
            generations = []
            for prod in grammar.productions(lhs=item):
                generations += _generate_tail_template_fragments(grammar, prod.rhs(), depth - 1)
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


def _combine_prolog_fragments(prolog_frag1, prolog_frag2, depth):
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
