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
from .constants.article_templates import BASIC_ARTICLE_TEMPLATE, TEMPORAL_ARTICLE_TEMPLATE


def get_articles(db: Database, names: list[str], num_procs: int, include_temporal: bool = False) -> dict:
    """Construct articles for a list of names.

    Args:
        db: Database object
        names: list of names
        num_procs: number of worker processes for batched queries (1 = serial).
        include_temporal: if True, include temporal life events section
    Returns:
        dict of articles for each name
    """
    # HACK: Do not include parent, child, and sibling in the articles
    relation_list = [r for r in FAMILY_RELATION_EASY if r not in ["parent", "child", "sibling"]]
    family_sentences, family_facts = get_relations(
        db, names, relation_list, FAMILY_FACT_TEMPLATES, FAMILY_FACT_TEMPLATES_PL, num_procs
    )
    friend_sentences, friend_facts = get_relations(
        db, names, FRIENDSHIP_RELATION, FRIENDSHIP_FACT_TEMPLATES, FRIENDSHIP_FACT_TEMPLATES_PL, num_procs
    )
    attribute_sentences, attribute_facts = get_attributes(
        db, names, ATTRIBUTE_TYPES + ["gender"], ATTRIBUTE_FACT_TEMPLATES, num_procs
    )

    temporal_sentences = defaultdict(list)
    temporal_facts_map = defaultdict(list)
    if include_temporal:
        temporal_sentences, temporal_facts_map = get_temporal_sentences(db, names)

    articles = {}
    for name in names:
        if include_temporal and temporal_sentences[name]:
            article = TEMPORAL_ARTICLE_TEMPLATE.format(
                name=name,
                family_facts="\n".join(family_sentences[name]),
                friend_facts="\n".join(friend_sentences[name]),
                attribute_facts="\n".join(attribute_sentences[name]),
                temporal_facts="\n".join(temporal_sentences[name]),
            )
        else:
            article = BASIC_ARTICLE_TEMPLATE.format(
                name=name,
                family_facts="\n".join(family_sentences[name]),
                friend_facts="\n".join(friend_sentences[name]),
                attribute_facts="\n".join(attribute_sentences[name]),
            )
        facts = (
            family_facts[name]
            + friend_facts[name]
            + attribute_facts[name]
            + temporal_facts_map[name]
        )
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
    num_procs: int,
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

    pairs = [(name, relation) for name in names for relation in relation_list]
    queries = [f'distinct({rel}("{nm}", X))' for nm, rel in pairs]
    all_results = db.batch_query(queries, num_procs)

    name_rel_to_targets: dict[tuple[str, str], list[str]] = {}
    for (name, relation), results in zip(pairs, all_results):
        target = []
        for result in results:
            decoded_result = decode(result["X"])
            target.append(decoded_result)
            facts[name].append(f'{relation}("{name}", "{decoded_result}").')
        name_rel_to_targets[(name, relation)] = target

    for name in names:
        for relation in relation_list:
            target = name_rel_to_targets[(name, relation)]
            if not target:
                continue
            if len(target) > 1:
                relation_template = relation_templates_plural[relation]
            else:
                relation_template = relation_templates[relation]
            sent = relation_template.replace("<subject>", name) + " " + ", ".join(target) + "."
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
    num_procs: int,
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Get attribute sentences for a list of names.

    Args:
        db: Database object
        names: list of names
        num_procs: number of worker processes for batched queries (1 = serial).
    Returns:
        dict of sentences for each name
    """
    sents = defaultdict(list)
    facts = defaultdict(list)

    pairs = [(name, attr) for name in names for attr in attribute_list]
    queries = [f'{attr}("{nm}", X)' for nm, attr in pairs]
    all_results = db.batch_query(queries, num_procs)

    name_attr_to_targets: dict[tuple[str, str], list[str]] = {}
    for (name, attr), results in zip(pairs, all_results):
        target = []
        for result in results:
            decoded_result = decode(result["X"])
            target.append(decoded_result)
            facts[name].append(f'{attr}("{name}", "{decoded_result}").')
        name_attr_to_targets[(name, attr)] = target

    for name in names:
        for attr in attribute_list:
            target = name_attr_to_targets[(name, attr)]
            if not target:
                continue
            attr_template = attribute_templates[attr]
            sent = attr_template.replace("<subject>", name) + " " + ", ".join(target) + "."
            sents[name].append(sent)
    return sents, facts


#
# Functionality to get temporal event sentences
#
def get_temporal_sentences(
    db: Database,
    names: list[str],
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Get temporal event sentences for a list of names.

    Args:
        db: Database object
        names: list of names
    Returns:
        tuple of (sentences dict, facts dict) for each name
    """
    from ..facts.temporal.constants import TEMPORAL_FACT_TEMPLATES

    sents = defaultdict(list)
    facts = defaultdict(list)

    for name in names:
        # Education events
        for r in db.query(f'education("{name}", School, Year)'):
            school = decode(r["School"])
            year = int(r["Year"])
            sent = TEMPORAL_FACT_TEMPLATES["education"].format(name=name, school=school, year=year)
            sents[name].append(sent)
            facts[name].append(f'education("{name}", "{school}", {year}).')

        # Career events (sorted by start year)
        career_results = list(db.query(f'career("{name}", Job, Company, Start, End)'))
        career_results.sort(key=lambda r: int(r["Start"]))
        for r in career_results:
            job = decode(r["Job"])
            company = decode(r["Company"])
            start = int(r["Start"])
            end = int(r["End"])
            if end == 9999:
                sent = TEMPORAL_FACT_TEMPLATES["career_current"].format(
                    name=name, job=job, company=company, start_year=start
                )
            else:
                sent = TEMPORAL_FACT_TEMPLATES["career"].format(
                    name=name, job=job, company=company, start_year=start, end_year=end
                )
            sents[name].append(sent)
            facts[name].append(f'career("{name}", "{job}", "{company}", {start}, {end}).')

        # Marriage year events
        for r in db.query(f'marriage_year("{name}", Spouse, Year)'):
            spouse = decode(r["Spouse"])
            year = int(r["Year"])
            sent = TEMPORAL_FACT_TEMPLATES["marriage_year"].format(name=name, spouse=spouse, year=year)
            sents[name].append(sent)
            facts[name].append(f'marriage_year("{name}", "{spouse}", {year}).')

        # Lived-in events (sorted by start year)
        lived_results = list(db.query(f'lived_in("{name}", City, Start, End)'))
        lived_results.sort(key=lambda r: int(r["Start"]))
        for r in lived_results:
            city = decode(r["City"])
            start = int(r["Start"])
            end = int(r["End"])
            if end == 9999:
                sent = TEMPORAL_FACT_TEMPLATES["lived_in_current"].format(
                    name=name, city=city, start_year=start
                )
            else:
                sent = TEMPORAL_FACT_TEMPLATES["lived_in"].format(
                    name=name, city=city, start_year=start, end_year=end
                )
            sents[name].append(sent)
            facts[name].append(f'lived_in("{name}", "{city}", {start}, {end}).')

    return sents, facts
