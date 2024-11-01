from phantom_wiki.utils.visualization import create_dot_graph, prolog_to_facts

# TODO: refactor as a proper test

# Read prolog facts
path_to_pl = "phantom-wiki/tests/family_tree_100.pl"
prolog_facts = prolog_to_facts(path_to_pl)  # Path to the family tree in prolog (not the rules)

# Create a dot graph
graph = create_dot_graph(prolog_facts)

# Save as PNG
path_to_save = "family_tree_100_visualization.png"
graph.write_png(path_to_save)
