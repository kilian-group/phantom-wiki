"""Functionality for generating articles from facts.

The article generation pipeline comprises two stages:
1. Querying the database for Prolog facts
We currently support two types of facts:
- relations, which includes family relations and friendship relations
- attributes, which includes hobbies, jobs, dates of birth, and genders

TODO (Albert): add support for ternary predicates

2. Converting each Prolog fact to a natural-language sentence using templates
Each Prolog predicate is associated with a template that specifies how to convert
a fact with that predicate to a natural-language sentence. For example, the Prolog
predicate hobby/2 is associated with the template "The hobby of <subject> is".
Note that some predicates have multiple templates to handle singular and plural cases.

TODO (Albert): figure out a better way of storing the following information
- templates (singular and plural)
- aliases (e.g., dob -> date-of-birth)
- choices (e.g., set of all hobbies) and probability of choosing each choice (e.g., uniform)
- whether we include the predicate in articles
- whether we include the predicate in questions
NOTE: for templates, we could also consider introducing a syntax for translating from
Prolog facts to natural-language sentences. For example,
- sibling(X, Y) -> "The sibling of <X> is <Y>." and "The siblings of <X> are <Y>."
- hobby(X, Y) -> "The hobby of <X> is <Y>."
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
    family_sentences, family_facts = get_relations(
        db, names, relation_list, FAMILY_FACT_TEMPLATES, FAMILY_FACT_TEMPLATES_PL
    )
    friend_sentences, friend_facts = get_relations(
        db, names, FRIENDSHIP_RELATION, FRIENDSHIP_FACT_TEMPLATES, FRIENDSHIP_FACT_TEMPLATES_PL
    )
    attribute_sentences, attribute_facts = get_attributes(
        db, names, ATTRIBUTE_TYPES + ["gender"], ATTRIBUTE_FACT_TEMPLATES
    )

    articles = {}
    for name in names:
        article = BASIC_ARTICLE_TEMPLATE.format(
            name=name,
            family_facts="\n".join(family_sentences[name]),
            friend_facts="\n".join(friend_sentences[name]),
            attribute_facts="\n".join(attribute_sentences[name]),
        )
        facts = family_facts[name] + friend_facts[name] + attribute_facts[name]
        articles[name] = (article, facts)
    return articles


#
# Functionality to get relation sentences
#
def get_relations(
    db: Database,
    names: list[str],
    relation_list: list[str],
    relation_templates: dict[str, str],
    relation_templates_plural: dict[str, str],
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
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
    facts = defaultdict(list)
    for name in names:
        for relation in relation_list:
            # create list of answers for each relation
            target = []

            query = f'distinct({relation}("{name}", X))'
            for result in db.query(query):
                decoded_result = decode(result["X"])
                target.append(decoded_result)
                facts[name].append(f'{relation}("{name}", "{decoded_result}").')

            if not target:
                continue
            # Choose the appropriate template based on the number of targets
            if len(target) > 1:
                relation_template = relation_templates_plural[relation]
            else:
                relation_template = relation_templates[relation]
            # Construct the sentence
            sent = relation_template.replace("<subject>", name) + " " + ", ".join(target) + "."
            # Append the sentence to the list of sentences for the person
            sents[name].append(sent)
    return sents, facts


#
# Functionality to get attribute sentences
#
def get_attributes(
    db: Database,
    names: list[str],
    attribute_list: list[str],
    attribute_templates: dict[str, str],
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Get attribute sentences for a list of names.

    Args:
        db: Database object
        names: list of names
    Returns:
        dict of sentences for each name
    """
    sents = defaultdict(list)
    facts = defaultdict(list)
    for name in names:
        for attr in attribute_list:
            # create list of answers for each attribute
            target = []
            query = f'{attr}("{name}", X)'
            for result in db.query(query):
                decoded_result = decode(result["X"])
                target.append(decoded_result)
                facts[name].append(f'{attr}("{name}", "{decoded_result}").')
            if not target:
                continue
            # Construct the sentence
            attr_template = attribute_templates[attr]
            sent = attr_template.replace("<subject>", name) + " " + ", ".join(target) + "."
            # Append the sentence to the list of sentences for the person
            sents[name].append(sent)
    return sents, facts
