import pandas as pd
from datasets import load_dataset
from pyswip import Prolog
import tqdm
import re

def prolog_query_all(pl_file: str, goal: str):
    return list(PROLOG.query(goal))

def extract_elements(s: str):
    start_idx = s.find("(")
    end_idx = s.rfind(")")
    predicate,inside = s[:start_idx], s[start_idx+1 : end_idx]
    parts = [predicate] + inside.split(",", 1)
    parts = [p.strip().replace('"', '') for p in parts]
    return parts

def extract_elements(s: str):
    # For aggregate_all functions
    # pattern = r'distinct\((\w+)\("([^"]+)",\s*\w+\)\),\s*(Count_\d+)'
    pattern = r'distinct\((\w+)\(([^,]+),\s*[^)]+\)\),\s*(Count_\d+)'
    match = re.search(pattern, s)
    if match:
        predicate, elem_a,elem_b = match.groups()
        predicate = 'distinct_' + predicate
        return [predicate,elem_a.strip('"'),elem_b.strip('"')]
    start_idx = s.find("(")
    end_idx = s.rfind(")")
    predicate,inside = s[:start_idx], s[start_idx+1 : end_idx]
    parts = [predicate] + inside.split(",", 1)
    parts = [p.strip().replace('"', '') for p in parts]
    return parts

# https://github.com/kilian-group/phantom-wiki/blob/main/src/phantom_wiki/facts/family/constants.py
# https://github.com/kilian-group/phantom-wiki/blob/main/src/phantom_wiki/facts/attributes/constants.py#L8
SPLIT = 'depth_20_size_50_seed_1'
BASIC_TEMPLATE_OF = "{A} of {B} is {C}."
BASIC_TEMPLATE_S = "{B}'s {A} is {C}."
BASIC_TEMPLATES_DISTINCT = "The number of {A} {B} has is {C}."


# Load dataset
# database = load_dataset("kilian-group/phantom-wiki-v1",'database')
# text_corpus = load_dataset("kilian-group/phantom-wiki-v1",'text-corpus')
question_answer = load_dataset("kilian-group/phantom-wiki-v1",'question-answer')
question_answer_df = question_answer[SPLIT].to_pandas()

# Load solutions
fname = "/Users/godongyoung/Dropbox/2025-Fall/PostDoc(25-27)/Paper_Work/Phantom_reasoning/implementation/prolog/depth_20_size_50_seed_1.pl"
PROLOG = Prolog()
PROLOG.consult(fname)

FRIENDSHIP_FACT_TEMPLATES = {
    "friend": "The friend of <subject> is",
}

FAMILY_FACT_TEMPLATES = {
    "brother": "The brother of <subject> is",
    "sister": "The sister of <subject> is",
    "sibling": "<subject>'s sibling is",
    "parent": "The parent of <subject> is",
    "father": "The father of <subject> is",
    "mother": "The mother of <subject> is",
    "spouse": "<subject>'s spouse is",
    "child": "The child of <subject> is",
    "son": "The son of <subject> is",
    "daughter": "The daughter of <subject> is",
    "wife": "The wife of <subject> is",
    "husband": "The husband of <subject> is",
    "stepfather": "The stepfather of <subject> is",
    "stepmother": "The stepmother of <subject> is",
    "number of children": "The number of children <subject> has is",
    "uncle": "The uncle of <subject> is",
    "aunt": "The aunt of <subject> is",
    "father_in_law": "The father-in-law of <subject> is",
    "mother_in_law": "The mother-in-law of <subject> is",
    "brother_in_law": "The brother-in-law of <subject> is",
    "sister_in_law": "The sister-in-law of <subject> is",
    "son_in_law": "The son-in-law of <subject> is",
    "daughter_in_law": "The daughter-in-law of <subject> is",
}

ATTRIBUTE_FACT_TEMPLATES = {
    "dob": "The date of birth of <subject> is",
    "job": "The occupation of <subject> is",
    "hobby": "The hobby of <subject> is",
    "gender": "The gender of <subject> is",
}


TEMPLATES = FRIENDSHIP_FACT_TEMPLATES | FAMILY_FACT_TEMPLATES #| ATTRIBUTE_FACT_TEMPLATES

from pyswip.easy import Variable

def decode(x):
    if isinstance(x, bytes):
        return x.decode("utf-8")
    return x

fin_cot_list = []
agg_list = []
# for prolog_idx,prolog in enumerate(tqdm.tqdm(question_answer_df['prolog'].values)):
for prolog_idx,qd_data in tqdm.tqdm(question_answer_df.iterrows()):
    prolog = qd_data['prolog']
    answers = qd_data['answer']
    QUERY = prolog['query']
    QUERY_ANSWER = prolog['answer']
    # Reversing the order
    # https://github.com/kilian-group/phantom-wiki/blob/main/src/phantom_wiki/utils/get_answer.py#L117
    reversed_query = QUERY[::-1]
    prolog_query = ','.join(reversed_query)+'.'
    solutions = prolog_query_all(fname,prolog_query)

    # Deduplicate solutions
    solutions = [eval(s) for s in list(set([str({k:v for k,v in s.items() if not isinstance(v,Variable)}) for s in solutions]))]
    solutions = [{k:decode(v)  for k,v in s.items()}for s in solutions]

    if any(['aggregate_all' in query for query in reversed_query]):
        agg_list.append(prolog_idx)
    # Make CoT
    intermediate_cot_list = []
    for s in reversed_query:
        elements = extract_elements(s)
        assert len(elements) == 3

        if elements[0] in TEMPLATES:
            cot = TEMPLATES[elements[0]].replace('<subject>',elements[1]) + ' ' + elements[2] + '.'
        elif 'distinct' in elements[0]:
            cot = BASIC_TEMPLATES_DISTINCT.format(A=elements[0].replace('distinct_','').replace('_','-'), B=elements[1], C=elements[2])
        elif elements[0] in ATTRIBUTE_FACT_TEMPLATES.keys():
            BASIC_TEMPLATE = BASIC_TEMPLATE_S
            cot = BASIC_TEMPLATE.format(A=elements[0].replace('_','-'), B=elements[1], C=elements[2])
        else:
            BASIC_TEMPLATE = BASIC_TEMPLATE_OF
            cot = BASIC_TEMPLATE.format(A=elements[0].replace('_','-'), B=elements[1], C=elements[2])

        intermediate_cot_list.append(cot)
    # Optional: Capitalize the first letter of each cot
    for idx,cot in enumerate(intermediate_cot_list):
        cot = cot[0].capitalize() + cot[1:]
        intermediate_cot_list[idx] = cot
    _cot = ' '.join(intermediate_cot_list)

    # Fill in the answer with solutions (You can also use all solutions)
    cot_list = []
    # solution = solutions[0]
    for solution in solutions:
        cot = _cot[:] # Deep copy
        solution = {k:str(v) for k,v in solution.items()}
        for k,v in solution.items():
            cot = cot.replace(k,str(v))
        
        answer = solution[QUERY_ANSWER]
        assert answer in answers
        cot += f" The answer is {answer}."
        cot_list.append(cot)
    # fin_cot_list.append(cot)
    fin_cot_list.append(cot_list)

question_answer_df['cot'] = fin_cot_list