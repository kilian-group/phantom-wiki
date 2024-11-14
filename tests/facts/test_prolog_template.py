#%%
import os
import sys

import numpy as np

module_path = os.path.abspath(os.path.join("../.."))
if module_path not in sys.path:
    sys.path.append(module_path)

from src.phantom_wiki.utils.nltk_generate import generate
from src.phantom_wiki.facts.question_template import QA_GRAMMAR_STRING

from nltk import CFG

def print_prolog_templates(grammar_string=QA_GRAMMAR_STRING, depth=15):
    grammar = CFG.fromstring(grammar_string)
    questions = generate(grammar, depth=depth)
    for question in questions:
        print(question)

print_prolog_templates()

# %%
