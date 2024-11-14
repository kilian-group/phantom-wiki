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
import typing

import insanity

from reldata.data import base_individual
from reldata.data import data_context as dc
from reldata.data import individual_factory

import person

# ==================================================================================================================== #
#  CLASS  P E R S O N  F A C T O R Y                                                                                   #
# ==================================================================================================================== #

class PersonFactory(object):
    """A factory class for creating instances of an implementation of :class:`person.Person`."""

    _REMAINING_FEMALE_NAMES = "PersonFactory.remaining_female_names"
    """str: The key that is used for storing the remaining female names in the context."""

    _REMAINING_MALE_NAMES = "PersonFactory.remaining_male_names"
    """str: The key that is used for storing the remaining male names in the context."""
    
    # Method to load names from JSON files
    @staticmethod
    def load_names_from_file(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)

    FEMALE_NAMES = load_names_from_file.__func__('names/female_names.json')
    """list[str]: A list of all known female names."""
    
    MALE_NAMES = load_names_from_file.__func__('names/male_names.json')
    """list[str]: A list of all known male names."""
    
    #  METHODS  ########################################################################################################
    
    @classmethod
    def _prepare_context(cls):
        """Prepares the current context for the ``PersonFactory`` if it is not prepared yet."""
        if dc.DataContext.get_context()[cls._REMAINING_FEMALE_NAMES] is None:
            cls.reset()
    
    @classmethod
    def create_person(cls, tree_level: int, female: bool=None) -> person.Person:
        """Constructs a new instance of :class:`person.Person`.

        Args:
            tree_level (int): The level in the family tree on which the created person is located.
            female (bool, optional): Indicates whether the created person is female. If not provided, then the gender
                is sampled randomly.
        """
        # sanitize args
        insanity.sanitize_type("tree_level", tree_level, int)
        
        # prepare context if necessary
        cls._prepare_context()
        
        # fetch current context
        ctx = dc.DataContext.get_context()
        
        # determine gender
        if female is None:
            female = random.random() > 0.5
        else:
            female = bool(female)
        
        # fetching names that may be used
        if female:
            remaining_names = ctx[cls._REMAINING_FEMALE_NAMES]
        else:
            remaining_names = ctx[cls._REMAINING_MALE_NAMES]
        
        # determine name
        name_index = random.randrange(len(remaining_names))
        name = remaining_names[name_index]
        del remaining_names[name_index]
        
        # check whether the just used list of names has to be reset (i.e., is empty now)
        # -> we just reuse known names and append a postfix to ensure uniquenes
        if not remaining_names:
            
            # determine the postfix to append to the new names
            postfix = re.search("([0-9]+)$", name)  # -> the previously used postfix
            if postfix:
                postfix = str(int(postfix.group(0)) + 1)  # increment existing postfix
            else:
                postfix = "2"  # start with postfix 2
            
            # create new names to use
            if female:
                ctx[cls._REMAINING_FEMALE_NAMES] = [n + postfix for n in cls.FEMALE_NAMES]
            else:
                ctx[cls._REMAINING_MALE_NAMES] = [n + postfix for n in cls.MALE_NAMES]
        
        # return new person
        return individual_factory.IndividualFactory.create_individual(
                name,
                target_type=_Person,
                args=[female, tree_level]
        )
    
    @classmethod
    def reset(cls) -> None:
        """Resets the ``PersonFactory`` to its initial state."""
        ctx = dc.DataContext.get_context()
        ctx[cls._REMAINING_FEMALE_NAMES] = cls.FEMALE_NAMES[:]
        ctx[cls._REMAINING_MALE_NAMES] = cls.MALE_NAMES[:]


# ==================================================================================================================== #
#  CLASS  _ P E R S O N                                                                                                #
# ==================================================================================================================== #


class _Person(person.Person):
    """A private implementation of :class:`person.Person`."""
    
    def __init__(self, index: int, name: str, female: bool, tree_level: int):
        base_individual.BaseIndividual.__init__(self)
        
        self._children = []
        self._female = female
        self._index = index
        self._married_to = None
        self._name = name
        self._parents = []
        self._tree_level = tree_level
    
    #  MAGIC FUNCTIONS  ################################################################################################
    
    def __str__(self):
        return "Person(index = {:d}, name = '{}', female = {}, married_to = {}, parents = {}, children = [{}])".format(
                self.index,
                self.name,
                str(self.female),
                str(self.married_to.index) if self.married_to else "None",
                "({})".format(", ".join([str(p.index) for p in self.parents])) if self.parents else "None",
                ", ".join([str(c.index) for c in self.children])
        )
    
    #  PROPERTIES  #####################################################################################################
    
    @property
    def children(self) -> typing.List[person.Person]:
        return self._children
    
    @property
    def female(self) -> bool:
        return self._female
    
    @property
    def married_to(self) -> typing.Union[typing.Any, None]:
        return self._married_to
    
    @married_to.setter
    def married_to(self, spouse: person.Person) -> None:
        insanity.sanitize_type("spouse", spouse, person.Person)
        self._married_to = spouse
    
    @property
    def parents(self) -> typing.List[person.Person]:
        return self._parents
    
    @property
    def tree_level(self) -> int:
        return self._tree_level
