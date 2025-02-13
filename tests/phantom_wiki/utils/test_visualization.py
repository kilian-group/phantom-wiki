from phantom_wiki.utils.visualization import create_dot_graph, prolog_to_facts


# TODO: refactor as a proper test
def to_refactor_as_test():
    # TODO: fix path to get the example from tests/family
    FAMILY_TREE_EXAMPLE_100_PATH = "family_tree_100.pl"
    prolog_facts = prolog_to_facts(
        FAMILY_TREE_EXAMPLE_100_PATH
    )  # Path to the family tree in prolog (not the rules)

    # Create a dot graph
    graph = create_dot_graph(prolog_facts)

    # Save as PNG
    path_to_save = "family_tree_100_visualization.png"
    graph.write_png(path_to_save)
