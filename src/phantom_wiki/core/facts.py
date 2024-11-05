from phantom_wiki.core.data.grouped_relations import ppl_2_ppl
from phantom_wiki.family.queries import get_family_relationships


def get_family_facts(names: list[str]) -> dict[str, list[str]]:
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
