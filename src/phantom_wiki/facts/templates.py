"""Generates formal question templates and corresponding Prolog queries using a context-free grammar (CFG).


*Question templates* are based on the QA_GRAMMAR_STRING and can be generated at varying recursion depths.
The templates are not complete questions or valid queries, as they contain the <placeholder> tokens intended
to be replaced with their instantiations that depend on their type and the Prolog database.

For example, at a low recursion depth the grammar string may generate two questions:

    > Question: Who is the person whose hobby is reading?
    > Template: Who is the person whose <attribute_name>_1 is <attribute_value>_1 ?

    > Question: How many children does John have?
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
    > Query: aggregate_all(count, <relation_plural>_2(<name>_1, Y_3), Count_3).
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
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field

from nltk import CFG, Nonterminal

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


def generate_templates(grammar: CFG = None, depth=4, n=None) -> Iterable:
    """Generates an iterator of all question templates and corresponding Prolog queries from a CFG.

    Args:
        grammar:
        depth: The maximal depth of the generated tree. Default value 4, minimum depth of QA_GRAMMAR_STRING.
        n: The maximum number of sentences to return. If None, returns all sentences.

    Returns:
        An iterator of lists of the form [question_template, prolog_template], where
        question_template is a list of strings of non-terminal tokens, and
        prolog_tempalte is of the form [list of query statements: list[str], query answer: str]
    """
    if grammar is None:
        grammar = CFG.fromstring(QA_GRAMMAR_STRING)

    start = grammar.start()
    if depth is None:
        # Safe default, assuming the grammar may be recursive:
        depth = (sys.getrecursionlimit() // 3) - 3

    iter = _generate_tail_template_fragments(grammar, [start], depth)

    if n:
        iter = itertools.islice(iter, n)

    return iter


@dataclass
class Fragment:
    """Fragment of the question and Prolog query template.

    Attributes:
        q_fragment: Question template of the current fragment
        p_fragment: Prolog query template of the current fragment
        p_answer: The variable in the Prolog query template corresponding to the answer
    """

    q_fragment: list[str] = field(default_factory=list)
    p_fragment: list[str] = field(default_factory=list)
    p_answer: str = None

    def is_empty(self):
        """End-of-production fragment."""
        return not self.q_fragment

    def is_terminal(self):
        """Regular non<placeholder> terminal."""
        return not self.p_fragment

    def is_placeholder(self):
        """Test for <placeholder> terminal."""
        return len(self.p_fragment) == 1 and not self.p_answer

    def get_question_template(self) -> str:
        # TODO remove space before question mark
        return " ".join(self.q_fragment)

    def get_query_template(self) -> str:
        return ", ".join(self.p_fragment)

    def get_query_answer(self) -> str:
        return self.p_answer


def _generate_tail_template_fragments(grammar, items, depth):
    """

    For question generation:
    Recursively process the remaining fragments (e.g. [R, '?'])
    this will yield all possible sentences for e.g. [R, '?'] as a list[list[str]]
    for each list (possible continuation) this adds the first fragment (frag1)
    to the beginning
    which yields another list[list[str]] of sentences now containing the starting
    fragment
    For prolog template generation:

    Terminal
    for question generation:
    yield the terminal as list[str] of length 1
    for prolog query generation
    if item is a <placeholder>, annotate with depth (e.g. <placeholder>_depth) and return
    if item is another string (e.g. 'Who is') return nothing
    """
    if items:
        try:
            templates = []
            for frag1 in _generate_head_template_fragments(grammar, items[0], depth):
                # Process the first fragment in the items list
                #   e.g. 'Who is' in ['Who is', R, '?']
                for frag2 in _generate_tail_template_fragments(grammar, items[1:], depth):
                    new_fragment = _combine_fragments(frag1, frag2, depth)
                    templates.append(new_fragment)
        except RecursionError as error:
            # Helpful error message while still showing the recursion stack.
            raise RuntimeError(
                "The grammar has rule(s) that yield infinite recursion!\n\
                    Eventually use a lower 'depth', or a higher 'sys.setrecursionlimit()'."
            ) from error
        return templates
    else:
        # End of production
        return [Fragment()]


def _generate_head_template_fragments(grammar, item, depth):
    if depth > 0:
        if isinstance(item, Nonterminal):
            generations = []
            for prod in grammar.productions(lhs=item):
                generations += _generate_tail_template_fragments(grammar, prod.rhs(), depth - 1)
            return generations

        elif re.match(r"<.*?>", item):
            # <placeholder> terminal
            return [Fragment([f"{item}_{depth}"], [f"{item}_{depth}"], None)]
        else:
            # non<placeholder> terminal
            return [Fragment([item], [], None)]

    return []


def _combine_fragments(f1: Fragment, f2: Fragment, depth) -> Fragment:
    """Generates a subquery."""

    q_fragment = f1.q_fragment + f2.q_fragment

    if f1.is_empty():
        return Fragment(q_fragment, f2.p_fragment, f2.p_answer)

    # Non<placeholder> (terminal) f1 case (e.g. 'is', 'of', 'Who is',...)
    elif f1.is_terminal():
        if f2.is_empty():
            return Fragment(q_fragment, f1.p_fragment, f1.p_answer)
        else:
            return Fragment(q_fragment, f2.p_fragment, f2.p_answer)

    # <placeholder> f1 case (e.g. '<relation>', '<name>',...)
    #   Note: the grammar currently does not allow f1 to be a subquery,
    #   but f2 can be either a subquery, <placeholder>, terminal, or empty
    else:
        if f2.is_empty() or f2.is_terminal():
            return Fragment(q_fragment, f1.p_fragment, f1.p_answer)

        assert f1.is_placeholder()
        placeholder = f1.p_fragment[0]
        subquery = None
        answer = None

        # Match <placeholder>
        if re.match(r"<relation_plural>_(\d+)", placeholder):
            if f2.is_placeholder():
                # ... how many brothers does Alice have ...
                subquery = [
                    (f"aggregate_all(count, {placeholder}({f2.p_fragment[0]}, Y_{depth}), Count_{depth})")
                ]
            else:
                # ... how many brothers does the sister of Alice have ...
                subquery = [
                    f"aggregate_all(count, {placeholder}({f2.p_answer}, Y_{depth}), Count_{depth})"
                ] + f2.p_fragment
            answer = f"Count_{depth}"

        elif re.match(r"<relation>_(\d+)", placeholder):
            if f2.is_placeholder():
                # ... who is the mother of Alice ...
                subquery = [f"{placeholder}({f2.p_fragment[0]}, Y_{depth})"]
            else:
                # ... who is the mother of the mother of Alice ...
                subquery = [f"{placeholder}({f2.p_answer}, Y_{depth})"] + f2.p_fragment
            answer = f"Y_{depth}"
            
        elif re.match(r"<attribute_name>_(\d+)", placeholder):
            # Match <attribute_value>
            if placeholder.replace("name", "value") in f2.p_fragment[0]:
                # ... whose hobby is running ...
                assert f2.is_placeholder()
                subquery = [f"{placeholder}(Y_{depth}, {f2.p_fragment[0]})"]
            else:
                # ...the hobby of the mother of Alice ...
                subquery = [f"{placeholder}({f2.p_answer}, Y_{depth})"] + f2.p_fragment
            answer = f"Y_{depth}"

        return Fragment(q_fragment, subquery, answer)
