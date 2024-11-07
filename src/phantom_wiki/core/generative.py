import openai

from phantom_wiki.core.constants.llm_templates import CFG_PROMPT_TEMPLATE, CFG2QAs_TEMPLATE


# TODO: add more types of information/make this more flexible?
def generate_cfg_openai(person: str, job: str) -> str:
    prompt = CFG_PROMPT_TEMPLATE.format(person, job)
    response = openai.chat.completions.create(
        model="gpt-4o", messages=[{"role": "system", "content": prompt}]
    )
    raw_text = response.choices[0].message.content
    return raw_text


def geneate_qa_openai(grammar: str) -> str:
    prompt = CFG2QAs_TEMPLATE.format(grammar)
    response = openai.chat.completions.create(
        model="gpt-4o", messages=[{"role": "system", "content": prompt}]
    )
    raw_text = response.choices[0].message.content
    return raw_text
