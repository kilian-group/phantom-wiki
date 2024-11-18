# Usage:
# Creating questions:
#   python -m phantom_wiki -op <output path>

# standard imports
import argparse
import json
import os
import numpy as np

# phantom wiki functionality
from .core.article import get_articles
from .facts import db_generate_attributes, db_generate_population, get_database
from .facts.templates import generate_templates
from .facts.sample import sample
from .utils import blue

def get_arguments():
    parser = argparse.ArgumentParser(description="Generate articles from Prolog files")
    parser.add_argument("--seed", "-s", default=1, type=int, help="Global seed for random number generator")
    parser.add_argument("--output_path", "-op", type=str, default="output", help="Path to the output folder")
    parser.add_argument("--num_people", "-n", type=int, default=100, help="Number of people in the universe")
    # this is useful when running the script from a notebook so that we use the default values
    args, _ = parser.parse_known_args()
    return args

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
    db.define(
        "parent/2"
    )  # NOTE: define parent relationship since we don't have our own family tree implementation yet
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
    # TODO: add CLI argument for the depth
    # TODO: add CLI argument for the number of questions per type
    # TODO: add valid only flag
    templates = generate_templates(depth=6)
    # sample questions for each template (i.e., type)
    question_dir = os.path.join(args.output_path, "questions")
    print(f"Saving questions to: {question_dir}")
    os.makedirs(question_dir, exist_ok=True)
    questions = []
    rng = np.random.default_rng(args.seed)
    for i, (question_template, query_template, answer) in enumerate(templates):
        _, question, query = sample(
            db, 
            question_template, 
            query_template, 
            rng=rng,
            valid_only=False
        )
        questions.append({
            "template": question_template,
            "question": question,
            "query": query,
            # TODO: get ground-truth answer by running the query
            "answer": answer,
        })
        with open(os.path.join(question_dir, f"type{i}_question.json"), "w") as file:
            json.dump(questions, file, indent=4)

if __name__ == "__main__":
    main()
