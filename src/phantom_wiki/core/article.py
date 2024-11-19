
from faker import Faker
from nltk import CFG
from nltk.parse.generate import generate

from .generative import generate_cfg_openai
from ..utils.parsing import format_generated_cfg
from .constants.article_templates import BASIC_ARTICLE_TEMPLATE
from ..facts import Database
from ..facts.attributes import get_attribute_facts
from ..facts.family import (FAMILY_FACT_TEMPLATES, 
                            FAMILY_RELATION_EASY)
from ..facts.friends import (FRIENDSHIP_RELATION, 
                             FRIENDSHIP_FACT_TEMPLATES,)

def get_articles(db: Database, names: list[str]) -> dict:
    # get family article
    family_facts = get_relation_facts(db, names, FAMILY_RELATION_EASY, FAMILY_FACT_TEMPLATES)
    # get friendship article
    friend_facts = get_relation_facts(db, names, FRIENDSHIP_RELATION, FRIENDSHIP_FACT_TEMPLATES)
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
        query = f"{relation}(\'{name}\', X)"
        results = [result['X'] for result in db.query(query)]
        relations[relation] = results

    return relations


# 
# WIP: Functionality to generate articles using CFGs
# 
def generate_llm_article_cfg_pairs(
    person_list: list[str], use_jobs=True, max_attempts=10
) -> dict[str, tuple[str, str]]:
    pairs = {}
    if use_jobs:
        fake = Faker()
    for person in person_list:
        if use_jobs:
            job = fake.job()
        else:
            job = "unknown"

        for _ in range(max_attempts):
            try:
                generated_cfg = generate_cfg_openai(person, job)
                formatted_cfg = format_generated_cfg(generated_cfg)
                cfg = CFG.fromstring(formatted_cfg)
                article = " ".join(generate(cfg))
                break
            except Exception as e:
                print(f"[Attempt {_}] Error generating CFG and article for {person}: {e}")
                cfg = None
                article = None
                continue

        if article is None:
            print(f"Failed to generate CFG and article for {person}")
            continue
        else:
            pairs[person] = (article, cfg.tostring())

    return pairs