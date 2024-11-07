import janus_swi as janus

from phantom_wiki.family.constants import FAMILY_FACT_TEMPLATES


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
        janus.query_once("husband(X, Y)", {"X": name}) or janus.query_once("wife(X, Y)", {"X": name})
    )["Y"]:
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


class FamilyDatabase:
    def __init__(self, facts_file: str, rules_file: str):
        janus.query_once(f"consult('{facts_file}')")
        janus.query_once(f"consult('{rules_file}')")

    def get_family_relationships(self, name: str) -> dict:
        return get_family_relationships(name)

    def get_names():
        pass  # TODO and replace get_names_from_file
