import logging
from multiprocessing import Pool

from pyswip import Prolog
from tqdm import tqdm

from phantom_wiki.facts.family.constants import PERSON_TYPE
from phantom_wiki.utils import decode

SAVE_ALL_CLAUSES_TO_FILE = """
(save_all_clauses_to_file(File) :-
    open(File, write, Stream),
    set_output(Stream),
    listing,
    close(Stream))
"""


class Database:
    def __init__(self, *rules: str):
        self.prolog = Prolog()
        logging.debug("Consulting rules from:")
        for rule in rules:
            logging.debug(f"- {rule}")
            self.prolog.consult(rule)
        # Add ability to save clauses to a file
        self.prolog.assertz(SAVE_ALL_CLAUSES_TO_FILE)

    @classmethod
    def from_disk(cls, file: str):
        """Loads a Prolog database from a file.

        Args:
            file: path to the file
        """
        db = cls()
        db.consult(file)
        return db

    def get_person_names(self) -> list[str]:
        """Gets the names of all people in the Prolog database.

        Returns:
            List of people's names.
        """
        people = [decode(result["X"]) for result in self.prolog.query(f"type(X, {PERSON_TYPE})")]
        return people

    def get_attribute_values(self) -> list[str]:
        """Gets all attribute values from the Prolog database.

        Returns:
            List of attribute values present in the database (e.g. specific jobs like "architect",
              hobbies like "running")
        """

        # Defining the `attribute` predicate allows querying for attributes
        # even when none are defined in the database
        self.define("attribute/1")
        attributes = [decode(result["X"]) for result in self.prolog.query("attribute(X)")]
        return attributes

    def batch_query(self, queries: list[str], multi_threading: bool = False) -> list[list[dict]]:
        """Queries the Prolog database with multiple queries. If multi_threading
         is true, then this function leverages multi processors.

        Args:
            queries: List of Prolog query strings

        Returns:
            List of results for each query
        """
        if multi_threading:
            with Pool() as pool:
                results = []
                for result in tqdm(
                    pool.imap(self.query, queries), total=len(queries), desc="Querying the database"
                ):
                    results.append(result)

        else:
            results = []
            for q in tqdm(queries, desc="Querying the database"):
                results.append(self.query(q))

        return results

    def query(self, query: str) -> list[dict]:
        """Queries the Prolog database.

        Args:
            query: Prolog query string

        Returns:
            List of results
        """
        return list(self.prolog.query(query))

    def consult(self, *files: str) -> None:
        """Consults Prolog files.

        Args:
            files: paths to Prolog files
        """
        logging.debug("Consulting files:")
        for file in files:
            logging.debug(f"- {file}")
            self.prolog.consult(file)

    def add(self, *facts: str) -> None:
        """Adds fact(s) to the Prolog database.

        The fact is added to the end of the clause list, which means that it will be returned last when
        querying.

        NOTE: This is not a persistent operation.

        Args:
            facts: list of Prolog fact strings
        """
        logging.debug("Adding facts:")
        for fact in facts:
            logging.debug(f"- {fact}")
            self.prolog.assertz(fact)

    def remove(self, *facts: str) -> None:
        """Removes a fact from the Prolog database.

        Prolog allows duplicate facts, so this removes all matching facts.
        To remove only the first matching fact, use prolog.retract(fact) instead.

        NOTE: This is not a persistent operation.

        Args:
            facts: list of Prolog fact strings
        """
        logging.debug("Removing facts:")
        for fact in facts:
            logging.debug(f"- {fact}")
            self.prolog.retractall(fact)

    def define(self, *predicates: str) -> None:
        """Defines dynamic predicates in the Prolog database.

        Examples:
        >>> db.define("parent/2", "sibling/2")

        Args:
            predicates: list of term signatures
        """
        logging.debug("Defining rules:")
        for predicate in predicates:
            logging.debug(f"- {predicate}")
            self.prolog.dynamic(predicate)

    def save_to_disk(self, file: str) -> None:
        """Saves all clauses in the database to a file.

        Args:
            file: path to the file
        """
        self.query(f"save_all_clauses_to_file('{file}').")
