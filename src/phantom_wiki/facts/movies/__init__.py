# standard impors
import random
# phantom wiki functionality
from ..database import Database
from .generate import (match_create_actor, match_create_director, match_create_producer, match_create_writer, match_create_movie, match_create_person)



from pyswip import Prolog
from phantom_wiki.facts.family.constants import PERSON_TYPE

SAVE_ALL_CLAUSES_TO_FILE = """
(save_all_clauses_to_file(File) :-
    open(File, write, Stream),
    set_output(Stream),
    listing,
    close(Stream))
"""
class Database:
    # TODO this will potentially need to consult several rules files (for family vs friends etc.)
    # TODO define an API for consulting different types of formal facts (family, friendships, hobbies)
    # TODO define logic for consulting different types of facts based on difficulty
    def __init__(self, *rules: list[str]):
        self.prolog = Prolog()
        print("Consulting rules from:")
        for rule in rules:
            print(f"- {rule}")
            self.prolog.consult(rule)
        # Add ability to save clauses to a file
        self.prolog.assertz(SAVE_ALL_CLAUSES_TO_FILE)

    @classmethod
    def from_disk(cls, file: str):
        """Loads a Prolog database from a file.
        args:
            file: path to the file
        """
        db = cls()
        db.consult(file)
        return db

    def get_names(self):
        """Gets all names from a Prolog database.
        Returns:
            List of people's names.
        """
        people = [result["X"] for result in self.prolog.query(f"type(X, {PERSON_TYPE})")]
        return people

    def get_attribute_values(self):
        """Gets all attributes from a Prolog database.
        Returns:
            List of attributes.
        """
        # NOTE: if you want to be able to query for attributes, 
        # without actually having attributes in the database, 
        # you need to define the attribute predicate by uncommenting the line below
        # self.define("attribute/1")
        attributes = [result["X"] for result in self.prolog.query("attribute(X)")]
        return attributes

    def query(self, query: str):
        """Queries the Prolog database.
        args:
            query: Prolog query string
        returns:
            List of results
        """
        return list(self.prolog.query(query))

    def consult(self, *files: str):
        """Consults Prolog files.
        args:
            files: paths to Prolog files
        """
        print("Consulting files:")
        for file in files:
            print(f"- {file}")
            self.prolog.consult(file)

    def add(self, *facts: str):
        """Adds fact(s) to the Prolog database.

        The fact is added to the end of the clause list,
        which means that it will be returned last when querying.

        NOTE: This is not a persistent operation.

        args:
            facts: list of Prolog fact strings
        """
        print("Adding facts:")
        for fact in facts:
            print(f"- {fact}")
            self.prolog.assertz(fact)

    def remove(self, *facts: str):
        """Removes a fact from the Prolog database.
        Prolog allows duplicate facts, so we removes all matching facts.
        To remove only the first matching fact, use prolog.retract(fact) instead.

        NOTE: This is not a persistent operation.

        args:
            facts: list of Prolog fact strings
        """
        print("Removing facts:")
        for fact in facts:
            print(f"- {fact}")
            self.prolog.retractall(fact)

    def define(self, *predicates: str):
        """Defines dynamic predicates in the Prolog database.
        Examples:
        >>> db.define("parent/2", "sibling/2")

        args:
            predicates: list of term signatures
        """
        print("Defining rules:")
        for predicate in predicates:
            print(f"- {predicate}")
            self.prolog.dynamic(predicate)

    def save_to_disk(self, file: str):
        """Saves all clauses in the database to a file.
        args:
            file: path to the file
        """
        return self.query(f"save_all_clauses_to_file(\'{file}\').")
    

def db_generate_movies(db: Database, SQL_path: str):
    """
    Generate attributes for each person in the database.

    Args:
        db (Database): The database containing the facts.
        args (ArgumentParser): The command line arguments.

    How to create movie dataset in Prolog
    1. Create a movie: 
        movie(Title, Releaseyear).
    2. Create the people involved in the movie
        type: 
            - (TomH)-[:ACTED_IN {roles:['Hero Boy', 'Father', 'Conductor', 'Hobo', 'Scrooge', 'Santa Claus']}]->(ThePolarExpress),
                roles can be a list but for simplicity we will use a single role
                
                acted_in(Title, Actor).

            - (NancyM)-[:DIRECTED]->(SomethingsGottaGive),

                directed(Title, Director).

            - (JoelS)-[:PRODUCED]->(SpeedRacer)

                produced(Title, Producer).

            # optional 
            -  (LanaW)-[:WROTE]->(SpeedRacer),

                wrote(Title, Writer).
    """
    names = db.get_names()
    moviestars_to_residents = map_residents_to_hollywood(names, SQL_path)

    # add the facts to the database
    facts = []
    with open(SQL_path) as f:
        lines = f.readlines()
    for line in lines:
        # if matched to a line that created movie cast information, then add to prolog database
        # TODO: add corresponding job for the person in the movie (e.g. actor, director, producer, writer)
        if actor := match_create_actor(line, moviestars_to_residents):
            facts.append(actor)
            continue
        elif director := match_create_director(line, moviestars_to_residents):
            facts.append(director)
            continue
        elif producer := match_create_producer(line, moviestars_to_residents):
            facts.append(producer)
            continue
        elif writer := match_create_writer(line, moviestars_to_residents):
            facts.append(writer)
            continue

        elif movie := match_create_movie(line):
            facts.append(movie)
            continue

    db.add(*facts)


def get_names_from_SQL(SQL_path):
    """Gets the names from a movie dataset created by SQL.
    Returns:
        List of people's names that appeared in the dataset.
    """
    with open(SQL_path) as f:
        lines = f.readlines()
    hollywood_people = []
    for line in lines:
        if match_create_person(line)[0] is not None:
            hollywood_people.append(match_create_person(line)[0])
    return hollywood_people


def map_residents_to_hollywood(residents, SQL_path):
    """Sample a subset of residents to be Hollywood people.
    Returns:
        Dictionary mapping residents to Hollywood people.
    """
    # first get the names of the Hollywood people
    hollywood_people = get_names_from_SQL(SQL_path)

    if len(hollywood_people) > len(residents):
        raise ValueError("Number of Hollywood people cannot be larger than number of residents.")

    # Randomly sample from residents without replacement
    sampled_residents = random.sample(residents, len(hollywood_people))

    # Create the mapping
    moviestars_to_residents = dict(zip(hollywood_people, sampled_residents))

    return moviestars_to_residents