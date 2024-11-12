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

def get_question_templates(grammar_string=QA_GRAMMAR_STRING, depth=15):
    cfg = CFG.fromstring(grammar_string)
    questions = []
    for question in generate(cfg, depth=depth):
        questions.append(question)
    return questions

# test question templates (depth=5)
# 1. 'Who is', 'the', relation1, 'of', 'the', 'relation2, 'of', 'name1, '?'
# Prolog_query: relation1(X,Y), relation2(name1,Y)
# Answer: X 
# 2. 'Who is', 'the', relation1 'of', 'the person whose', attributename1, 'is', attributevalue1, '?'
# Prolog_query: relation1(X,Y), attributename1(X, attributevalue1)
# Answer: Y
# 3. 'Who is', 'the', relation1, 'of', 'name1, '?'
# Prolog_query: relation1(name1, X)
# Answer: X
# 4. 'Who is', 'the', person whose, attributename1, 'is', attributevalue1, '?'
# Prolog_query: attributename1(X, attributevalue1)
# Answer: X
# 5. 'what is', 'the', attributename1, 'of', 'the', relation1, 'of' name1 '?'
# Prolog_query: attributename1(Y, Z), relation1(name1,Y)
# Answer: Z
# 7. 'How many', relation1s, 'does', name1, 'have?'
# Prolog_query: aggregate_all(count, relation1(name1,X), Count).
# Answer: count
