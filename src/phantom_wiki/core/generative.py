import openai
from together import Together

from .constants.llm_templates import (CFG_prompt_template_Openai,
                                      CFG_prompt_template_Llama,
                                      CFG2QAs_TEMPLATE)


# TODO: add more types of information/make this more flexible?
def generate_cfg_openai(person: str, job: str) -> str:
    prompt = CFG_prompt_template_Openai.format(person, job)
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


def generate_llama(person, job, cfg_str):
    # use LLaMA to generate a CFG
    client = Together()
    if cfg_str is None:
        prompt = CFG_prompt_template_Llama.format(person, job)
    else:
        prompt = CFG2QAs_TEMPLATE.format(cfg_str)
    response =client.chat.completions.create(
        model="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    raw_text = response.choices[0].message.content
    return raw_text
