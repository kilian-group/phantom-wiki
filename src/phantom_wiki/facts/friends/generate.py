import logging
import time

import networkx as nx


def create_friendship_graph(names, k: int, seed: int, visualize: bool = False, output_dir: str = None):
    """
    Given the names, this creates a friendship graph using the G(n,p) variant of Erdos-Renyi model.

    Returns a list of facts and individual features.
    """
    start_time = time.time()
    # Generate an G(n,p) Erdős–Rényi random graph
    p = k / len(names)
    G = nx.fast_gnp_random_graph(n=len(names), p=p, seed=seed)

    # Rename nodes with names from the list
    mapping = {i: name for i, name in enumerate(names)}
    G = nx.relabel_nodes(G, mapping)

    facts = []
    # if there is an edge between two nodes, they are friends
    connected_edges = list(G.edges)
    for i, j in connected_edges:
        facts.append(f'friend_("{i}", "{j}")')
    logging.info(f"Generated friendship tree of {len(names)} individuals in {time.time()-start_time:.3f}s.")

    if visualize:
        from matplotlib import pyplot as plt

        plt.figure(figsize=(8, 6))
        nx.draw(
            G,
            with_labels=True,
            node_color="lightblue",
            edge_color="gray",
            node_size=2000,
            font_size=6,
        )

        # Save the plot to a file
        plt.title(f"Erdős–Rényi Graph G(n={len(names)}, p={p})")
        plt.savefig(
            f"{output_dir}/friendship_graph.png", format="png", dpi=300
        )  # Save as PNG with high resolution
        plt.close()  # Close figure

    return facts
