import re
import tqdm
import argparse
from collections import defaultdict

import pandas as pd
from datasets import load_dataset, Dataset
from pyswip import Prolog
from pyswip.easy import Variable

from ..facts.friends.constants import FRIENDSHIP_FACT_TEMPLATES, FRIENDSHIP_FACT_TEMPLATES_PL
from ..facts.attributes.constants import ATTRIBUTE_FACT_TEMPLATES
from ..facts.family.constants import FAMILY_FACT_TEMPLATES, FAMILY_FACT_TEMPLATES_PL


# Constants
BASIC_TEMPLATE_OF = "The {A} of {B} is"
BASIC_TEMPLATE_S = "{B}'s {A} is"
BASIC_TEMPLATE_OF_PL = "The {A} of {B} are"
BASIC_TEMPLATE_S_PL = "{B}'s {A} are"
BASIC_TEMPLATES_DISTINCT = "The number of {A} {B} has is"

# CoT formatting tags
THINK_S = '<think>'
THINK_E = '</think>'
ANSWER_S = '<answer>'
ANSWER_E = '</answer>'

# Combine templates
TEMPLATES = FRIENDSHIP_FACT_TEMPLATES | FAMILY_FACT_TEMPLATES
TEMPLATES_PL = FRIENDSHIP_FACT_TEMPLATES_PL | FAMILY_FACT_TEMPLATES_PL


def extract_elements(s: str):
    """Extract elements from a Prolog predicate string."""
    # For aggregate_all functions
    pattern = r'distinct\((\w+)\(([^,]+),\s*[^)]+\)\),\s*(Count_\d+)'
    match = re.search(pattern, s)
    if match:
        predicate, elem_a, elem_b = match.groups()
        predicate = 'distinct_' + predicate
        return [predicate, elem_a.strip('"'), elem_b.strip('"')]
    
    # For regular predicates
    start_idx = s.find("(")
    end_idx = s.rfind(")")
    if start_idx == -1 or end_idx == -1:
        return [s.strip()]
    
    predicate = s[:start_idx]
    inside = s[start_idx + 1:end_idx]
    parts = [predicate] + inside.split(",", 1)
    parts = [p.strip().replace('"', '') for p in parts]
    return parts


def decode(x):
    """Decode bytes to string if necessary."""
    if isinstance(x, bytes):
        return x.decode("utf-8")
    return x


