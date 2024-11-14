from argparse import ArgumentParser
import random
import generator
import os
import pydot 

# Create parser for family tree generation
def get_fam_gen_parser():
    parser = ArgumentParser(description="Family Generator")
    parser.add_argument("--max-branching-factor", type=int, default=5,
                        help="The maximum number of children that any person in a family tree may have. (Default value: 5.)")
    parser.add_argument("--max-tree-depth", type=int, default=5,
                        help="The maximum depth that a family tree may have. (Default value: 5.)")
    parser.add_argument("--max-tree-size", type=int, default=26,
                        help="The maximum number of people that may appear in a family tree. (Default value: 26.)")
    parser.add_argument("--num-samples", type=int, default=1,
                        help="The size of the dataset to generate. (Default value: 1.)")
    parser.add_argument("--output-dir", type=str, default="./out",
                        help="The directory where the Prolog trees will be saved. (Default value: ./out)")
    parser.add_argument("--seed", type=int, default=1,
                        help="The seed that is used to initialize the used RNG. (Default value: 1.)")
    parser.add_argument("--stop-prob", type=float, default=0.0,
                        help="The probability of stopping to further extend a family tree after a person has been added. (Default value: 0.)")

    return parser

# Given parser args -> pretty print it
def pretty_print_args(args):
    print('-----------------')
    print('| Configuration |')
    print('-----------------')
    for key, value in vars(args).items():
        print(f"{key.replace('_', ' ').title()}: {value}")

# Given a family tree in the form of a list -> generate the prolog
def family_tree_to_pl(family_tree):
    # Outputs
    genders = []
    parent_relationships = []

    # Getting relationships and genders
    for p in family_tree:
        if p.female:
            genders.append(f"female({p.name}).")
        else:
            genders.append(f"male({p.name}).")

        for child in p.children:
            parent_relationships.append(f"parent({p.name}, {child.name}).")

    # Returning outputs 
    return sorted(genders) + [""] + sorted(parent_relationships)

# Given a family tree, generate and save a graph plot 
def create_dot_graph(family_tree):
    graph = pydot.Dot(graph_type='digraph')  # Directed graph

    # Add the nodes
    for p in family_tree:
        if p.female:
            color = "pink"
        else:
            color = "lightblue"

        graph.add_node(pydot.Node(p.name, style="filled", fillcolor=color))    

    # Add the edges
    for p in family_tree:
        for c in p.children:
            graph.add_edge(pydot.Edge(p.name, c.name))

    return graph

# Generate 
if __name__ == "__main__":
    # Parse arguments and print help
    parser = get_fam_gen_parser()
    args = parser.parse_args()

    # Pretty-print args
    pretty_print_args(args)

    # Set the seed
    random.seed(args.seed)

    # Ensure the output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Get the prolog family tree
    family_trees = generator.Generator.generate(args)
    
    for i, family_tree in enumerate(family_trees):
        print(family_tree[0])
        # Obtain family tree in Prolog format
        pl_family_tree = family_tree_to_pl(family_tree)

        # Create a unique filename for each tree
        output_file_path = os.path.join(args.output_dir, f"family_tree_{i+1}.pl")

        # Write the Prolog family tree to the file
        with open(output_file_path, "w") as f:
            f.write("\n".join(pl_family_tree))
        
        # Generate family graph plot and save it
        family_graph = create_dot_graph(family_tree)
        output_graph_path = os.path.join(args.output_dir, f"family_tree_{i+1}.png")
        family_graph.write_png(output_graph_path)