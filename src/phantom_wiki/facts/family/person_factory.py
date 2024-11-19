# Family Tree Generator
#
# Copyright (C) 2018 Patrick Hohenecker
# Author/Maintainer: Patrick Hohenecker <mail@paho.at>
# URL: <https://github.com/phohenecker/family-tree-data-gen/blob/master/LICENSE>
#
# Version: 2018.1
# Date: May 30, 2018
# License: BSD-2-Clause

import json
import random
import re
from dataclasses import dataclass, field
from typing import List, Optional


# ============================================================================= #
#                                CLASS  PERSON                                  #
# ============================================================================= #

@dataclass
class Person:
    """A class representing a person in the family tree."""
    index: int
    name: str
    female: bool
    tree_level: int
    children: List['Person'] = field(default_factory=list)
    parents: List['Person'] = field(default_factory=list)
    married_to: Optional['Person'] = None

    def __str__(self) -> str:
        return (
            f"Person(index={self.index}, name='{self.name}', female={self.female}, "
            f"married_to={self.married_to.index if self.married_to else 'None'}, "
            f"parents=({', '.join(str(p.index) for p in self.parents) if self.parents else 'None'}), "
            f"children=[{', '.join(str(c.index) for c in self.children)}])"
        )
    

# ============================================================================= #
#                            CLASS PERSON FACTORY                               #
# ============================================================================= #

class PersonFactory:
    """A factory class for creating Person instances."""
    
    def __init__(self):
        self._person_counter = 0
        self._remaining_female_names: List[str] = []
        self._remaining_male_names: List[str] = []
        self._female_names: List[str] = []
        self._male_names: List[str] = []
        
    def load_names(self) -> None:
        """Load names from JSON files."""
        from importlib.resources import files
        female_names_file = files("phantom_wiki").joinpath("facts/family/names/female_names.json")
        male_names_file = files("phantom_wiki").joinpath("facts/family/names/male_names.json")

        with open(female_names_file, 'r') as f:
            self._female_names = json.load(f)
        with open(male_names_file, 'r') as f:
            self._male_names = json.load(f)
        self.reset()
    
    def reset(self) -> None:
        """Reset the name pools to their initial state."""
        self._remaining_female_names = self._female_names[:]
        self._remaining_male_names = self._male_names[:]
    
    def _get_next_name(self, female: bool) -> str:
        """Get the next available name based on gender."""
        name_pool = self._remaining_female_names if female else self._remaining_male_names

        name_index = random.randrange(len(name_pool))
        name = name_pool.pop(name_index)

        if not name_pool:
            # If we've run out of names, create new ones with incremented postfix
            last_name = name
            postfix = re.search(r"([0-9]+)$", last_name)
            new_postfix = str(int(postfix.group(0)) + 1) if postfix else "2"
            
            base_names = self._female_names if female else self._male_names
            name_pool = [f"{name}{new_postfix}" for name in base_names]
            if female:
                self._remaining_female_names = name_pool
            else:
                self._remaining_male_names = name_pool
        
        return name
    
    def create_person(self, tree_level: int, female: Optional[bool] = None) -> Person:
        """Create a new Person instance.
        
        Args:
            tree_level: The level in the family tree where this person belongs
            female: Optional boolean indicating gender. If None, gender is randomly assigned
        """        

        if female is None:
            female = random.random() > 0.5
        
        name = self._get_next_name(female)
        self._person_counter += 1
        
        return Person(
            index=self._person_counter,
            name=name,
            female=female,
            tree_level=tree_level
        )