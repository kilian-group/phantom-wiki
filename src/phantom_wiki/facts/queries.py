# TODO: to review

import janus_swi as janus
from pyswip import Prolog

from phantom_wiki.facts.family.constants import FAMILY_FACT_TEMPLATES


def get_family_relationships(name: str) -> dict:
    # TODO make sure a proper Prolog query is present for each template in FAMILY_FACT_TEMPLATES
    """
    Get the following relationships for a given name:
    - mother
    - father
    - siblings
    - children
    - wife/husband

    Assumes that the prolog files are loaded and the predicates are defined in the prolog files.
    This can be done using the following code:
    ```
    janus.query_once("consult('../../tests/family_tree.pl')")
    janus.query_once("consult('./family/rules.pl')")
    ```

    Ref: https://www.swi-prolog.org/pldoc/man?section=janus-call-prolog
    """
    # name = 'elias'
    relations = {}
    # get mother
    if mother := janus.query_once("mother(X, Y)", {"Y": name})["X"]:
        relations["mother"] = mother
    # print(mother)
    # get father
    if father := janus.query_once("father(X, Y)", {"Y": name})["X"]:
        relations["father"] = father
    # print(father)
    # get siblings
    if siblings := [sibling["X"] for sibling in janus.query("sibling(X, Y)", {"Y": name})]:
        relations["sibling"] = ", ".join(siblings)
    # print(list(siblings))
    # get children
    if children := [child["X"] for child in list(janus.query("child(X, Y)", {"Y": name}))]:
        relations["child"] = ", ".join(children)
        relations["number of children"] = len(children)
    # print(list(children))

    # TODO: get wife and husband
    if spouse := (
        janus.query_once(f"husband(X, Y)", {"X": name})["Y"]
        or janus.query_once(f"wife(X, Y)", {"X": name})["Y"]
    ):
        relations["spouse"] = spouse

    # facts = []
    # for relation, target in relations.items():
    #     relation_template = ppl_2_ppl[relation]
    #     fact = relation_template.replace("<subject>", name) + " " + str(target) + "."
    #     facts.append(fact)

    # article = "\n".join(facts)
    # return article

    return relations


def get_family_facts(names: list[str]) -> dict[str, list[str]]:
    # TODO: add docstring
    # TODO: add an argument to regulate depth/complexity of the facts
    #   (e.g. how many (types of) relations to include)
    facts = {}
    for name in names:
        relations = get_family_relationships(name)

        person_facts = []
        for relation, target in relations.items():
            relation_template = FAMILY_FACT_TEMPLATES[relation]
            fact = relation_template.replace("<subject>", name) + " " + str(target) + "."
            person_facts.append(fact)

        facts[name] = person_facts

    return facts

def get_names(facts_file: str) -> list[str]:
    """Gets all names from a Prolog database.

    Args:
        facts_file: file that defines the formal facts
    
    Returns: 
        List of people's names.
    """
    names = []
    with open(facts_file,'r') as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith('female') or line.startswith('male'):
                # scrape the text in parentheses as people's names
                name = line.split('(')[1].split(')')[0].split(',')
                names.append(name[0])
    
    return names



class FamilyDatabase:
    # TODO this will potentially need to consult several rules files (for family vs friends etc.)
    # TODO define an API for consulting different types of formal facts (family, friendships, hobbies)
    # TODO define logic for consulting different types of facts based on difficulty
    def __init__(self, facts_file: str, rules_file: str):
        self.facts_file = facts_file
        self.rules_file = rules_file
        self.prolog = Prolog()
        self.prolog.consult(facts_file)
        self.prolog.consult(rules_file)

    def get_family_relationships(self, name: str) -> dict:
        return get_family_relationships(name)

    def get_names(self): 
        return get_names(self.facts_file)
