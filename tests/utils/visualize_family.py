# %%
import os
import sys
module_path = os.path.abspath(os.path.join('../..'))
if module_path not in sys.path:
    sys.path.append(module_path)

from src.phantom_wiki.utils.visualization import create_dot_graph, prolog_to_facts
from IPython.display import Image, display

def view_pydot(pdot):
    plt = Image(pdot.create_png())
    display(plt)

FAMILY_TREE_EXAMPLE_26_PATH = "./family_tree_26.pl"
# Path to the family tree in prolog (not the rules)
prolog_facts = prolog_to_facts(FAMILY_TREE_EXAMPLE_26_PATH)  

# Create a dot graph
graph = create_dot_graph(prolog_facts)

# NOTE: requires graphviz to be installed (e.g. `brew install graphviz`)
view_pydot(graph)
# %%
