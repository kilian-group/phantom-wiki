import numpy as np
import pydot
import re

# def get_names(family_tree_pl):
#     """Given path to family tree, pull out all the names"""
#     names = []
#     with open(family_tree_pl) as f:
#         for l in f.readlines():
#             l = l.split("(")
#             if l[0]=="male" or l[0]=="female":
#                 name = l[1].split(")")[0]
#                 names.append(name)

#     return names
 
def random_coordinate(n, radius=5):
    """
    Obtains a random point in the (x,y) plane distributed along a n-community gaussian
    mixture block model.
    """
    theta = np.random.randint(0, n) * 2 * np.pi / n
    mean = radius*np.array([np.cos(theta), np.sin(theta)])
    cov = np.eye(2)

    return np.random.multivariate_normal(mean, cov)

def are_friends(p1, p2, tau=.7):
    """Given 2 individuals' features, determine whether they are friends."""
    return np.dot(p1, p2) >= tau

def create_friendship_graph(names, number_of_communities=5, friendship_threshold=.7):
    """ 
    Given the names, this creates a friendship graph with `number_of_communities`
    communities. The `friendship_threshold` input dictates how many friends there are.

    Returns a list of facts and individual features.
    """
    individual_features = []
    for name in names:
        ft = random_coordinate(number_of_communities)
        individual_features.append(ft)

    facts = []
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            if are_friends(individual_features[i], individual_features[j], friendship_threshold):
                facts.append(f"friend(\'{names[i]}\', \'{names[j]}\')")

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