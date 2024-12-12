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
from typing import List
import os
import pydot
from dateutil.relativedelta import relativedelta

from phantom_wiki.facts.family.person_factory import (PersonFactory, 
                                                      Person, 
                                                      Event)
from phantom_wiki.facts.family import fam_gen_parser
from phantom_wiki.utils import get_parser
from phantom_wiki.facts.family.constants import PERSON_TYPE

# NOTE: we set the marriage date to 16 years after the younger spouse's date of birth
AGE_AT_MARRIAGE = relativedelta(years=16)
DUR_OF_MARRIAGE = relativedelta(years=16)
DUR_OF_DIVORCE = relativedelta(years=1)

# ============================================================================= #
#                               CLASS  GENERATOR                                #
# ============================================================================= #

class Generator:        
    """A generator for creating family tree datasets."""
    
    def __init__(self, person_factory: PersonFactory):
        self.person_factory = person_factory

    def _sample_family_tree(self, args) -> List[Person]:
        """Creates a single family tree.
        
        Args:
            args: The configuration that specifies how to create the dataset.
        """
        # add first person to the family tree
        fam_tree = [self.person_factory.create_person(args.max_tree_depth)]

        # AG: initialize min_level and max_level to have value: `args.max_tree_depth`
        # It seems like the exact value of min_level and max_level is not important.
        min_level = max_level = fam_tree[0].tree_level
        tree_depth = max_level - min_level
        person_count = 1
        total_attempts = 0

        while True:
    
            # randomly choose a person from the tree
            current_person = random.choice(fam_tree)
            
            # determine whether it is possible to add parents and children of the sampled person
            can_add_parents = (
                # AG: the person has no parents
                not current_person.parents and
                # AG: the person is neither at the the top level of the tree or at the maximum allowable depth
                (current_person.tree_level > min_level or tree_depth < args.max_tree_depth)
            )
            can_add_children = (
                # AG: the person has less than the maximum number of children
                len(current_person.children) < args.max_branching_factor and
                # AG: the person is neither at the bottom level of the tree or at the maximum allowable depth
                (current_person.tree_level < max_level or tree_depth < args.max_tree_depth)
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
                # check whether the chosen person is single, if not -> add a partner
                if current_person.events:
                    e = current_person.events[0]
                    assert e.type == 'marriage', "First event must be a marriage"
                    # NOTE: to test events, we define the spouse to be the partner in the first event, even if they divorced later
                    spouse = current_person.events[0].spouse
                else:
                    spouse = self.person_factory.create_spouse(
                        tree_level = current_person.tree_level,
                        female = not current_person.female,
                        spouse = current_person
                    )
                    date_of_marriage = max(current_person.date_of_birth, spouse.date_of_birth) + AGE_AT_MARRIAGE
                    spouse.events.append(Event('marriage', current_person, date_of_marriage))
                    current_person.events.append(Event('marriage', spouse, date_of_marriage))
                    fam_tree.append(spouse)
                    person_count += 1
        
                # create child
                child = self.person_factory.create_child(
                    tree_level = current_person.tree_level + 1,
                    parents = [current_person, spouse],
                    siblings = current_person.children
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
                date_of_marriage = max(dad.date_of_birth, mom.date_of_birth) + AGE_AT_MARRIAGE
                dad.events.append(Event('marriage', mom, date_of_marriage))
                mom.events.append(Event('marriage', dad, date_of_marriage))
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
            if (person_count >= args.max_tree_size or
                total_attempts >= args.max_tree_size * 10 or
                (args.stop_prob > 0 and random.random() < args.stop_prob)):
                break


        return fam_tree

    def generate(self, args) -> List[List[Person]]:
        """Generates a family tree dataset based on the provided configuration.
        
        Args:
            args: The configuration that specifies how to create the dataset.
        """        
        # create list for storing graph representations of all created samples
        family_trees = []

        for sample_idx in range(args.num_samples):
            
            print("creating sample #{}: ".format(sample_idx), end="")
            start = time.time()
                
            # sample family tree
            print("sampling family tree...")
            family_tree = self._sample_family_tree(args)
            family_trees.append(family_tree)

            # add divorce and remarrying events
            # TODO: should we wrap this in a loop?
            print("adding divorce and remarrying events...")
            # for each person in the family tree with a spouse
            # add a divorce event after 16 years with a fixed probability (previous marriage duration for testing)
            # for each person in the family tree with a latest divorce event
            # add a remarriage event after 1 year with a fixed probability
            for i in range(len(family_tree)):
                p = family_tree[i]
                if len(p.events) % 2 == 1: # can only divorce if the person has odd number of events (i.e., married)
                    e = p.events[-1]
                    assert e.type == 'marriage', "Last event must be a marriage"
                    spouse = e.spouse
                    if random.random() < args.divorce_rate:
                        divorce_date = e.date + DUR_OF_MARRIAGE
                        p.events.append(Event('divorce', spouse, divorce_date))
                        spouse.events.append(Event('divorce', p, divorce_date))

                elif len(p.events) > 0 and len(p.events) % 2 == 0: # can only remarry if the person has even number of events (i.e., divorced)
                    e = p.events[-1]
                    assert e.type == 'divorce', "Last event must be a divorce"
                    if random.random() < args.remarry_rate:
                        remarry_date = e.date + DUR_OF_DIVORCE
                        # TODO: how to find the spouse? for now just remarry to one of your exes? 
                        exes = [event.spouse for event in p.events if event.type == 'marriage']
                        spouse = random.choice(exes)
                        p.events.append(Event('marriage', spouse, remarry_date))
                        spouse.events.append(Event('marriage', p, remarry_date))

            # add remarriage events
            print("adding remarriage events...")


                        

            print("OK ({:.3f}s)".format(time.time() - start))

            # Resetting person factory if user allows for duplicate names
            if not args.duplicate_names:
                self.person_factory.reset()


        return family_trees
    
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
            # parent_relationships.append(f"parent({p.name}, {child.name}).")
            parent_relationships.append(f"parent({child.name}, {p.name}).")

    # Returning outputs 
    return sorted(genders) + [""] + sorted(parent_relationships)

# Given a family tree in the form of a list -> generate the facts
def family_tree_to_facts(family_tree):
    # Outputs
    people = []
    genders = []
    parent_relationships = []
    dates_of_birth = []
    events = []

    # Add facts for each person in the family tree
    for p in family_tree:
        # add 1-ary clause indicating the person exists
        people.append(f"type(\'{p.name}\', {PERSON_TYPE})")
        # add 2-ary clause indicating gender
        # NOTE: by making gender an attribute, the attribute value can be any literal
        if p.female:
            genders.append(f"gender(\'{p.name}\', \'female\')")
        else:
            genders.append(f"gender(\'{p.name}\', \'male\')")
        # add 2-ary clause indicating parent relationship
        for child in p.children:
            parent_relationships.append(f"parent(\'{child.name}\', \'{p.name}\')")
        # add 2-ary clause indicating date of birth
        dates_of_birth.append(f"dob(\'{p.name}\', \'{p.date_of_birth}\')")

        # add 3-ary events ('marriage' or 'divorce')
        for event in p.events:
            events.append(f"{event.type}(\'{p.name}\', \'{event.spouse.name}\', \'{event.date}\')")
            # NOTE: a single marriage will correspond to two `married` facts in the prolog database

    # Returning outputs 
    return sorted(people) + sorted(genders) + sorted(parent_relationships) + sorted(dates_of_birth) + sorted(events)

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
    events = set()
    for p in family_tree:
        for c in p.children:
            graph.add_edge(pydot.Edge(p.name, c.name))
        # add a solid line for marriage
        if len(p.events) == 1 and p.events[0].type == 'marriage':
            # don't add the same edge twice
            if (p.events[0].spouse.name, p.name) in events:
                continue
            graph.add_edge(pydot.Edge(p.name, p.events[0].spouse.name, style="solid", dir="none"))
            events.add((p.name, p.events[0].spouse.name))
        elif len(p.events) == 2 and p.events[0].type == 'marriage' and p.events[1].type == 'divorce':
            # don't add the same edge twice
            if (p.events[1].spouse.name, p.name) in events:
                continue
            graph.add_edge(pydot.Edge(p.name, p.events[1].spouse.name, style="dashed", dir="none"))
            events.add((p.name, p.events[1].spouse.name))

    return graph

# Generate 
if __name__ == "__main__":
    # Parse arguments and print help
    parser = get_parser(parents=[fam_gen_parser])
    args = parser.parse_args()

    # Pretty-print args
    pretty_print_args(args)

    # Set the seed
    random.seed(args.seed)

    # Ensure the output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Get the prolog family tree
    pf = PersonFactory()
    pf.load_names()

    gen = Generator(pf)
    family_trees = gen.generate(args)
    for i, family_tree in enumerate(family_trees):
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