def generate_cot_for_dataset(dataset_name: str, split_name: str):
    """Generate Chain of Thought (CoT) for a given dataset split."""
    
    def prolog_query_all(pl_file: str, goal: str):
        """Execute a Prolog query and return all solutions."""
        return list(prolog_db.query(goal))
    
    # Load dataset
    database = load_dataset(dataset_name, 'database')
    question_answer = load_dataset(dataset_name, 'question-answer')
    question_answer_df = question_answer[split_name].to_pandas()
    
    # Load Prolog DB
    filename = f"{split_name}.pl"
    with open(filename, "w", encoding="utf-8") as file:
        file.write(database[split_name]['content'][0])
    print(f"File '{filename}' has been created.")
    
    prolog_db = Prolog()
    prolog_db.consult(filename)
    
    fin_cot_list = []
    
    # Process each question-answer pair
    for prolog_idx, qd_data in tqdm.tqdm(question_answer_df.iterrows()):
        prolog_data = qd_data['prolog']
        answers = qd_data['answer']
        query = prolog_data['query']
        query_answer = prolog_data['answer']
        
        # Reversing the order
        # https://github.com/kilian-group/phantom-wiki/blob/main/src/phantom_wiki/utils/get_answer.py#L117
        reversed_query = query[::-1]
        prolog_query = ','.join(reversed_query) + '.'
        solutions = prolog_query_all(filename, prolog_query)
        
        # Deduplicate solutions
        solutions = [eval(s) for s in list(set([str({k: v for k, v in s.items() if not isinstance(v, Variable)}) for s in solutions]))]
        solutions = [{k: str(decode(v)) for k, v in s.items()} for s in solutions]
        
        # Make CoT, by accumulating the intermediate CoT with dictionary
        cum_cot_list = []
        for s in reversed_query:
            cum_cot_dict = defaultdict(set)
            _elements = extract_elements(s)
            assert len(_elements) == 3, f"Expected 3 elements, got {len(_elements)}: {_elements}"
            
            for solution in solutions:
                elements = _elements[::]  # Deep copy
                elements[1] = solution.get(elements[1], elements[1])
                elements[2] = solution.get(elements[2], elements[2])
                
                # Make dictionary of intermediate CoT with the key as the predicate and the value as the accumulated answer
                cot_key = (elements[0], elements[1])
                cot_value = elements[2]
                # if elements[0] in TEMPLATES:
                #     cot_key = TEMPLATES[elements[0]].replace('<subject>', elements[1])
                # elif 'distinct' in elements[0]:
                #     cot_key = BASIC_TEMPLATES_DISTINCT.format(
                #         A=elements[0].replace('distinct_', '').replace('_', '-'), 
                #         B=elements[1]
                #     )
                #     cot_value = elements[2]
                # elif elements[0] in ATTRIBUTE_FACT_TEMPLATES.keys():
                #     basic_template = BASIC_TEMPLATE_S
                #     cot_key = basic_template.format(
                #         A=elements[0].replace('_', '-'), 
                #         B=elements[1]
                #     )
                #     cot_value = elements[2]
                # else:
                #     basic_template = BASIC_TEMPLATE_OF
                #     cot_key = basic_template.format(
                #         A=elements[0].replace('_', '-'), 
                #         B=elements[1]
                #     )
                #     cot_value = elements[2]
                
                cum_cot_dict[cot_key].add(cot_value)
            cum_cot_list.append(cum_cot_dict)
        
        # Make answer part of the CoT
        cum_cot_dict = defaultdict(set)
        for solution in solutions:
            answer = solution[query_answer]
            assert answer in answers, f"Answer {answer} not found in expected answers {answers}"
            cum_cot_dict[("The answer is", "")].add(answer)
        
        assert sorted(cum_cot_dict[("The answer is", "")]) == sorted(set(answers))
        cum_cot_list.append(cum_cot_dict)
        
        # Merge the accumulated CoT into a single CoT with proper formatting
        fin_cot = f'{THINK_S}'
        for cot_idx, cum_cot_dict in enumerate(cum_cot_list):
            _cum_cot = ''
            for key in sorted(cum_cot_dict.keys()):
                predicate, subject = key  # e.g. "The friend of xxx is"
                tail = ', '.join(sorted(cum_cot_dict[key]))  # e.g. "xxx, yyy"
                
                if 'distinct' in predicate:
                    templates = BASIC_TEMPLATES_DISTINCT
                    predicate = predicate.replace('distinct_', '').replace('_', '-')
                # Directly answer the question
                elif 'answer' in predicate:
                    head = '' 
                # Handle pluralization for multiple answers
                elif len(cum_cot_dict[key]) > 1:
                    templates = TEMPLATES_PL
                    if predicate in templates:
                        head = templates[predicate].replace('<subject>', subject)
                    elif predicate in ATTRIBUTE_FACT_TEMPLATES.keys():
                        templates = BASIC_TEMPLATE_S_PL
                        head = templates.format(
                            A=predicate.replace('_', '-'), 
                            B=subject
                        )
                    else:
                        templates = BASIC_TEMPLATE_OF_PL
                        head = templates.format(
                            A=predicate.replace('_', '-'), 
                            B=subject
                        )
                else:
                    templates = TEMPLATES
                    if predicate in templates:
                        head = templates[predicate].replace('<subject>', subject)
                    elif predicate in ATTRIBUTE_FACT_TEMPLATES.keys():
                        templates = BASIC_TEMPLATE_S
                        head = templates.format(
                            A=predicate.replace('_', '-'), 
                            B=subject
                        )
                    else:
                        templates = BASIC_TEMPLATE_OF
                        head = templates.format(
                            A=predicate.replace('_', '-'), 
                            B=subject
                        )
                
                _cot = f'{head} {tail}. '
                # Capitalize the first letter of each cot
                _cot = _cot[0].capitalize() + _cot[1:]
                _cum_cot += _cot
            
            # Add think and answer tags at appropriate positions
            if cot_idx == len(cum_cot_list) - 2:
                # Second to last element - close think tag
                _cum_cot = f'{_cum_cot.strip()}{THINK_E}'
            elif cot_idx == len(cum_cot_list) - 1:
                # Last element - wrap in answer tags
                _cum_cot = f'{ANSWER_S}{_cum_cot.strip()}{ANSWER_E}'
            
            fin_cot += _cum_cot
        
        fin_cot = fin_cot.strip()
        fin_cot_list.append(fin_cot)
    
    # Add CoT column to dataframe and save
    question_answer_df['cot'] = fin_cot_list
    
    # Print sample CoT for verification
    if fin_cot_list:
        print(f"Sample CoT: {fin_cot_list[0]}")
    
    # question_answer_df.to_csv(f"{split_name}.csv", index=False)
    # Save to disk
    question_answer = Dataset.from_pandas(question_answer_df)
    question_answer.save_to_disk(f"{split_name}")
    print(f"Generated CoT for {len(fin_cot_list)} questions and saved to {split_name}")
    
    return question_answer_df


def main():
    """Main function to run the CoT generation."""
    parser = argparse.ArgumentParser(description='Generate Chain of Thought (CoT) for Phantom Wiki dataset')
    parser.add_argument('--split', type=str, default='depth_20_size_50_seed_1',
                       help='Dataset split to process (default: depth_20_size_50_seed_1)')
    parser.add_argument('--dataset', type=str, default='kilian-group/phantom-wiki-v1',
                       help='Dataset name on Hugging Face Hub (default: kilian-group/phantom-wiki-v1)')
    
    args = parser.parse_args()
    
    print(f"Starting CoT generation for split: {args.split}")
    print(f"Using dataset: {args.dataset}")
    
    try:
        result_df = generate_cot_for_dataset(args.dataset, args.split)
        print(f"Successfully completed CoT generation for {len(result_df)} questions")
    except Exception as e:
        print(f"Error during CoT generation: {e}")
        raise


if __name__ == "__main__":
    main()