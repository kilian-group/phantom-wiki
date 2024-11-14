
from faker import Faker
from nltk import CFG
from nltk.parse.generate import generate

from .generative import generate_cfg_openai
from ..utils.parsing import format_generated_cfg
from .constants.article_templates import BASIC_ARTICLE_TEMPLATE
from ..facts import Database
from ..facts.family import get_family_facts
from ..facts.attributes import get_attribute_facts

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

def get_articles(db: Database, names: list[str]) -> dict:
    # get family article
    family_facts = get_family_facts(db, names)
    # TODO: get friendship facts
    # TODO: get attributes
    attribute_facts = get_attribute_facts(db, names)
    
    # import pdb; pdb.set_trace()
    articles = {}
    for name in names:
        article = BASIC_ARTICLE_TEMPLATE.format(
            name=name,
            family_facts="\n".join(family_facts[name]),
            friend_facts="unknown",
            attribute_facts="\n".join(attribute_facts[name]),
        )
        # print(article)
        articles[name] = article
    return articles