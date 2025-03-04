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
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

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
    children: list["Person"] = field(default_factory=list)
    parents: list["Person"] = field(default_factory=list)
    married_to: Optional["Person"] = None

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

    def __init__(self, duplicate_names):
        self._person_counter = 0
        self.duplicate_names = duplicate_names

        # Name datastructures
        self._female_names: list[str] = []
        self._male_names: list[str] = []
        self._last_names: list[str] = []
        self._remaining_names = dict()
        self._remaining_male_last_names: list[str] = []
        self._remaining_female_last_names: list[str] = []
        self._remaining_both_last_names: list[str] = []
        self._remaining_either_last_names: list[str] = []

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

        self.load_names()

    def load_names(self) -> None:
        """Load names from JSON files."""
        from importlib.resources import files

        female_names_file = files("phantom_wiki").joinpath("facts/family/names/female_names.json")
        male_names_file = files("phantom_wiki").joinpath("facts/family/names/male_names.json")
        family_names_file = files("phantom_wiki").joinpath("facts/family/names/last_names.json")

        with open(female_names_file) as f:
            self._female_names = json.load(f)
        with open(male_names_file) as f:
            self._male_names = json.load(f)
        with open(family_names_file) as f:
            self._last_names = json.load(f)

        self._remaining_male_last_names = self._last_names.copy()
        self._remaining_female_last_names = self._last_names.copy()
        self._remaining_both_last_names = self._last_names.copy()
        self._remaining_either_last_names = self._last_names.copy()

        for last_name in self._last_names:
            self._remaining_names[last_name] = {
                True: self._female_names.copy(),
                False: self._male_names.copy(),
            }

    def _get_last_name(self, female: bool = None) -> str:
        """Get an available last name"""
        if female is None:  # Need to choose a last name that still has male and female first names
            last_name_pool = self._remaining_both_last_names
        else:  # Need to choose a last name that this has first names depending on female value
            last_name_pool = self._remaining_female_last_names if female else self._remaining_male_last_names

        if last_name_pool == []:
            raise NotImplementedError(
                "Insufficient names: Generating a dataset of this size is not supported "
                "(try reducing --num-family-trees)"
            )

        last_name = random.choice(last_name_pool)
        return last_name

    def _get_first_name(self, female: bool, surname: str) -> str:
        """Get an available first name based on gender and surnmame"""
        name_pool = self._remaining_names[surname][female]

        if name_pool == []:
            raise NotImplementedError(
                "Insufficient names: Generating a dataset of this size is not supported "
                "(try reducing --num-family-trees)"
            )

        name_index = random.randrange(len(name_pool))

        if not self.duplicate_names:
            name = name_pool.pop(name_index)
        else:
            name = name_pool[name_index]

        if len(name_pool) == 0:
            last_name_pool = self._remaining_female_last_names if female else self._remaining_male_last_names

            last_name_pool.remove(surname)

            self._remaining_both_last_names.remove(surname)

            other_last_name_pool = (
                self._remaining_male_last_names if female else self._remaining_female_last_names
            )
            if surname not in other_last_name_pool:
                self._remaining_either_last_names.remove(surname)

        return name

    def _get_name(self, female: bool) -> str:
        """Get an available name, last_name based on gender."""
        last_name = self._get_last_name(female)
        name = self._get_first_name(female, last_name)

        return name, last_name

    def create_parents(self, tree_level: int, children: Person) -> list[Person]:
        """Given a children, it will create its 2 parents

        Args:
            tree_level: The level in the family tree where this person belongs
            children: The children of the two parents who are returned
        """
        # DOB of parents - related_person is the child
        yob_child = children.date_of_birth.year
        parent_yob_1 = int(random.gauss(yob_child - self._avg_parent_age, self._parent_child_age_diff_std))
        parent_yob_2 = int(random.gauss(parent_yob_1, self._spouse_age_diff_std))

        # Enforcing min-max age difference between parent and child
        parent_yob_1 = min(
            max(parent_yob_1, yob_child - self._max_parent_age), yob_child - self._min_parent_age
        )
        parent_yob_2 = min(
            max(parent_yob_2, yob_child - self._max_parent_age), yob_child - self._min_parent_age
        )

        # Enforce max diff parent age
        parent_yob_2 = min(
            max(parent_yob_2, parent_yob_1 - self._max_parent_age_diff),
            parent_yob_1 + self._max_parent_age_diff,
        )

        parent_dob_1 = date(parent_yob_1, random.randint(1, 12), random.randint(1, 28))
        parent_dob_2 = date(parent_yob_2, random.randint(1, 12), random.randint(1, 28))

        # Generate lastname
        if children.female and children.married_to:
            parent_surname = self._get_last_name()
        else:
            parent_surname = children.surname

        out = [
            self.create_person(tree_level, parent_surname, parent_dob_1, False),
            self.create_person(tree_level, parent_surname, parent_dob_2, True),
        ]

        return out

    def create_child(self, tree_level: int, parents: list[Person], siblings: list[Person] | None = None):
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
            min_dob = date(
                max_parent_dob.year + self._min_parent_age, max_parent_dob.month, min(max_parent_dob.day, 28)
            )  # NOTE: Min to ensure that day>28 or else it could error if pushed to a leap year
            mean_dob = date(
                max_parent_dob.year + self._avg_parent_age, max_parent_dob.month, min(max_parent_dob.day, 28)
            )
            max_dob = date(
                min_parent_dob.year + self._max_parent_age, min_parent_dob.month, min(min_parent_dob.day, 28)
            )

            start_date = date(1, 1, 1)
            min_days = (min_dob - start_date).days
            mean_days = (mean_dob - start_date).days
            max_days = (max_dob - start_date).days

            # Create the list of invalid intervals for days
            invalid_day_intervals = [(0, min_days), (max_days, float("inf"))]
            for sibling in siblings:
                sib_days = (sibling.date_of_birth - start_date).days
                invalid_day_intervals.append(
                    (sib_days - self._min_days_sibling_diff, sib_days + self._min_days_sibling_diff)
                )

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

    def create_spouse(self, tree_level: int, female: bool, spouse: Person) -> Person:
        """Create a spouse (Person instance).

        Args:
            tree_level: The level in the family tree where this person belongs
            spouse: The person who will mary the spouse output
            female: boolean indicating gender
        """

        # Generating DOB of spouse
        parent_yob = spouse.date_of_birth.year
        spouse_yob = int(random.gauss(parent_yob, self._spouse_age_diff_std))

        # Enforce max diff parent age
        spouse_yob = min(
            max(spouse_yob, parent_yob - self._max_parent_age_diff), parent_yob + self._max_parent_age_diff
        )
        spouse_dob = date(spouse_yob, random.randint(1, 12), random.randint(1, 28))

        # Generate surname
        if female:
            new_surname = spouse.surname
        else:
            new_surname = self._get_last_name(female)  # New surname for both spouses

            # We're going to void spouse's current surname -> add it back to the pool
            if not self.duplicate_names:
                self._remaining_names[spouse.surname][spouse.female].append(spouse.name)

            # For spouse, find new name which works with new_surname
            spouse.surname = new_surname
            spouse.name = self._get_first_name(spouse.female, spouse.surname)

        return self.create_person(tree_level, new_surname, spouse_dob, female)

    def create_person(
        self,
        tree_level: int,
        surname: str | None = None,
        dob: date | None = None,
        female: bool | None = None,
    ) -> Person:
        """Create a new Person instance.

        Args:
            tree_level: The level in the family tree where this person belongs
            dob: The date of birth of the individual
            dob: The date of birth of the individual
            female: Optional boolean indicating gender. If None, gender is randomly assigned
        """
        if dob is None:
            dob = date(
                tree_level * (self._max_parent_age + 1) + random.randint(1, self._max_parent_age),
                random.randint(1, 12),
                random.randint(1, 28),
            )

        if female is None:
            female = random.random() > 0.5

        if surname is None:
            surname = self._get_last_name(female)

        name = self._get_first_name(female, surname)
        self._person_counter += 1

        return Person(
            surname=surname,
            index=self._person_counter,
            name=name,
            female=female,
            tree_level=tree_level,
            date_of_birth=dob,
        )
