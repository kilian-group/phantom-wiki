# %%
import os
import sys

module_path = os.path.abspath(os.path.join("../../src"))
if module_path not in sys.path:
    sys.path.append(module_path)

from nltk import CFG

from phantom_wiki.facts.templates import QA_GRAMMAR_STRING, generate_templates

DEPTH = 8


def print_prolog_templates(grammar_string=QA_GRAMMAR_STRING, depth=DEPTH):
    grammar = CFG.fromstring(grammar_string)
    questions = generate_templates(grammar, depth=depth)
    total_questions = 0
    for question in questions:
        total_questions += 1
        print("Question:\t" + question.get_question_template())
        print("Query:\t\t" + question.get_query_template())
        print("Answer:\t\t" + question.get_query_answer())
        print()
    print(f"Total questions (depth {DEPTH}):\t\t\t{total_questions}")


print_prolog_templates()

# print(f"Ground truth number of questions (depth {DEPTH}):\t{len(get_question_templates(depth=DEPTH))}")
# %%
