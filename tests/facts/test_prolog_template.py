# %%
import os
import sys

module_path = os.path.abspath(os.path.join("../../src"))
if module_path not in sys.path:
    sys.path.append(module_path)

from nltk import CFG

from phantom_wiki.facts.question_template import QA_GRAMMAR_STRING, get_question_templates
from phantom_wiki.utils.nltk_generate import generate_1

DEPTH = 6

def print_prolog_templates(grammar_string=QA_GRAMMAR_STRING, depth=DEPTH):
    grammar = CFG.fromstring(grammar_string)
    questions = generate_1(grammar, depth=depth)
    total_questions = 0
    for question in questions:
        total_questions += 1
        print("Question:\t" + " ".join(question[0]))
        print("Query:\t\t" + ",".join(question[1][0]) + ".")
        print("Answer:\t\t" + question[1][1])
        print()
    print(f"Total questions (depth {DEPTH}):\t\t\t {total_questions}")

print_prolog_templates()

print(f"Ground truth number of questions (depth {DEPTH}):\t {len(get_question_templates(depth=DEPTH))}")
# %%
