import os
import argparse
from faker import Faker

from CFG_utils import * 

def get_arguments():
    parser = argparse.ArgumentParser(description="Generate articles from Prolog files")
    parser.add_argument("--pl_file", type=str, default='../../tests/family_tree.pl', help="Path to the Prolog file")
    parser.add_argument("--output_folder", type=str, default= 'output', help="Path to the output folder")
    parser.add_argument("--rules", type=str, default='../phantom_wiki/family/rules.pl', help="Path to the rules file")
    return parser.parse_args()

# 
# Begin Albert's code
# 
import re
import janus_swi as janus
from grouped_relations import ppl_2_ppl
# , ppl_2_socialconstructs, ppl_2_objs, things

def consult(predicate_path, rule_path):
    janus.query_once(f"consult(X)", {'X': predicate_path})
    janus.query_once("consult(X)", {'X': rule_path})

def parse(line):
    """
    parses a Prolog predicate
    Examples:
        female(vanessa). -> ('female', ['vanessa', 'albert'])
        parent(anastasia, sarah). -> ('parent', ['anastasia', 'sarah'])
        
    Args:
        line (str): predicate(arg1, arg2, ..., argn).
    Returns:
        (predicate, [arg1, arg2, ..., argn])
    """
    pattern = r"^([a-z]+)\((.*)\)\.$"
    match = re.search(pattern, line)
    return match.group(1), match.group(2).split(", ")

def get_family_article(name):
    """
    Get the following relations for a given name:
    - mother
    - father
    - siblings
    - children
    - wife/husband 

    Assumes that the prolog files are loaded and the predicates are defined in the prolog files.
    This can be done using the following code:
    ```
    janus.query_once("consult('../../tests/family_tree.pl')")
    janus.query_once("consult('./family/rules.pl')")
    ```

    Ref: https://www.swi-prolog.org/pldoc/man?section=janus-call-prolog
    """
    # name = 'elias'
    relations = {}
    # get mother
    if mother := janus.query_once("mother(X, Y)", {'Y': name})['X']:
        relations['mother'] = mother
    # print(mother)
    # get father
    if father := janus.query_once("father(X, Y)", {'Y': name})['X']:
        relations['father'] = father
    # print(father)
    # get siblings
    if siblings := [sibling['X'] for sibling in janus.query("sibling(X, Y)", {'Y': name})]:
        relations['sibling'] = ', '.join(siblings)
    # print(list(siblings))
    # get children
    if children := [child['X'] for child in list(janus.query("child(X, Y)", {'Y': name}))]:
        relations['child'] = ', '.join(children)
        relations['number of children'] = len(children)
    # print(list(children))
    
    # TODO: get wife and husband
    if spouse := (janus.query_once(f"husband(X, Y)", {'X': name}) or janus.query_once(f"wife(X, Y)", {'X': name}))['Y']:
        relations['spouse'] = spouse

    facts = []
    for relation, target in relations.items():
        relation_template = ppl_2_ppl[relation]
        fact = relation_template.replace("<subject>", name) + " " + str(target) + "."
        facts.append(fact)

    article = "\n".join(facts)
    return article

# 
# End Albert's code
# 

if __name__ == "__main__":
    # get arguments
    args = get_arguments()
    # set seed
    Faker.seed(0)
    fake = Faker()
    #make directories
    bio_folder = os.path.join(args.output_folder, 'bio')
    CFG_folder = os.path.join(args.output_folder, 'CFG')
    # TODO want to put prologs and DLVs also in the same folder
    os.makedirs(CFG_folder, exist_ok=True)
    os.makedirs(bio_folder, exist_ok=True)
    # load the prolog file
    print(f"loading predicates from {args.pl_file}")
    print(f"loading rules from {args.rules}")
    consult(args.pl_file, args.rules)

    with open(args.pl_file, "r") as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("female") or line.startswith("male"):
                person = match_name(line)
            else:
                print('skip line')
                continue

            # get the family article
            family = get_family_article(person)
            print("family article:")
            print(family)

            # get the job article
            job = fake.job()
            print(f"{person} is a {job}")
            # import pdb; pdb.set_trace()
            # allow multiple tries and only write to file if a bio is successfully generated
            bio, cfg = generate_article_with_retries(person, job, max_attempts=10)

            # write the CFG to a file
            CFG_file = os.path.join(CFG_folder, f"{person}_CFG.txt")
            with open(CFG_file, "w") as file:
                file.write(cfg)

            # write to file
            bio_file = os.path.join(bio_folder, f"{person}_bio.txt")
            write_bio(bio, bio_file)
            print(f"writen bio for {person} to {person}_bio.txt")