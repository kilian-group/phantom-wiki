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
    > Query: aggregate_all(count, distinct(<relation_plural>_2(<name>_1, Y_3)), Count_3).
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

import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from nltk import CFG, Nonterminal

QA_GRAMMAR_STRING = """
    S -> 'Who is' R '?' | 'What is' A '?' | 'How many' RN_p 'does' R_c 'have' '?'
    R -> 'the' RN 'of' R_c | 'the person whose' AN 'is' AV
    R_c -> R | N
    A -> 'the' AN 'of' R
    RN -> '<relation>'
    RN_p -> '<relation_plural>'
    AN -> '<attribute_name>'
    AV -> '<attribute_value>'
    N -> '<name>'
    """
# QA_GRAMMAR_STRING = """
#     S -> 'Who is' R '?' | 'What is' A '?'
#     R -> 'the' RN 'of' R_c | 'the person whose' AN 'is' AV
#     R_c -> R | N
#     A -> 'the' AN 'of' R
#     RN -> '<relation>'
#     RN_p -> '<relation_plural>'
#     AN -> '<attribute_name>'
#     AV -> '<attribute_value>'
#     N -> '<name>'
#     """


def generate_templates(grammar: CFG = None, depth=4) -> Iterable:
    """Generates an iterator of all question templates and corresponding Prolog queries from a CFG.

    To generate valid Prolog queries, the grammar is assumed to contain <placeholder> terminals with
    <relation>s (with <relation_plural>s for counting queries), <attribute_name>s (corresponding to
    concepts like "job" or "hobby") and matching <attribute_value>s (e.g., "architect" or "running").

    Args:
        grammar: The CFG used to generate questions and queries.
            By default, the grammar is based on QA_GRAMMAR_STRING.
        depth: The maximal depth of the generated tree.
            Default value 4, minimum depth of QA_GRAMMAR_STRING.

    Returns:
        An iterator of lists of the form [question_template, prolog_template], where
        question_template is a list of strings of non-terminal tokens, and
        prolog_template is of the form [list of query statements: list[str], query answer: str]
    """
    if grammar is None:
        grammar = CFG.fromstring(QA_GRAMMAR_STRING)

    start = grammar.start()
    if depth is None:
        # Safe default, assuming the grammar may be recursive:
        depth = (sys.getrecursionlimit() // 3) - 3

    fragments = _generate_tail_template_fragments(grammar, [start], depth, depth)

    templates = []
    for fragment in fragments:
        question = fragment.q_fragment
        query = fragment.p_fragment
        answer = fragment.p_answer

        templates.append((question, query, answer))

    return templates


@dataclass
class Fragment:
    """Fragment of the question and Prolog query template.

    Represents a subsequence of the CFG.
    If the subsequence is empty, it will be of the form ([], [], None).
    If the subsequence is a single terminal, it will be of the form (['terminal'], [], None).
    If the subsequence is a single <placeholder> terminal, it will be of the form
        (['<placeholder>_*'], ['<placeholder>_*'], None).
    Otherwise, a general subsequence is of the form
        (['Who is', 'the', '<relation>_*', ...], ['<relation>_*(...)', ...], Y_*)

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


def _generate_tail_template_fragments(
    grammar: CFG, items: list[Nonterminal | Any], depth: int, total_depth: int
) -> list[Fragment]:
    """Generates fragments for a list of symbols (`items`) in the grammar.

    Calls `_generate_head_template_fragments` to process the first symbol in `items` and then makes a
    recursive call to process the "remaining symbols" (tail) of the list.
    Then combines all valid subsequences (fragments) resulting from the tail call with all the valid
    subsequences produced from the first symbol.
    """
    if items:
        try:
            fragments = []
            for frag1 in _generate_head_template_fragments(grammar, items[0], depth, total_depth):
                for frag2 in _generate_tail_template_fragments(grammar, items[1:], depth, total_depth):
                    fragments.append(_combine_fragments(frag1, frag2, depth, total_depth))
        except RecursionError as error:
            # Helpful error message while still showing the recursion stack.
            raise RuntimeError(
                "The grammar has rule(s) that yield infinite recursion!\n\
                    Eventually use a lower 'depth', or a higher 'sys.setrecursionlimit()'."
            ) from error
        return fragments
    else:
        # End of production
        return [Fragment()]


def _generate_head_template_fragments(
    grammar: CFG, item: Nonterminal | Any, depth: int, total_depth: int
) -> list[Fragment]:
    """Generates fragments for the current `item` symbol of the grammar.

    Called as a subroutine to process the first symbol (head) of the current production (`item`).
    Recursively calls `_generate_tail_template_fragments` if `item` is a nonterminal in the CFG, for all its
    possible productions.
    If `item` is a <placeholder> or terminal, generates its Fragment.
    """
    if depth > 0:
        if isinstance(item, Nonterminal):
            fragments = []
            for prod in grammar.productions(lhs=item):
                fragments += _generate_tail_template_fragments(grammar, prod.rhs(), depth - 1, total_depth)
            return fragments

        elif re.match(r"<.*?>", item):
            # <placeholder> terminal
            d = total_depth - depth
            return [Fragment([f"{item}_{d}"], [f"{item}_{d}"], None)]
        else:
            # non<placeholder> terminal
            return [Fragment([item], [], None)]

    return []


def _combine_fragments(f1: Fragment, f2: Fragment, depth, total_depth) -> Fragment:
    """Combines two Fragments.

    This merges two CFG subsequences, e.g. 'Who is' and 'the <relation> of ...'.
    The question fragments are combined straightforwardly by concatenating the symbols.
    The Prolog query fragments are combined based on the <placeholder> and query type.

    Examples:
    > (['Who is'], [], None) + (['<name>'], ['<name>'], None) -> (['Who is', '<name>'], ['<name>'], None)
    > (['<attribute_name>_3'], ['<attribute_name>_3'], None)
        + (['of the', '<relation>_2', 'of', '<name>_1', '?'], ['<relation>_2(<name>_1, Y_3)'], 'Y_3')
        -> (['<attribute_name>_3', 'of the', ...],
            ['<attribute_name>_3(Y_3, Y_4)', '<relation>_2(<name>_1, Y_3)'],
            'Y_4')
    """

    q_fragment = f1.q_fragment + f2.q_fragment

    if f1.is_empty():
        return Fragment(q_fragment, f2.p_fragment, f2.p_answer)

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

        d = total_depth - depth

        if re.match(r"<relation_plural>_(\d+)", placeholder):
            if f2.is_placeholder():
                # ... how many brothers does Alice have ...
                subquery = [
                    (f"aggregate_all(count, distinct({placeholder}({f2.p_fragment[0]}, Y_{d})), Count_{d})")
                ]
            else:
                # ... how many brothers does the sister of Alice have ...
                subquery = [
                    f"aggregate_all(count, distinct({placeholder}({f2.p_answer}, Y_{d})), Count_{d})"
                ] + f2.p_fragment
            answer = f"Count_{d}"

        elif re.match(r"<relation>_(\d+)", placeholder):
            if f2.is_placeholder():
                # ... who is the mother of Alice ...
                subquery = [f"{placeholder}({f2.p_fragment[0]}, Y_{d})"]
            else:
                # ... who is the mother of the mother of Alice ...
                subquery = [f"{placeholder}({f2.p_answer}, Y_{d})"] + f2.p_fragment
            answer = f"Y_{d}"

        elif re.match(r"<attribute_name>_(\d+)", placeholder):
            if placeholder.replace("name", "value") in f2.p_fragment[0]:
                # ... whose hobby is running ...
                assert f2.is_placeholder()
                subquery = [f"{placeholder}(Y_{d}, {f2.p_fragment[0]})"]
            else:
                # ...the hobby of the mother of Alice ...
                subquery = [f"{placeholder}({f2.p_answer}, Y_{d})"] + f2.p_fragment
            answer = f"Y_{d}"

        return Fragment(q_fragment, subquery, answer)
