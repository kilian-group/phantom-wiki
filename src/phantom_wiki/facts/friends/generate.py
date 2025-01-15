import numpy as np
from numpy.random import Generator
import pydot
import logging
import time
import re

def random_coordinate(rng, n, radius=5):
    """
    Obtains a random point in the (x,y) plane distributed along a n-community gaussian
    mixture block model.
    """
    theta = rng.integers(0, n) * 2 * np.pi / n
    mean = radius*np.array([np.cos(theta), np.sin(theta)])
    cov = np.eye(2)

    return rng.multivariate_normal(mean, cov)

def are_friends(p1, p2, tau=.7):
    """Given 2 individuals' features, determine whether they are friends."""
    return np.dot(p1, p2) >= tau

def create_friendship_graph(
        rng: Generator,
        names, 
        number_of_communities=5, 
        friendship_threshold=.7,
    ):
    """ 
    Given the names, this creates a friendship graph with `number_of_communities`
    communities. The `friendship_threshold` input dictates how many friends there are.

    Returns a list of facts and individual features.
    """
    start_time = time.time()
    individual_features = []
    for name in names:
        ft = random_coordinate(rng, number_of_communities)
        individual_features.append(ft)

    facts = []
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            if are_friends(individual_features[i], individual_features[j], friendship_threshold):
                facts.append(f"friend_(\"{names[i]}\", \"{names[j]}\")")
    logging.info(f"Generated friendship tree of {len(names)} individuals in {time.time()-start_time:.3f}s.")
        
    return facts, individual_features

def plot_friendship_tree(names, coords, pl_friendship_tree):
    """ Given the prolog friendship tree, plot it. """
    graph = pydot.Dot(graph_type='graph',layout="neato")
    
    for friendship in pl_friendship_tree:
        _, f1, f2, _ = re.split("[(),]", friendship)
        edge = pydot.Edge(f1, f2)
        graph.add_edge(edge)
    
    # Add nodes
    for name, (x, y) in zip(names, coords): 
        graph.add_node(pydot.Node(name, pos=f"{x},{y}!", style="filled", fillcolor="white"))
    
    return graph

# # Obtain names to create the friendship tree on
# names = get_names("tests/family/family_tree_100.pl")


"""
# Plot and save plot of friendship tree
generate_tree_visualization = False
if generate_tree_visualization:
    graph = plot_friendship_tree(names, coords, pl_friendship_tree)
    graph.write_png('tests/friendship_tree_100_visualization.png')
"""