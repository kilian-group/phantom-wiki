# Usage:
# Creating questions:
#   python -m phantom_wiki -od <output path>

# standard imports
import json
import os
import numpy as np
import time
import logging
import subprocess
import sys
from datetime import datetime

# phantom wiki functionality
from .facts import (get_database,
                    db_generate_family, 
                    db_generate_friendships,
                    db_generate_attributes)
from .core.article import get_articles
from .facts.templates import generate_templates
from .facts.sample import sample
from .utils import blue, get_parser, generate_unique_id
from .facts.family import fam_gen_parser
from .facts import question_parser

def check_git_status():
    try:
        # Check for uncommitted changes
        result = subprocess.run(['git', 'status', '--porcelain'], stdout=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print("Error: Unable to check Git status.")
            sys.exit(1)
        
        # If `git status --porcelain` output is not empty, there are uncommitted changes
        if result.stdout.strip():
            print("Error: You have uncommitted or unstashed changes. Please commit or stash them before running this script.")
            sys.exit(1)
    except FileNotFoundError:
        print("Error: Git is not installed or not available in PATH.")
        sys.exit(1)


def save_command_and_git_info(output_dir):
    """Save the executed command and Git commit hash to a file."""

    def get_commit_hash():
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE, text=True)
        return result.stdout.strip()
    
    git_commit_hash = get_commit_hash()
    executed_command = " ".join(sys.argv)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    info_content = (
        f"Command: {executed_command}\n"
        f"Timestamp: {timestamp}\n"
        f"Git Commit Hash: {git_commit_hash}\n"
    )

    os.makedirs(output_dir, exist_ok=True)
    info_file_path = os.path.join(output_dir, "run_info.txt")
    
    with open(info_file_path, "w") as info_file:
        info_file.write(info_content)

    print(f"Run information saved to: {info_file_path}")

def main(args):

    # Check Git status before running the main logic
    check_git_status()
    print("Git status is clean. Running the script...")

    # Set up logging
    logging.getLogger('faker').setLevel(logging.INFO)

    if args.quiet:
        log_level = logging.WARNING
    elif args.debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(
        level=log_level,
        format='%(message)s',
        handlers=[logging.StreamHandler()]
    )

    start_time=time.time()
    # save the executed command and Git commit hash to a file 
    save_command_and_git_info(args.output_dir)

    logging.info(f"Output dir: {args.output_dir}")
    # 
    # Step 1. Generate facts
    #
    db = get_database()
    db.define("nonbinary/1")

    blue("Generating facts")
    # generate family tree
    db_generate_family(db, args)
    # generate friend relationships between people in the database
    db_generate_friendships(db, args)
    # generate jobs, hobbies for each person in the database
    db_generate_attributes(db, args)

    facts_time = time.time()

    # save the database to a file
    db.save_to_disk(os.path.join(args.output_dir, "facts.pl"))

    article_time = time.time()
    #
    # Step 2. Generate articles
    # Currently, the articles are comprised of a list of facts.
    #
    blue("Generating articles")
    # TODO: add code to merge family and CFG articles
    # currently, we just pass in the family article
    articles = get_articles(db, db.get_names())
    if args.article_format == "txt":
        article_dir = os.path.join(args.output_dir, "articles")
        logging.info(f"Saving articles to: {article_dir}")
        os.makedirs(article_dir, exist_ok=True)
        for name, article in articles.items():
            with open(os.path.join(article_dir, f"{name}.txt"), "w") as file:
                file.write(article)
    elif args.article_format == "json":
        save_path = os.path.join(args.output_dir, "articles.json")
        logging.info(f"Saving articles to: {save_path}")
        with open(save_path, "w") as file:
            json.dump([{"title" : name, "article" : article} for name, article in articles.items()], file, indent=4)
    else:
        raise ValueError(f"Article format {args.article_format} not supported!")

    question_time = time.time()
    #
    # Step 3. Generate question-answer pairs
    #
    blue("Generating question answer pairs")
    # generate question templates with a given depth
    templates = generate_templates(depth=args.depth)
    # sample questions for each template (i.e., type)
    if args.question_format == "json_by_type":
        question_dir = os.path.join(args.output_dir, "questions")
        logging.info(f"Saving questions to: {question_dir}")
        os.makedirs(question_dir, exist_ok=True)

    all_questions = []
    for i, (question_template, query_template, answer) in enumerate(templates):
        # Reset the seed at the start of each question type
        # so that sampled questions are the same for each question type
        rng = np.random.default_rng(args.seed)
        questions = []
        for _ in range(args.num_questions_per_type):
            _, question, query = sample(
                db, 
                question_template, 
                query_template, 
                rng=rng,
                valid_only=args.valid_only
            )
            # get distinct answers
            # TODO: is there a better way to do this?
            # NOTE: we concatenate the clauses in the prolog query in reverse order
            # since prolog executes goals from left to right
            all_results=[]
            reversed_query = query[::-1]
            import pdb; pdb.set_trace()
            # to get intermediate answers, we get the answer for each subset of the query, each time incremented by one subquery
            for i in range(len(reversed_query)):
                partial_results = db.query(", ".join(reversed_query[:i+1]))
                # partial_results = [x.values().tolist() for x in partial_results]
                all_results.extend(partial_results)
            final_results = [str(x[answer]) for x in db.query(", ".join(reversed_query))]
            final_results = list(set(final_results))
            # make unique and sort in alphabetical order
            questions.append({
                "id": generate_unique_id(),
                "question": question,
                "intermediate_answers": all_results,
                "answer": final_results,
                "prolog": {"query": query, "answer": answer},
                "template": question_template,
                "type": i, # this references the template type
            })
            
            if args.question_format == "json_by_type":
                with open(os.path.join(question_dir, f"type{i}.json"), "w") as file:
                    json.dump(questions, file, indent=4)
        all_questions.extend(questions)

    if args.question_format == "json":
        # save all questions to a single file
        save_path = os.path.join(args.output_dir, "questions.json")
        logging.info(f"Saving questions to: {save_path}")
        with open(save_path, "w") as file:
            json.dump(all_questions, file, indent=4)

    logging.info("Benchmarking Results:")
    logging.info(f"Generating all facts: {facts_time-start_time:.4f}s")
    logging.info(f"Saving all facts in dataframe: {article_time-facts_time:.4f}s")
    logging.info(f"Generating and writing all articles: {question_time-article_time:.4f}s")
    logging.info(f"Generating and writing Q/As: {time.time()-question_time:.4f}s")
    logging.info(f"Total time: {time.time()-start_time:.4f}s")

if __name__ == "__main__":
    # we combine a base parser with the family generator parser
    # TODO: add parser for other generation components
    # - friend
    # - attribute
    parser = get_parser(parents=[
        fam_gen_parser,
        question_parser,
    ])
    args = parser.parse_args()
    main(args)
