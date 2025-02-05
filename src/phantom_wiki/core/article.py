from ..facts import Database
from ..facts.attributes import get_attribute_facts
from ..facts.family import FAMILY_FACT_TEMPLATES, FAMILY_FACT_TEMPLATES_PL, FAMILY_RELATION_EASY
from ..facts.friends import FRIENDSHIP_FACT_TEMPLATES, FRIENDSHIP_FACT_TEMPLATES_PL, FRIENDSHIP_RELATION
from .constants.article_templates import BASIC_ARTICLE_TEMPLATE
from ..utils import decode

def get_articles(
        db: Database, 
        names: list[str], 
        args: ArgumentParser,
    ) -> dict:
    """
    Generate articles for a list of names.
    
    Args:
        db: Database object
        names: list of names (for debugging purposes, 
            we can generate articles for a subset of names)
        seed: random seed (NOTE: even for the same seed, the articles may be different
            because Together is not fully determinstic)
    Returns:
        dict of name -> article generations
        article generation contains multiple types of articles (e.g., basic, llama-8b)
    """
    # get family article
    # HACK: Do not include parent, child, and sibling in the articles
    relation_list = [r for r in FAMILY_RELATION_EASY if r not in ["parent", "child", "sibling"]]
    family_facts = get_relation_facts(
        db, names, relation_list, FAMILY_FACT_TEMPLATES, FAMILY_FACT_TEMPLATES_PL
    )
    # get friendship article
    friend_facts = get_relation_facts(
        db, names, FRIENDSHIP_RELATION, FRIENDSHIP_FACT_TEMPLATES, FRIENDSHIP_FACT_TEMPLATES_PL
    )
    attribute_facts = get_attribute_facts(db, names)

    articles = {}
    for name in names:
        # generate multiple types of articles so that we can compare their quality
        articles[name] = {}

        # generate article using templates
        # NOTE: this also serves as a reference since it contains the facts in simple language
        articles[name]["basic"] = BASIC_ARTICLE_TEMPLATE.format(
            name=name,
            family_facts="\n".join(family_facts[name]),
            friend_facts="\n".join(friend_facts[name]),
            attribute_facts="\n".join(attribute_facts[name]),
        )

        if args.model:
            # generate article using LLMs
            articles[name][args.model] = llm_generate_article(
                model_name=args.model,
                name=name, 
                family_facts=family_facts[name], 
                friend_facts=friend_facts[name],
                attribute_facts=attribute_facts[name],
                seed=args.seed,
            )

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
        results = [decode(result["X"]) for result in db.query(query)]
        relations[relation] = results

    return relations

# Functionality to generate articles using LLM
# 
# NOTE: set the API key using conda env vars (see README.md)
client = Together()

MODELS = {
    'llama3-8b': "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
}

# %%
def llm_generate_article(
        model_name: str,
        name: str, 
        family_facts: list[str],
        friend_facts: list[str],
        attribute_facts: list[str],
        max_tokens: Optional[int] = None, 
        verbose: bool = True,
        seed: int = 1,
    ) -> str:
    # format the facts as a basic article
    facts = [f"- subject name is {name}."] # add name as a fact
    for fact in family_facts + friend_facts + attribute_facts:
        facts.append("- " + fact)
    facts = "\n".join(facts)
    if verbose:
        print(f"generating article for {name} with the following facts:")
        print(facts)
        print("===========================START ARTICLE==========================")
    response = client.chat.completions.create(
        model=MODELS[model_name],
        messages=[
            {"role": "user", "content": LLAMA_ARTICLE_GENERAION_PROMPT7.format(facts)},
        ],
        temperature=0.7,
        top_p=0.7,
        top_k=50,
        repetition_penalty=1,
        stop=["<|eot_id|>"],
        stream=True,
        truncate=max_tokens,
        seed=seed,
    )
    article = ""
    for chunk in response:
        s = chunk.choices[0].delta.content or ""
        if verbose: print(s, end="", flush=True)
        article += s
    if verbose: print("\n===========================END ARTICLE==========================")
    return article
