# Usage:
# Creating questions:
#   python -m phantom_wiki -od <output path>

# standard imports
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime

import numpy as np
import pandas as pd
from tqdm import tqdm

from .core.article import get_articles

# phantom wiki functionality
from .facts import (
    db_generate_attributes,
    db_generate_family,
    db_generate_friendships,
    get_database,
    question_parser,
)
from .facts.family import fam_gen_parser
from .facts.friends import friend_gen_parser
from .facts.question_difficulty import calculate_query_difficulty
from .facts.sample import sample_valid_only
from .facts.templates import generate_templates
from .utils import blue, generate_unique_id, get_parser
from .utils.get_answer import get_answer


def check_git_status():
    try:
        # Check for uncommitted changes
        result = subprocess.run(["git", "status", "--porcelain"], stdout=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print("Error: Unable to check Git status.")
            sys.exit(1)

        # If `git status --porcelain` output is not empty, there are uncommitted changes
        if result.stdout.strip():
            print(
                "Error: You have uncommitted or unstashed changes. Please commit or stash them before running this script."
            )
            sys.exit(1)
    except FileNotFoundError:
        print("Error: Git is not installed or not available in PATH.")
        sys.exit(1)


def save_command_and_git_info(output_dir):
    """Save the executed command and Git commit hash to a file."""

    def get_commit_hash():
        result = subprocess.run(["git", "rev-parse", "HEAD"], stdout=subprocess.PIPE, text=True)
        return result.stdout.strip()

    git_commit_hash = get_commit_hash()
    executed_command = " ".join(sys.argv)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    info_content = (
        f"Command: {executed_command}\n" f"Timestamp: {timestamp}\n" f"Git Commit Hash: {git_commit_hash}\n"
    )

    os.makedirs(output_dir, exist_ok=True)
    info_file_path = os.path.join(output_dir, "run_info.txt")

    with open(info_file_path, "w") as info_file:
        info_file.write(info_content)

    print(f"Run information saved to: {info_file_path}")


def main(args):
    # Check Git status before running the main logic
    if not args.debug:
        check_git_status()
        print("Git status is clean. Running the script...")
    else:
        print("Debug mode enabled. Skipping Git status check.")

    if args.quiet:
        log_level = logging.WARNING
    elif args.debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(level=log_level, format="%(message)s", handlers=[logging.StreamHandler()])

    # save the executed command and Git commit hash to a file
    save_command_and_git_info(args.output_dir)

    logging.info(f"Output dir: {args.output_dir}")

    # create dictionary to store timings
    timings = {}
    global_start = time.time()

    #
    # Step 1. Generate facts
    #
    db = get_database()
    db.define("nonbinary/1")

    blue("Generating facts")
    start = time.time()
    # generate family tree
    db_generate_family(db, args)
    # generate friend relationships between people in the database
    db_generate_friendships(db, args)
    # generate jobs, hobbies for each person in the database
    db_generate_attributes(db, args)
    timings["facts_generate"] = time.time() - start

    db_path = os.path.join(args.output_dir, "facts.pl")
    blue(f"Saving Prolog database to {db_path}")
    facts_time = time.time()
    db.save_to_disk(db_path)
    timings["facts_save"] = time.time() - facts_time

    #
    # Step 2. Generate articles
    # Currently, the articles are comprised of a list of facts.
    #
    blue("Generating articles")
    start = time.time()
    articles = get_articles(db, db.get_person_names())
    timings["articles_generate"] = time.time() - start

    blue("Saving articles")
    start = time.time()
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
            json.dump(
                [{"title": name, "article": article} for name, article in articles.items()], file, indent=4
            )
    else:
        raise ValueError(f"Article format {args.article_format} not supported!")
    timings["articles_save"] = time.time() - start

    #
    # Step 3. Generate question-answer pairs
    #
    blue("Generating question answer pairs")
    start = time.time()
    # generate question templates with a given depth
    templates = generate_templates(depth=args.depth)
    # sample questions for each template (i.e., type)
    if args.question_format == "json_by_type":
        question_dir = os.path.join(args.output_dir, "questions")
        logging.info(f"Saving questions to: {question_dir}")
        os.makedirs(question_dir, exist_ok=True)

    progbar = tqdm(enumerate(templates), desc="Generating questions", total=len(templates))

    # Populate person name bank for the universe. The list is static across generating questions
    # so create it once and pass it to the question generation function
    person_name_bank: list[str] = db.get_person_names()

    # Create caches for person -> (attr name, attr value) and person -> (relation, related person) pairs
    # When we iterate over multiple questions, we can reuse the same cache to avoid recomputing
    # e.g. "John" -> [("dob", "1990-01-01"), ("job", "teacher"), ("hobby", "reading"), ("hobby", "swimming"), ...]
    # NOTE: Invariant: (attr name, attr value) pairs are unique
    person_name2attr_name_and_val: dict[str, list[tuple[str, str]]] = {}
    # e.g. "John" -> [("child", "Alice"), ("child", "Bob"), ("friend", "Charlie"), ...]
    # NOTE: Invariant: (relation, related person) pairs are unique
    person_name2relation_and_related: dict[str, list[tuple[str, str]]] = {}

    # To store all the questions and queries for all templates
    all_questions = []
    all_queries = []

    for i, (question_template, query_template, answer) in progbar:
        # Reset the seed at the start of each question type
        # so that sampled questions are the same for each question type
        rng = np.random.default_rng(args.seed)

        # To store the questions and queries for the given template
        questions = []
        queries = []

        # for _ in range(args.num_questions_per_type):
        while len(questions) < args.num_questions_per_type: # TODO: this is a temporary fix to make sure that we generate the same number of questions for each template

            # sample a question
            if args.valid_only:
                question, query = sample_valid_only(
                    question_template,
                    query_template,
                    rng,
                    db,
                    person_name_bank,
                    person_name2attr_name_and_val,
                    person_name2relation_and_related,
                    hard_mode=args.hard_mode,
                    num_sampling_attempts=args.num_sampling_attempts,
                )
            else:
                raise NotImplementedError("Sampling questions without valid_only is not supported.")

            questions.append(question)
            queries.append(query)

        all_questions.append(questions)
        all_queries.append(queries)


    # Get all possible answers/solution traces for the queries
    answers = [t[2] for t in templates]
    all_solution_traces, all_final_results = get_answer(all_queries, db, answers, return_solution_traces=False, multi_threading=args.use_multithreading)

    all_full_questions = []
    progbar = tqdm(enumerate(templates), desc="Generating questions #2", total=len(templates))
    
    for i, (question_template, query_template, answer) in progbar:
        template_questions = all_questions[i]
        template_queries = all_queries[i]
        template_solution_traces = all_solution_traces[i]
        template_final_results = all_final_results[i]

        questions = []
        for j in range(len(template_final_results)):
            solution_trace = template_solution_traces[j]
            question = template_queries[j]
            query = template_questions[j]
            final_result = template_final_results[j]

            # get the difficulty of the question
            question_difficulty = calculate_query_difficulty(query)
            questions.append(
                {
                    "id": generate_unique_id(),
                    "question": question,
                    "intermediate_answers": json.dumps(solution_trace), # NOTE: serialize list of dicts so that it can be saved on HF
                    "answer": final_result,
                    "prolog": {"query": query, "answer": answer},
                    "template": question_template,
                    "type": i,  # this references the template type
                    "difficulty": question_difficulty,
                }
            )
            if args.question_format == "json_by_type":
                with open(os.path.join(question_dir, f"type{i}.json"), "w") as file:
                    json.dump(questions, file, indent=4)

        all_full_questions.extend(questions) # TODO: What is this?

        # update progbar
        progbar.set_description(f"Template ({i+1}/{len(templates)})")
    timings["questions_generate"] = time.time() - start

    blue("Saving questions")
    start = time.time()
    if args.question_format == "json":
        # save all questions to a single file
        save_path = os.path.join(args.output_dir, "questions.json")
        logging.info(f"Saving questions to: {save_path}")
        with open(save_path, "w") as file:
            json.dump(all_full_questions, file, indent=4)
    timings["questions_save"] = time.time() - start

    timings["total"] = time.time() - global_start

    logging.info("Benchmarking results:")
    df_timings = pd.DataFrame([timings])
    logging.info(df_timings.T.to_markdown())
    timings_path = os.path.join(args.output_dir, "timings.csv")
    logging.info(f"Saving timings to {timings_path}")
    df_timings.to_csv(timings_path, index=False)
    blue("Done!")


if __name__ == "__main__":
    # we combine a base parser with the family generator parser
    # TODO: add parser for other generation components
    # TODO: change --depth 10 --num-samples 1 --max-tree-size 50 --max-tree-depth 20 to be more informative
    # i.e. specify which depth corresponds to question depth, family tree depth etc.
    # - attribute
    parser = get_parser(
        parents=[
            fam_gen_parser,
            friend_gen_parser,
            question_parser,
        ]
    )
    args = parser.parse_args()
    main(args)
