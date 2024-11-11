"""Generates questions using CFGs.
    Step 1: Define the grammar
    Step 2: Sample the grammar (note: this will include placeholders)
    Step 3: Replace the placeholders with the actual values queried from Prolog
"""

from nltk import CFG
from nltk.parse.generate import generate

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

# define the CFG
cfg = CFG.fromstring(QA_GRAMMAR_STRING)
# sample the grammar
n_questions = 0
depth = 200
for question in generate(cfg, depth=depth):
    n_questions += 1
    # print(" ".join(question))
print(f"{n_questions} questions at depth {depth}")

