from typing import List, Dict

from faker import Faker
from nltk import CFG
from nltk.parse.generate import generate

from .generative import generate_cfg_openai
from ..utils.parsing import format_generated_cfg

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

from .constants.article_templates import BASIC_ARTICLE_TEMPLATE
from ..facts import Database
from ..facts.family import get_family_facts
def get_articles(db: Database, names: List[str]) -> Dict:
    articles = {}
    # get family article
    family_facts = get_family_facts(db, names)
    # TODO: get hobby facts
    # TODO: get friendship facts

    for name in names:
        articles[name] = BASIC_ARTICLE_TEMPLATE.format(
            family_facts[name],
            "unknown",
            "unknown"
        )
    return articles