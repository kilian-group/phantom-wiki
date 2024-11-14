# Family Tree Generator
#
# Copyright (C) 2018 Patrick Hohenecker
# Author/Maintainer: Patrick Hohenecker <mail@paho.at>
# URL: <https://github.com/phohenecker/family-tree-data-gen/blob/master/LICENSE>
#
# Version: 2018.1
# Date: May 30, 2018
# License: BSD-2-Clause

import random
import time
import typing

import networkx as nx

from reldata import data_context as dc

import person
import person_factory as pf

class Generator(object):
    """A generator for creating family tree datasets."""
    
    CLASSES = [
            "female",
            "male"
    ]
    """list: A list of classes each node can belong to."""
    
    def __init__(self):
        raise NotImplementedError("The class Generator cannot be instantiated!")
            
    @classmethod
    def _sample_family_tree(cls, args) -> typing.List[person.Person]:
        """Creates a single family tree.
        
        Args:
            args: The configuration that specifies how to create the dataset.
        
        Returns:
            list[:class:`person.Person`]: The created family tree specified as a list of persons appearing in the same.
                All of the according parent-of relations are specified in terms of the provided instances.
        """
        # add first person to the family tree
        fam_tree = [pf.PersonFactory.create_person(args.max_tree_depth)]

        min_level = fam_tree[0].tree_level
        max_level = fam_tree[0].tree_level
        tree_depth = max_level - min_level
        p = 1
        total_attempts = 0  # the total number of attempts to add a person to the family tree
        while True:
    
            # randomly choose a person from the tree
            current_person = random.choice(fam_tree)
            
            # determine whether it is possible to add parents and children of the sampled person
            can_add_parents = (
                    not current_person.parents and
                    (current_person.tree_level > min_level or tree_depth < args.max_tree_depth)
            )
            can_add_children = (
                    len(current_person.children) < args.max_branching_factor and
                    (current_person.tree_level < max_level or tree_depth < args.max_tree_depth)
            )
            
            # decide what to do
            add_parents = False
            add_child = False
            if can_add_parents and can_add_children:  # -> randomly add either a child or parents
                if random.random() > 0.5:
                    add_parents = True
                else:
                    add_child = True
            elif can_add_parents:
                add_parents = True
            elif can_add_children:
                add_child = True
    
            if add_child:
        
                # check whether the chosen person is married, if not -> add a partner
                if current_person.married_to:
                    spouse = current_person.married_to
                else:
                    spouse = pf.PersonFactory.create_person(
                            current_person.tree_level + 1,
                            female=not current_person.female
                    )
                    spouse.married_to = current_person
                    current_person.married_to = spouse
                    fam_tree.append(spouse)
                    p += 1
        
                # create child
                child = pf.PersonFactory.create_person(current_person.tree_level + 1)
                child.parents.append(current_person)
                child.parents.append(spouse)
                fam_tree.append(child)
                p += 1
        
                # add child to current person and spouse
                current_person.children.append(child)
                spouse.children.append(child)
    
            elif add_parents:
        
                # create mother
                mom = pf.PersonFactory.create_person(current_person.tree_level - 1, female=True)
                mom.children.append(current_person)
                fam_tree.append(mom)
                p += 1
        
                # create father
                dad = pf.PersonFactory.create_person(current_person.tree_level - 1, female=False)
                dad.children.append(current_person)
                fam_tree.append(dad)
                p += 1
        
                # specify parents to be married
                mom.married_to = dad
                dad.married_to = mom
        
                # specify parents of chosen person
                current_person.parents.append(mom)
                current_person.parents.append(dad)
            
            # update bookkeeping variables
            total_attempts += 1
            if add_parents:
                min_level = min(min_level, current_person.tree_level - 1)
            elif add_child:
                max_level = max(max_level, current_person.tree_level + 1)
            tree_depth = max_level - min_level
    
            # stop adding people of maximum number has been reached
            if (
                    p >= args.max_tree_size or
                    total_attempts >= args.max_tree_size * 10 or
                    (args.stop_prob > 0 and random.random() < args.stop_prob)
            ):
                break

        return fam_tree

    @classmethod
    def generate(cls, args) -> None:
        """Generates a family tree dataset based on the provided configuration.
        
        Args:
            args: The configuration that specifies how to create the dataset.
        """        
        # create list for storing graph representations of all created samples (for checking isomorphism)
        sample_graphs = []
        family_trees = []

        for sample_idx in range(args.num_samples):
            
            print("creating sample #{}: ".format(sample_idx), end="")
            
            # use a fresh data context
            with dc.DataContext() as data_ctx:
                
                # reset person factory
                pf.PersonFactory.reset()
                    
                # sample family tree
                print("sampling family tree", end="")
                start = time.time()
                done = False
                while not done:
                    
                    # randomly sample a tree
                    family_tree = cls._sample_family_tree(args)
                    
                    # create a graph that represents the structure of the created sample for checking isomorphism
                    current_graph = nx.DiGraph()
                    for p in family_tree:
                        for parent in p.parents:
                            current_graph.add_edge(p.index, parent.index)
                        if p.married_to is not None:
                            current_graph.add_edge(p.index, p.married_to.index)
                    
                    # check whether the new sample is isomorphic to any sample created earlier
                    for existing_sample in sample_graphs:
                        if nx.is_isomorphic(existing_sample, current_graph):
                            data_ctx.clear()
                            pf.PersonFactory.reset()
                            break
                    else:
                        sample_graphs.append(current_graph)
                        done = True
            
            family_trees.append(family_tree)
            print(" OK ({:.3f}s)".format(time.time() - start))

        return family_trees