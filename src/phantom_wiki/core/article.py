"""Functionality for generating articles from facts.

The article generation pipeline comprises two stages:
1. Querying the database for Prolog facts
We currently support two types of facts:
- relations, which includes family relations and friendship relations
- attributes, which includes hobbies, jobs, dates of birth, and genders
TODO: add support for ternary predicates

2. Converting each Prolog fact to a natural-language sentence using templates
Each Prolog predicate is associated with a template that specifies how to convert
a fact with that predicate to a natural-language sentence. For example, the Prolog
predicate hobby/2 is associated with the template "The hobby of <subject> is".
Note that some predicates have multiple templates to handle singular and plural cases.
TODO: figure out a better way of storing the following information
- templates (singular and plural)
- aliases (e.g., dob -> date-of-birth)
- choices (e.g., set of all hobbies) and probability of choosing each choice (e.g., uniform)
- whether we include the predicate in articles
- whether we include the predicate in questions
"""

from collections import defaultdict

from ..facts import Database
from ..facts.attributes.constants import ATTRIBUTE_FACT_TEMPLATES, ATTRIBUTE_TYPES
from ..facts.family import FAMILY_RELATION_EASY
from ..facts.family.constants import FAMILY_FACT_TEMPLATES, FAMILY_FACT_TEMPLATES_PL
from ..facts.friends.constants import (
    FRIENDSHIP_FACT_TEMPLATES,
    FRIENDSHIP_FACT_TEMPLATES_PL,
    FRIENDSHIP_RELATION,
)
from ..utils import decode
from .constants.article_templates import BASIC_ARTICLE_TEMPLATE


def get_articles(db: Database, names: list[str]) -> dict:
    """Construct articles for a list of names.

    Args:
        db: Database object
        names: list of names
    Returns:
        dict of articles for each name
    """
    # HACK: Do not include parent, child, and sibling in the articles
    relation_list = [r for r in FAMILY_RELATION_EASY if r not in ["parent", "child", "sibling"]]
    family_sentences = get_relation_sentences(
        db, names, relation_list, FAMILY_FACT_TEMPLATES, FAMILY_FACT_TEMPLATES_PL
    )
    friend_sentences = get_relation_sentences(
        db, names, FRIENDSHIP_RELATION, FRIENDSHIP_FACT_TEMPLATES, FRIENDSHIP_FACT_TEMPLATES_PL
    )
    attribute_sentences = get_attribute_sentences(db, names)

    articles = {}
    for name in names:
        article = BASIC_ARTICLE_TEMPLATE.format(
            name=name,
            family_facts="\n".join(family_sentences[name]),
            friend_facts="\n".join(friend_sentences[name]),
            attribute_facts="\n".join(attribute_sentences[name]),
        )
        articles[name] = article
    return articles


#
# Functionality to get relation sentences
#
def get_relation_sentences(
    db: Database,
    names: list[str],
    relation_list: list[str],
    relation_templates: dict[str, str],
    relation_templates_plural: dict[str, str],
) -> dict[str, list[str]]:
    """
    Get relation sentences for a list of names.

    Args:
        db: Database object
        names: list of names
        relation_list: list of relations to query
        relation_templates: dict of relation templates for
            constructing fact sentences
    Returns:
        dict of facts for each name
    """
    sents = defaultdict(list)
    for name in names:
        relations = get_relations(db, name, relation_list)
        for relation, target in relations.items():
            if not target:
                continue
            if len(target) > 1:
                relation_template = relation_templates_plural[relation]
            else:
                relation_template = relation_templates[relation]
            fact = relation_template.replace("<subject>", name) + " " + ", ".join(target) + "."
            sents[name].append(fact)
    return sents


def get_relations(db: Database, name: str, relation_list: list[str]) -> dict:
    """
    Get the results for all relations in the specified `relation_list`
    for a given `name`.
    """
    relations = {}
    for relation in relation_list:
        query = f'distinct({relation}("{name}", X))'
        results = [decode(result["X"]) for result in db.query(query)]
        relations[relation] = results

    return relations


#
# Functionality to get attribute sentences
#
def get_attribute_sentences(db: Database, names: list[str]) -> dict[str, list[str]]:
    """Get attribute sentences for a list of names.

    Args:
        db: Database object
        names: list of names
    Returns:
        dict of sentences for each name
    """
    sents = defaultdict(list)
    for name in names:
        attributes = get_attributes(db, name)
        for attr, target in attributes.items():
            if target == []:
                continue
            attr_template = ATTRIBUTE_FACT_TEMPLATES[attr]
            fact = attr_template.replace("<subject>", name) + " " + ", ".join([str(s) for s in target]) + "."
            sents[name].append(fact)
    return sents


def get_attributes(db: Database, name: str):
    """
    Get attributes for each person in the database.
    """
    attributes = {}
    # HACK: Include "gender" as an attribute type when generating articles
    attribute_type_in_articles = ATTRIBUTE_TYPES + ["gender"]
    for attr in attribute_type_in_articles:
        query = f'{attr}("{name}", X)'
        results = [decode(result["X"]) for result in db.query(query)]
        attributes[attr] = results
    return attributes
