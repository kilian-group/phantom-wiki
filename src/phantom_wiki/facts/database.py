from pyswip import Prolog


class Database:
    # TODO this will potentially need to consult several rules files (for family vs friends etc.)
    # TODO define an API for consulting different types of formal facts (family, friendships, hobbies)
    # TODO define logic for consulting different types of facts based on difficulty
    def __init__(self, rules: list[str]):
        self.prolog = Prolog()
        print("Consulting rules from:")
        for rule in rules:
            print(f"- {rule}")
            self.prolog.consult(rule)

    def get_names(self):
        """Gets all names from a Prolog database.
        Returns:
            List of people's names.
        """
        females = [result["X"] for result in self.prolog.query("female(X)")]
        males = [result["X"] for result in self.prolog.query("male(X)")]
        nonbinary = []  # [result['X'] for result in self.prolog.query("nonbinary(X)")]
        return females + males + nonbinary

    def get_attribute_values(self):
        """Gets all attributes from a Prolog database.
        Returns:
            List of attributes.
        """
        self.define("attribute/1")
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
        args:
            predicates: list of term signatures (e.g., female/1, male/1, age/2, etc.)
        """
        print("Defining rules:")
        for predicate in predicates:
            print(f"- {predicate}")
            self.prolog.dynamic(predicate)
