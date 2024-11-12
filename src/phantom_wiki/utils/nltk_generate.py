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


nonterminal_map = {
    ('the', Nonterminal('RN'), 'of', Nonterminal('R')): "<relation>(X,Y)",
    ('the', Nonterminal('RN'), 'of', Nonterminal('N')): "<relation>(X,Y)",
    ('the person whose', Nonterminal('AN'), 'is', Nonterminal('AV')): "<attributename>(X,Y)",
    ('the', Nonterminal('AN'), 'of', Nonterminal('R')): "<attributename>(X,Y)",
    ('How many', Nonterminal('RN_p'), 'does', Nonterminal('N'), 'have?'): 'aggregate_all(count, <relation>(Z, Y), X)',
}

def generate_(grammar, start=None, depth=5):
    """
    Generates all possible sentences from a CFG up to a given depth with additional string annotations.

    :param grammar: The Grammar used to generate sentences.
    :param start: The Nonterminal from which to start generating sentences.
    :param depth: The maximal depth of the generated tree.
    :return: A list of tuples (sentence as a string, list of annotations).
    """
    if not start:
        start = grammar.start()
    
    # Initialize a results list to store each sentence and its annotations
    results = []
    
    # Generate sentences up to the specified depth
    for sentence, annotations in _generate_all_sentences(grammar, [start], depth):
        results.append((" ".join(sentence), annotations))
    
    return results

def _generate_all_sentences(grammar, items, depth):
    """
    Helper generator to yield sentences with annotations up to the specified depth.
    """
    # Generate each sentence with a fresh annotation list
    for sentence in _generate_all(grammar, items, depth, []):
        yield sentence

def _generate_all(grammar, items, depth, output_list):
    if items:
        try:
            for frag1, frag1_annotations in _generate_one(grammar, items[0], depth):
                for frag2, frag2_annotations in _generate_all(grammar, items[1:], depth, output_list):
                    # Combine fragments and annotations for a single sentence
                    yield (frag1 + frag2, frag1_annotations + frag2_annotations)
        except RecursionError as error:
            raise RuntimeError(
                "The grammar has rule(s) that yield infinite recursion!\n"
                "Consider using a lower 'depth' or increasing 'sys.setrecursionlimit()'."
            ) from error
    else:
        yield ([], [])

def _generate_one(grammar, item, depth):
    if depth > 0:
        if isinstance(item, Nonterminal):
            for prod in grammar.productions(lhs=item):
                rhs_tuple = tuple(prod.rhs())  # Convert RHS to a tuple for comparison

                # Initialize a fresh list of annotations for this branch
                annotations = []
                
                # Check if rhs_tuple is in the nonterminal_map and add its annotation if present
                if rhs_tuple in nonterminal_map:
                    annotations.append(nonterminal_map[rhs_tuple])

                for sentence, child_annotations in _generate_all(grammar, prod.rhs(), depth - 1, []):
                    # Combine the current annotations with child annotations
                    yield (sentence, annotations + child_annotations)
        else:
            # Terminal, just yield the item as a single-element list
            yield ([item], [])