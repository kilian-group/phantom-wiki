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

from datetime import date, timedelta


# ============================================================================= #
#                                CLASS  PERSON                                  #
# ============================================================================= #

@dataclass
class Person:
    """A class representing a person in the family tree."""
    index: int
    name: str
    surname: str
    female: bool
    tree_level: int
    date_of_birth: date
    children: List['Person'] = field(default_factory=list)
    parents: List['Person'] = field(default_factory=list)
    married_to: Optional['Person'] = None

    def __str__(self) -> str:
        return (
            f"Person(index={self.index}, name='{self.name} {self.surname}', female={self.female}, "
            f"dob={self.date_of_birth}, "
            f"married_to={self.married_to.index if self.married_to else 'None'}, "
            f"parents=({', '.join(str(p.index) for p in self.parents) if self.parents else 'None'}), "
            f"children=[{', '.join(str(c.index) for c in self.children)}])"
        )
    
    def get_full_name(self) -> str:
        return f"{self.name} {self.surname}"
    

# ============================================================================= #
#                            CLASS PERSON FACTORY                               #
# ============================================================================= #

class PersonFactory:
    """A factory class for creating Person instances."""
    
    def __init__(self):
        self._person_counter = 0
        self._remaining_female_names: List[str] = []
        self._remaining_last_names: List[str] = []
        self._female_names: List[str] = []
        self._male_names: List[str] = []
        self._last_names: List[str] = []

        # Birth date constraints
        self._min_parent_age = 18
        self._max_parent_age = 45
        self._avg_parent_age = 27
        self._max_parent_age_diff = 10
        self._min_year = 0  
        self._twin_probability = 0.05
        self._avg_twin_time_diff = 30
        self._spouse_age_diff_std = 2
        self._parent_child_age_diff_std = 3
        self._std_twin_time_diff = 10
        self._min_days_sibling_diff = 300

    def load_names(self) -> None:
        """Load names from JSON files."""
        from importlib.resources import files
        female_names_file = files("phantom_wiki").joinpath("facts/family/names/female_names.json")
        male_names_file = files("phantom_wiki").joinpath("facts/family/names/male_names.json")
        family_names_file = files("phantom_wiki").joinpath("facts/family/names/last_names.json")

        with open(female_names_file, 'r') as f:
            self._female_names = json.load(f)
        with open(male_names_file, 'r') as f:
            self._male_names = json.load(f)
        with open(family_names_file, 'r') as f:
            self._last_names = json.load(f)
        self.reset()
    
    def reset_names(self) -> None:
        """Reset the first (female & male) name pools to their initial state."""
        self._remaining_female_names = self._female_names[:]
        self._remaining_male_names = self._male_names[:]

    def reset_surnames(self) -> None:
        """Reset the last name to its initial state."""
        self._remaining_last_names = self._last_names[:]

    def reset(self) -> None:
        """Reset the name pools to their initial state."""
        self.reset_names()
        self.reset_surnames()

    def _get_next_surname(self) -> str:
        """Get the next available surname"""
        name_pool = self._last_names

        surname_index = random.randrange(len(name_pool))
        surname = name_pool.pop(surname_index)

        if not name_pool:
            raise NotImplementedError(f"Insufficient surnames: Generating more family trees than available surnames ({len(self._last_names)} total surnames)")
        
        return surname

    def _get_next_name(self, female: bool) -> str:
        """Get the next available name based on gender."""
        name_pool = self._remaining_female_names if female else self._remaining_male_names

        name_index = random.randrange(len(name_pool))
        name = name_pool.pop(name_index)

        if not name_pool:
            raise NotImplementedError(f"Insufficient first names: Generating more people in a family tree than available first names ({len(self._female_names)}, {len(self._male_names)} total female and male names)")
        
        return name
    
    def create_parents(self, tree_level:int, children: Person) -> List[Person]:
        """ Given a children, it will create its 2 parents

        Args:
            tree_level: The level in the family tree where this person belongs
            children: The children of the two parents who are returned            
        """
        # DOB of parents - related_person is the child
        yob_child = children.date_of_birth.year 
        parent_yob_1 = int(random.gauss(yob_child - self._avg_parent_age, self._parent_child_age_diff_std))
        parent_yob_2 = int(random.gauss(parent_yob_1, self._spouse_age_diff_std))

        # Enforcing min-max age difference between parent and child
        parent_yob_1 = min(max(parent_yob_1, yob_child-self._max_parent_age), yob_child-self._min_parent_age)
        parent_yob_2 = min(max(parent_yob_2, yob_child-self._max_parent_age), yob_child-self._min_parent_age)

        # Enforce max diff parent age
        parent_yob_2 = min(max(parent_yob_2, parent_yob_1-self._max_parent_age_diff), parent_yob_1+self._max_parent_age_diff)
        
        parent_dob_1 = date(parent_yob_1, random.randint(1, 12), random.randint(1, 28))
        parent_dob_2 = date(parent_yob_2, random.randint(1, 12), random.randint(1, 28))
        
        # Use child's lastname
        parent_surname = children.surname

        out = [self.create_person(tree_level, parent_surname, parent_dob_1, False),
               self.create_person(tree_level, parent_surname, parent_dob_2, True)]
        
        return out

    def create_child(self, tree_level: int, parents: List[Person], siblings: Optional[List[Person]] = None):
        """Given a children, it will create its 2 parents

        Args:
            tree_level: The level in the family tree where this person belongs
            children: The children of the two parents who are returned            
        """
        max_parent_dob = max(parents[0].date_of_birth, parents[1].date_of_birth)
        min_parent_dob = min(parents[0].date_of_birth, parents[1].date_of_birth)

        # Generate DOB
        if siblings and random.random() < self._twin_probability:
            # Generating a twin 
            existing_twin = random.choice(siblings)
            delta_minutes = max(int(random.gauss(self._avg_twin_time_diff, self._std_twin_time_diff)), 1)

            child_dob = existing_twin.date_of_birth + timedelta(minutes=delta_minutes)
        
        else:
            # Generate a regular sibling
            min_dob = date(max_parent_dob.year+self._min_parent_age, max_parent_dob.month, min(max_parent_dob.day, 28)) # NOTE: Min to ensure that day>28 or else it could error if pushed to a leap year
            mean_dob = date(max_parent_dob.year+self._avg_parent_age, max_parent_dob.month, min(max_parent_dob.day, 28))
            max_dob = date(min_parent_dob.year+self._max_parent_age, min_parent_dob.month, min(min_parent_dob.day, 28))

            start_date = date(1,1,1)
            min_days = (min_dob - start_date).days
            mean_days = (mean_dob- start_date).days
            max_days = (max_dob - start_date).days

            # Create the list of invalid intervals for days
            invalid_day_intervals = [(0, min_days), (max_days, float("inf"))]
            for sibling in siblings:
                sib_days = (sibling.date_of_birth-start_date).days
                invalid_day_intervals.append((sib_days-self._min_days_sibling_diff, sib_days+self._min_days_sibling_diff))

            child_days = int(random.gauss(mean_days, 365 * self._parent_child_age_diff_std))
            while True:

                # Check whether generated day is invalid
                for invalid_interval in invalid_day_intervals:
                    if child_days >= invalid_interval[0] and child_days <= invalid_interval[1]:

                        # Invalid birth day -> Re-draw
                        child_days = int(random.gauss(mean_days, 365 * self._parent_child_age_diff_std))
                        continue

                break
            
            child_dob = start_date + timedelta(days=child_days)

        # Use father's surname
        father = parents[1] if parents[0].female else parents[0]
        surname = father.surname
        
        return self.create_person(tree_level, surname, child_dob)

    def create_spouse(self, tree_level:int, female: bool, spouse: Person) -> Person:
        """Create a spouse (Person instance).

        Args:
            tree_level: The level in the family tree where this person belongs
            spouse: The person who will mary the spouse output
            female: Optional boolean indicating gender. If None, gender is randomly assigned            
        """

        # Generating DOB of spouse
        parent_yob = spouse.date_of_birth.year
        spouse_yob = int(random.gauss(parent_yob, self._spouse_age_diff_std))

        # Enforce max diff parent age
        spouse_yob = min(max(spouse_yob, parent_yob-self._max_parent_age_diff), parent_yob+self._max_parent_age_diff)
        spouse_dob = date(spouse_yob, random.randint(1, 12), random.randint(1, 28))

        # Use spouse surname
        surname = spouse.surname

        return self.create_person(tree_level, surname, spouse_dob, female)

    def create_person(self, tree_level: int, surname: Optional[str] = None, dob: Optional[date] = None, female: Optional[bool] = None) -> Person:
        """Create a new Person instance.
        
        Args:
            tree_level: The level in the family tree where this person belongs
            dob: The date of birth of the individual
            dob: The date of birth of the individual
            female: Optional boolean indicating gender. If None, gender is randomly assigned
        """        
        if dob is None:
            dob = date(tree_level*(self._max_parent_age + 1) + random.randint(1, self._max_parent_age), 
                       random.randint(1,12), 
                       random.randint(1,28))

        if female is None:
            female = random.random() > 0.5
        
        if surname is None:
            surname = self._get_next_surname()

        name = self._get_next_name(female)
        self._person_counter += 1

        return Person(
            surname=surname,
            index=self._person_counter,
            name=name,
            female=female,
            tree_level=tree_level,
            date_of_birth=dob
        )