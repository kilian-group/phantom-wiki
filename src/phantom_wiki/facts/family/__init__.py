# imports for family relations and templates
from .constants import FAMILY_RELATION_DIFFICULTY

FAMILY_RELATION_EASY = [k for k, v in FAMILY_RELATION_DIFFICULTY.items() if v < 2]
FAMILY_RELATION_HARD = [k for k, v in FAMILY_RELATION_DIFFICULTY.items() if v >= 2]

from importlib.resources import files

FAMILY_RULES_BASE_PATH = files("phantom_wiki").joinpath("facts/family/rules_base.pl")
FAMILY_RULES_DERIVED_PATH = files("phantom_wiki").joinpath("facts/family/rules_derived.pl")

import logging

# imports for family generation
from argparse import ArgumentParser

# Create parser for family tree generation
fam_gen_parser = ArgumentParser(description="Family Generator", add_help=False)
fam_gen_parser.add_argument(
    "--max-branching-factor",
    type=int,
    default=5,
    help="The maximum number of children that any person in a family tree may have. (Default value: 5.)",
)
fam_gen_parser.add_argument(
    "--max-family-tree-depth",
    type=int,
    default=5,
    help="The maximum depth that a family tree may have. (Default value: 5.)",
)
fam_gen_parser.add_argument(
    "--max-family-tree-size",
    type=int,
    default=25,
    help="The maximum number of people that may appear in a family tree. (Default value: 25)",
)
fam_gen_parser.add_argument(
    "--num-family-trees",
    type=int,
    default=1,
    help="The number of family trees to generate. (Default value: 1.)",
)
fam_gen_parser.add_argument(
    "--stop-prob",
    type=float,
    default=0.0,
    help="The probability of stopping to further extend a family tree after a person has been added. "
    "(Default value: 0.)",
)
fam_gen_parser.add_argument(
    "--duplicate-names",
    type=bool,
    default=False,
    help="Allow/prevent duplicate names in the generation. (Default value: False.)",
)

# wrapper for family tree generation

import os
import random

from .generate import Generator, PersonFactory, create_dot_graph, family_tree_to_facts


def db_generate_family(
    db,
    seed: int,
    duplicate_names: bool,
    debug: bool,
    output_dir: str,
    visualize: bool,
    max_family_tree_depth: int,
    max_branching_factor: int,
    max_family_tree_size: int,
    stop_prob: float,
    num_family_trees: int,
) -> None:
    """Generates family facts for a database.

    Args:
        db: Database object to store the generated family facts.
        seed (int): Global seed for random number generator.
        duplicate_names (bool): Allow/prevent duplicate names in the generation.
        debug (bool): Whether to enable debug output.
        output_dir (str): Path to the output folder.
        visualize (bool): Whether or not to visualize the family graphs.
        max_family_tree_depth (int): The maximum depth that a family tree may have.
        max_branching_factor (int): The maximum number of children that any person in a family tree may have.
        max_family_tree_size (int): The maximum number of people that may appear in a family tree.
        stop_prob (float): Probability of stopping to extend a family tree after a person has been added.
        num_family_trees (int): The number of family trees to generate.

    Returns:
        None, the function adds the generated family facts to the database.
    """
    # set the random seed
    random.seed(seed)

    # Get the prolog family tree
    pf = PersonFactory(duplicate_names)

    gen = Generator(pf)
    family_trees = gen.generate(
        max_family_tree_depth,
        max_branching_factor,
        max_family_tree_size,
        stop_prob,
        num_family_trees,
        debug,
        output_dir,
    )

    for i, family_tree in enumerate(family_trees):
        logging.debug(f"Adding family tree {i+1} to the database.")

        # Obtain family tree facts
        facts = family_tree_to_facts(family_tree)
        db.add(*facts)

        # If the debug flag is effective -> save the family tree to a file
        if debug:
            # Create a unique filename for each tree
            output_file_path = os.path.join(output_dir, f"family_tree_{i+1}.pl")
            os.makedirs(output_dir, exist_ok=True)

            # Write the Prolog family tree to the file
            with open(output_file_path, "w") as f:
                f.write("\n".join(facts))

        # If the visualize flag is effective -> generate family graph plot and save it
        if visualize:
            family_graph = create_dot_graph(family_tree)
            output_graph_path = os.path.join(output_dir, f"family_tree_{i+1}.png")
            family_graph.write_png(output_graph_path)

    logging.debug(f"Saved family trees in {output_dir} as .pl and .png (if visualize=True).")
