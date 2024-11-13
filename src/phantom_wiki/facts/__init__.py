# 
# Class for interfacing with Prolog database.
# 
from typing import List
from pyswip import Prolog
from pkg_resources import resource_filename

class Database:
    # TODO this will potentially need to consult several rules files (for family vs friends etc.)
    # TODO define an API for consulting different types of formal facts (family, friendships, hobbies)
    # TODO define logic for consulting different types of facts based on difficulty
    def __init__(self):
        self.prolog = Prolog()
        print("Consulting built-in family rules...")
        base_rules_path = resource_filename(__name__, "facts/family/base_rules.pl")
        derived_rules_path = resource_filename(__name__, "facts/family/derived_rules.pl")
        self.prolog.consult(base_rules_path)
        self.prolog.consult(derived_rules_path)
        # TODO: consult friends rules

    @classmethod
    def from_facts(cls, *data_paths: str):
        """Creates a Database object from a list of rules files.
        args:
            data_paths: list of paths containing facts
        returns:
            Database object
        """
        db = cls()
        for path in data_paths:
            print(f"Consulting {path}...")
            db.consult(path)
        return db

    def get_names(self): 
        """Gets all names from a Prolog database.
        Returns: 
            List of people's names.
        """
        females = [result['X'] for result in self.prolog.query("female(X)")]
        males = [result['X'] for result in self.prolog.query("male(X)")]
        return females + males
    
    def query(self, query: str):
        """Queries the Prolog database.
        args:
            query: Prolog query string
        returns:
            List of results
        """
        return list(self.prolog.query(query))
    
    def consult(self, file: str):
        """Consults a Prolog file.
        args:
            file: path to Prolog file
        """
        self.prolog.consult(file)
