from ..facts import Database
from ..facts.attributes import get_attribute_facts
from ..facts.family import FAMILY_FACT_TEMPLATES, FAMILY_FACT_TEMPLATES_PL, FAMILY_RELATION_EASY
from ..facts.friends import FRIENDSHIP_FACT_TEMPLATES, FRIENDSHIP_FACT_TEMPLATES_PL, FRIENDSHIP_RELATION
from .constants.article_templates import BASIC_ARTICLE_TEMPLATE


def get_articles(db: Database, names: list[str]) -> dict:
    # get family article
    family_facts = get_relation_facts(
        db, names, FAMILY_RELATION_EASY, FAMILY_FACT_TEMPLATES, FAMILY_FACT_TEMPLATES_PL
    )
    # get friendship article
    friend_facts = get_relation_facts(
        db, names, FRIENDSHIP_RELATION, FRIENDSHIP_FACT_TEMPLATES, FRIENDSHIP_FACT_TEMPLATES_PL
    )
    # TODO: get attributes
    attribute_facts = get_attribute_facts(db, names)

    # import pdb; pdb.set_trace()
    articles = {}
    for name in names:
        article = BASIC_ARTICLE_TEMPLATE.format(
            name=name,
            family_facts="\n".join(family_facts[name]),
            friend_facts="\n".join(friend_facts[name]),
            attribute_facts="\n".join(attribute_facts[name]),
        )
        # print(article)
        articles[name] = article
    return articles


#
# Functionality to get relation-based facts
#
def get_relation_facts(
    db: Database,
    names: list[str],
    relation_list: list[str],
    relation_templates: dict[str, str],
    relation_templates_plural: dict[str, str],
) -> dict[str, list[str]]:
    """
    Get relation-based facts for a list of names.

    Args:
        db: Database object
        names: list of names
        relation_list: list of relations to query
        relation_templates: dict of relation templates for
            constructing fact sentences
    Returns:
        dict of facts for each name
    """
    facts = {}
    for name in names:
        relations = get_relations(db, name, relation_list)

        person_facts = []
        for relation, target in relations.items():
            if not target:
                continue
            if len(target) > 1:
                relation_template = relation_templates_plural[relation]
            else:
                relation_template = relation_templates[relation]
            fact = relation_template.replace("<subject>", name) + " " + ", ".join(target) + "."
            person_facts.append(fact)

        facts[name] = person_facts

    return facts


def get_relations(db: Database, name: str, relation_list: list[str]) -> dict:
    """
    Get the results for all relations in the specified `relation_list`
    for a given `name`.
    """
    relations = {}
    for relation in relation_list:
        query = f"distinct({relation}(\"{name}\", X))"
        results = [result["X"].decode('utf-8') for result in db.query(query)]
        relations[relation] = results

    return relations
