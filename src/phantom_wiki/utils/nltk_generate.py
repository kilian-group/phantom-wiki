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