"""Generates questions using CFGs.
    Step 1: Define the grammar
    Step 2: Sample the grammar (note: this will include placeholders)
    Step 3: Replace the placeholders with the actual values queried from Prolog
"""

from nltk import CFG
from nltk.parse.generate import generate
# from phantom_wiki.utils.nltk_generate import generate_

# Recursive relationship/hobby questions
# Examples:
# - Who is the mother of Anastasia?
# - Who is the mother of the mother of Anastasia?
# - What is the job of Anastasia?
# - What is the job of the mother of Anastasia?
# - Who is the mother of the person whose hobby is reading?
# - How many siblings does Anastasia have?
# - Who is the person whose hobby is reading?
QA_GRAMMAR_STRING = """
S -> 'Who is' R '?' | 'What is' A '?' | 'How many' RN_p 'does' N 'have?'
R -> 'the' RN 'of' R | 'the' RN 'of' N | 'the person whose' AN 'is' AV
A -> 'the' AN 'of' R
RN -> '<relation>'
RN_p -> '<relation_plural>'
AN -> '<attribute_name>'
AV -> '<attribute_value>'
N -> '<name>'
"""


def get_question_templates(grammar_string=QA_GRAMMAR_STRING, depth=15):
    cfg = CFG.fromstring(grammar_string)
    questions = []
    for question in generate(cfg, depth=depth):
        questions.append(question)
    return questions


def get_prolog_templates(question_templates: list[list[str]]) -> list[str]:
    """Generates Prolog skeletons for the question templates.

    The answer to the query is always X.

    Examples:
    >>> get_prolog_templates([["Who is", "the", "<relation>", "of", "the", "<relation>", "of", "<name>", "?"]])
    ["<relation>_1(Y, X), <relation>_2(<name>_1, Y)."]
    >>> get_prolog_templates([["Who is", "the", "<relation>", "of", "<name>", "?"]])
    ["<relation>_1(<name>_1, X)."]
    """

    return question_templates
