# Usage:
# Creating questions:
#   python -m phantom_wiki -op <output path>

# standard imports
import argparse
import json
import os
# phantom wiki functionality
from .facts import (get_database,
                    db_generate_population,
                    db_generate_attributes)
from .core.article import get_articles
from .core.formal_questions import get_question_answers
from .utils.prolog import parse_prolog_predicate_definition
from .utils import blue

def get_arguments():
    parser = argparse.ArgumentParser(description="Generate articles from Prolog files")
    parser.add_argument("--seed", "-s", default=1, type=int,
                        help="Global seed for random number generator")
    parser.add_argument("--output_path", "-op", type=str, default="output", 
                        help="Path to the output folder")
    parser.add_argument("--num_people", "-n", type=int, default=100,
                        help="Number of people in the universe")
    # this is useful when running the script from a notebook so that we use the default values
    args, _ = parser.parse_known_args()
    return args

def generate_relationship_graphs(db):
    pass

def generate_formal_questions(output_path, article_dir, base_rule_path, derived_rule_path):
    def get_rules(filename):
        rules = []
        with open(filename) as file:
            for line in file:
                # print(line)
                # if the line is a predicate, print it
                if line.endswith(":-\n"):  # TODO: make the prolog parsing more robust
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
    for filename in os.listdir(article_dir):
        # get the article
        with open(os.path.join(article_dir, filename)) as f:
            article = f.read()
        # each of these filenames has the form "X_family.txt"
        atom_val = filename.split("_")[0]
        atom_name = "X"
        print(f"Getting base questions for X={atom_val}")
        base_question_answers[atom_val] = {
            "evidence": article,
            "qa_pairs": get_question_answers(atom_val, atom_name, base_rules),
        }

        print(f"Getting derived questions for X={atom_val}")
        derived_question_answers[atom_val] = {
            "evidence": article,
            "qa_pairs": get_question_answers(atom_val, atom_name, derived_rules),
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
    
    # 
    # Step 1. Generate facts
    # 
    db = get_database()
    blue("Generating facts")
    db_generate_population(db, args.num_people, args.seed)
    # TODO: add our implementation of family tree
    db.define("parent/2") # NOTE: define parent relationship since we don't have our own family tree implementation yet
    # TODO: add our implementation of friendship graph
    # TODO: add our implementation of attributes
    db_generate_attributes(db, args.seed)

    # 
    # Step 2. Generate articles 
    # Currently, the articles are comprised of a list of facts.
    # 
    blue("Generating articles")
    # TODO: add code to merge family and CFG articles
    # currently, we just pass in the family article
    article_dir = os.path.join(args.output_path, "articles")
    print(f"Saving articles to: {article_dir}")
    os.makedirs(article_dir, exist_ok=True)
    articles = get_articles(db, db.get_names())
    for name, article in articles.items():
        with open(os.path.join(article_dir, f"{name}_article.txt"), "w") as file:
            file.write(article)

    # 
    # Step 3. Generate question-answer pairs
    # 
    blue("Generating question answer pairs")
    # TODO: deprecate generate_formal_questions
    # TODO: call function to generate question-answers from CFGs

if __name__ == "__main__":
    main()
