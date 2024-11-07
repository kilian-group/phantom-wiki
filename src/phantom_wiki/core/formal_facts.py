from phantom_wiki.core.data.grouped_relations import ppl_2_ppl
from phantom_wiki.family.queries import get_family_relationships


# TODO: split grouped_relations by type and move get_family_facts to queries.py.
def get_family_facts(names: list[str]) -> dict[str, list[str]]:
    # TODO: add docstring
    # TODO: add an argument to regulate depth/complexity of the facts (e.g. how many (types of) relations to include)
    facts = {}
    for name in names:
        relations = get_family_relationships(name)

        person_facts = []
        for relation, target in relations.items():
            relation_template = ppl_2_ppl[relation]
            fact = relation_template.replace("<subject>", name) + " " + str(target) + "."
            person_facts.append(fact)

        facts[name] = person_facts

    return facts
