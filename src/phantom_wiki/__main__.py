# Usage:
# Creating questions:
#   python -m phantom_wiki -op <output path>

# standard imports
import argparse
import os
import json
import janus_swi as janus
# phantom wiki functionality
from .utils import blue

def get_arguments():
    parser = argparse.ArgumentParser(description="Generate articles from Prolog files")
    parser.add_argument(
        "--pl_file", type=str, default="tests/family/family_tree.pl", help="Path to the Prolog file"
    )
    parser.add_argument("--skip_cfg", "-sc", action="store_true", 
                        help="Skip CFG generation")
    parser.add_argument(
        "--cfg_dir",
        "-cd",
        type=str,
        default=None,
        help="Path to the CFG directory if not generating new CFGs",
    )
    parser.add_argument("--output_path", "-op", type=str, default="output", 
                        help="Path to the output folder")
    # TODO this should not depend on the testing directory
    parser.add_argument("--rules", type=list, default=['src/phantom_wiki/family/base_rules.pl', 'src/phantom_wiki/family/derived_rules.pl'], help="list of Path to the rules file")
    (
        args,
        _,
    ) = (
        parser.parse_known_args()
    )  # this is useful when running the script from a notebook so that we use the default values
    return args

def generate_formal_questions(output_path, article_path, base_rule_path, derived_rule_path):
    from .utils.prolog import parse_prolog_predicate_definition
    from .core.formal_questions import get_question_answers

    def get_rules(filename):
        rules = []
        with open(filename, "r") as file:
            for line in file:
                # print(line)
                # if the line is a predicate, print it
                if line.endswith(":-\n"): # TODO: make the prolog parsing more robust
                    # print(parse(line))
                    rules.append(parse_prolog_predicate_definition(line))
        return rules

    # get all predicates in base_rules.pl
    print(f"All predicates in {base_rule_path}")
    # read each line of the file
    base_rules = get_rules(base_rule_path)
    print(base_rules)
    print(f"All predicates in {derived_rule_path}")
    derived_rules = get_rules(derived_rule_path)
    print(derived_rules)

    # store question and answers as a dictionary
    base_question_answers = {}
    derived_question_answers = {}
    # get all files in the output directory
    for filename in os.listdir(article_path):
        # get the article
        with open(os.path.join(article_path, filename), 'r') as f:
            article = f.read()
        # each of these filenames has the form "X_family.txt"
        atom_val = filename.split("_")[0]
        atom_name = 'X'
        print("Getting base questions for X={}".format(atom_val))
        base_question_answers[atom_val] = {
            'evidence': article,
            'qa_pairs' : get_question_answers(atom_val, atom_name, base_rules),
        }

        print("Getting derived questions for X={}".format(atom_val))
        derived_question_answers[atom_val] = {
            'evidence': article,
            'qa_pairs' : get_question_answers(atom_val, atom_name, derived_rules),
        }
    # save the question and answers to a file
    save_dir = os.path.join(output_path, "question_answers")
    os.makedirs(save_dir, exist_ok=True)
    base_path = os.path.join(save_dir, "base.json")
    with open(base_path, "w") as file:
        json.dump(base_question_answers, file, indent=4)
    derived_path = os.path.join(save_dir, "derived.json")
    with open(derived_path, "w") as file:
        json.dump(derived_question_answers, file, indent=4)
    return {
        "base": base_path,
        "derived": derived_path,
    }

def main():
    args = get_arguments()
    print(f"Output path: {args.output_path}")

    blue(f"Prolog file: {args.pl_file}")
    janus.query_once(f"consult(X)", {'X': args.pl_file})
    janus.query_once("consult(X)", {'X': args.rules[0]})
    janus.query_once("consult(X)", {'X': args.rules[1]})
    
    if args.skip_cfg:
        blue("Skipping CFG generation")
    else:
        blue("Generating CFGs")
        # TODO
        blue(f"Saving CFGs to: {args.cfg_dir}")

    blue("Generating articles")
    # TODO: add code to merge family and CFG articles
    # currently, we just pass in the family article
    article_path = os.path.join(args.output_path, "family")

    blue("Generating question answer pairs")
    # TODO
    question_answer_paths = generate_formal_questions(args.output_path, article_path, args.rules[0], args.rules[1])
    print(f"Saved question and answers to {question_answer_paths}")

    # print(f"Rules: {args.rules}")

if __name__ == "__main__":
    main()