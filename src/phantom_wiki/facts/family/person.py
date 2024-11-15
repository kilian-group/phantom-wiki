# Family Tree Generator
#
# Copyright (C) 2018 Patrick Hohenecker
# Author/Maintainer: Patrick Hohenecker <mail@paho.at>
# URL: <https://github.com/phohenecker/family-tree-data-gen/blob/master/LICENSE>
#
# Version: 2018.1
# Date: May 30, 2018
# License: BSD-2-Clause

import abc
import typing

# TODO: can we refactor the code to remove dependency on reldata?
from reldata.data import base_individual


class Person(base_individual.BaseIndividual, metaclass=abc.ABCMeta):
    """Represents a person in a family tree."""
    
    @property
    @abc.abstractmethod
    def children(self) -> list:
        """list[Person]: All children of a ``Person``."""
        pass
    
    @property
    @abc.abstractmethod
    def female(self) -> bool:
        """bool: Indicates whether this person is female."""
        pass
    
    @property
    @abc.abstractmethod
    def married_to(self) -> typing.Optional["Person"]:
        """Person: The partner of a ``Person``, if there is one."""
        pass
    
    @married_to.setter
    @abc.abstractmethod
    def married_to(self, spouse: "Person") -> None:
        pass
    
    @property
    @abc.abstractmethod
    def parents(self) -> typing.List["Person"]:
        """list[Person]: The parents of a ``Person``."""
        pass
    
    @property
    @abc.abstractmethod
    def tree_level(self) -> int:
        """int: The level in the family tree where a ``Person`` is located."""