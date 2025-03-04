"""Family Tree Generator

Copyright (C) 2018 Patrick Hohenecker
Author/Maintainer: Patrick Hohenecker <mail@paho.at>
URL: <https://github.com/phohenecker/family-tree-data-gen/blob/master/LICENSE>

Version: 2018.1
Date: May 30, 2018
License: BSD-2-Clause
"""

import logging
import os
import random
import time

import pydot
from tqdm import tqdm

from phantom_wiki.facts.family.constants import PERSON_TYPE
from phantom_wiki.facts.family.person_factory import Person, PersonFactory

# ============================================================================= #
#                               CLASS  GENERATOR                                #
# ============================================================================= #


class Generator:
    """A generator for creating family tree datasets."""

    def __init__(self, person_factory: PersonFactory):
        self.person_factory = person_factory

    def _sample_family_tree(
        self,
        max_family_tree_depth: int,
        max_branching_factor: int,
        max_family_tree_size: int,
        stop_prob: float,
    ) -> list[Person]:
        """Creates a single family tree.

        Args:
            max_family_tree_depth (int): The maximum depth that a family tree may have.
            max_branching_factor (int): Maximum number of children that any person in a family tree may have.
            max_family_tree_size (int): The maximum number of people that may appear in a family tree.
            stop_prob (float): Probability of stopping to extend a family tree after a person has been added.

        Returns:
            list[Person]: A list of Person objects representing the generated family tree.
        """
        # add first person to the family tree
        fam_tree = [self.person_factory.create_person(max_family_tree_depth)]

        min_level = max_level = fam_tree[0].tree_level
        tree_depth = max_level - min_level
        person_count = 1
        total_attempts = 0

        while True:
            # randomly choose a person from the tree
            current_person = random.choice(fam_tree)

            # determine whether it is possible to add parents and children of the sampled person
            can_add_parents = not current_person.parents and (
                current_person.tree_level > min_level or tree_depth < max_family_tree_depth
            )
            can_add_children = len(current_person.children) < max_branching_factor and (
                current_person.tree_level < max_level or tree_depth < max_family_tree_depth
            )

            # decide what to do
            add_parents = add_child = False
            if can_add_parents and can_add_children:  # -> randomly add either a child or parents
                add_parents = random.random() > 0.5
                add_child = not add_parents
            else:
                add_parents = can_add_parents
                add_child = can_add_children

            if add_child:
                # check whether the chosen person is married, if not -> add a partner
                if current_person.married_to:
                    spouse = current_person.married_to
                else:
                    spouse = self.person_factory.create_spouse(
                        current_person.tree_level, female=not current_person.female, spouse=current_person
                    )
                    spouse.married_to = current_person
                    current_person.married_to = spouse
                    fam_tree.append(spouse)
                    person_count += 1

                # create child
                child = self.person_factory.create_child(
                    current_person.tree_level + 1,
                    parents=[current_person, spouse],
                    siblings=current_person.children,
                )
                child.parents = [current_person, spouse]
                fam_tree.append(child)

                # add child to current person and spouse
                current_person.children.append(child)
                spouse.children.append(child)

                max_level = max(max_level, child.tree_level)
                person_count += 1

            elif add_parents:
                # Create parents
                dad, mom = self.person_factory.create_parents(current_person.tree_level - 1, current_person)

                # specify relationships
                mom.married_to = dad
                dad.married_to = mom
                mom.children.append(current_person)
                dad.children.append(current_person)
                current_person.parents = [mom, dad]

                # Add to tree
                fam_tree.extend([mom, dad])
                person_count += 2
                min_level = min(min_level, mom.tree_level)

            # update bookkeeping variables
            total_attempts += 1
            tree_depth = max_level - min_level

            # Check stopping conditions
            if (
                person_count >= max_family_tree_size
                or total_attempts >= max_family_tree_size * 10
                or (stop_prob > 0 and random.random() < stop_prob)
            ):
                break

        return fam_tree

    def generate(
        self,
        max_family_tree_depth: int,
        max_branching_factor: int,
        max_family_tree_size: int,
        stop_prob: float,
        num_family_trees: int,
        debug: bool,
        output_dir: str,
    ) -> list[list[Person]]:
        """Generates a list family trees based on the provided configuration.

        Args:
            max_family_tree_depth (int): The maximum depth that a family tree may have.
            max_branching_factor (int): Maximum number of children that any person in a family tree may have.
            max_family_tree_size (int): The maximum number of people that may appear in a family tree.
            stop_prob (float): Probability of stopping to extend a family tree after a person has been added.
            num_family_trees (int): The number of family trees to generate.
            debug (bool): Whether to enable debug output.
            output_dir (str): Path to the output folder.

        Returns:
            list[list[Person]]: A list of family trees, where family trees are lists of Person objects.
        """
        # create list for storing graph representations of all created samples
        family_trees = []

        all_time_start = time.time()
        names = []
        for sample_idx in tqdm(range(num_family_trees), desc="Generating family trees", leave=False):
            # sample family tree
            family_tree = self._sample_family_tree(
                max_family_tree_depth, max_branching_factor, max_family_tree_size, stop_prob
            )
            family_trees.append(family_tree)

            names += [p.get_full_name() for p in family_tree]

            # save generated family tree as a graph
            if debug:
                graph = create_dot_graph(family_tree)
                save_path = os.path.join(output_dir, f"family_tree_{sample_idx+1}.png")
                logging.debug(f"Saving family tree {sample_idx+1} to {save_path}")
                graph.write_png(save_path)

        if len(set(names)) != len(names):
            raise ValueError(
                "Duplicate names found || If this error is raised, there is a bug in the code. "
                "This is a sanity check which should never be triggered"
            )

        logging.info(
            f"Generated {len(family_trees)} family trees for a total of "
            f"{sum([len(tree) for tree in family_trees])} individuals in "
            f"{time.time()-all_time_start:.3f}s."
        )

        return family_trees


# Given a family tree in the form of a list -> generate the facts
def family_tree_to_facts(family_tree):
    # Outputs
    people = []
    genders = []
    parent_relationships = []
    dates_of_birth = []

    # Add facts for each person in the family tree
    for p in family_tree:
        # add 1-ary clause indicating the person exists
        people.append(f'type("{p.get_full_name()}", {PERSON_TYPE})')

        # add 2-ary clause indicating gender
        if p.female:
            genders.append(f'gender("{p.get_full_name()}", "female")')
        else:
            genders.append(f'gender("{p.get_full_name()}", "male")')

        # add 2-ary clause indicating parent relationship
        for child in p.children:
            parent_relationships.append(f'parent("{child.get_full_name()}", "{p.get_full_name()}")')

        # add 2-ary clause indicating date of birth
        dates_of_birth.append(f'dob("{p.get_full_name()}", "{p.date_of_birth}")')

    # Returning outputs
    return sorted(people) + sorted(genders) + sorted(parent_relationships) + sorted(dates_of_birth)


# Given a family tree, generate and save a graph plot
def create_dot_graph(family_tree):
    graph = pydot.Dot(graph_type="digraph")  # Directed graph

    # Add the nodes
    for p in family_tree:
        if p.female:
            color = "pink"
        else:
            color = "lightblue"

        graph.add_node(pydot.Node(p.get_full_name(), style="filled", fillcolor=color))

    # Add the edges
    for p in family_tree:
        for c in p.children:
            graph.add_edge(pydot.Edge(p.get_full_name(), c.get_full_name()))

    return graph
