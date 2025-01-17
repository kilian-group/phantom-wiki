# %%
import os
import sys

module_path = os.path.abspath(os.path.join("../.."))
if module_path not in sys.path:
    sys.path.append(module_path)

from IPython.display import Image, display

from src.phantom_wiki.utils.visualization import create_dot_graph, prolog_to_facts
from tests.phantom_wiki.facts.family import DATABASE_SMALL_107


def view_pydot(pdot):
    plt = Image(pdot.create_png())
    display(plt)


# Path to the family tree in prolog (not the rules)
prolog_facts = prolog_to_facts(DATABASE_SMALL_107)

# Create a dot graph
graph = create_dot_graph(prolog_facts)

# NOTE: requires graphviz to be installed (e.g. `brew install graphviz`)
view_pydot(graph)
# %%
