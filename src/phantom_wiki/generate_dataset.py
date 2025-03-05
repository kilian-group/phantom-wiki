import copy
import json
import logging
import os
import time

import numpy as np
import pandas as pd
from tqdm import tqdm

from .core.article import get_articles
from .facts import get_database
from .facts.attributes import db_generate_attributes
from .facts.family import db_generate_family
from .facts.friends import db_generate_friendships
from .facts.question_difficulty import calculate_query_difficulty
from .facts.sample import sample_question
from .facts.templates import generate_templates
from .utils import blue, generate_unique_id
from .utils.get_answer import get_answer


def generate_dataset(
    max_branching_factor: int = 5,
    max_family_tree_depth: int = 5,
    max_family_tree_size: int = 25,
    num_family_trees: int = 1,
    stop_prob: int = 0,
    duplicate_names: bool = False,
    friendship_k: int = 3,
    friendship_seed: int = 1,
    num_questions_per_type: int = 10,
    num_sampling_attempts: int = 100,
    question_depth: int = 6,
    easy_mode: bool = False,
    skip_solution_traces: bool = False,
    debug: bool = False,
    quiet: bool = False,
    visualize: bool = False,
    use_multithreading: bool = False,
    seed: int = 1,
    output_dir: str = "./out",
    article_format: str = "txt",
    question_format: str = "json_by_type",
) -> None:
    """
    Generate a PhantomWiki dataset consisting of family trees, friendship networks,
    articles, and reasoning questions with answers.

    Args:
        max_branching_factor (int): The maximum number of children that any person
            in a family tree may have. (default=5)
        max_family_tree_depth (int): The maximum depth that a family tree may have.
            (default=5)
        max_family_tree_size (int): The maximum number of people that may appear
            in a family tree. (default=25)
        num_family_trees (int): The number of family trees to generate. (default=1)
        stop_prob (float): The probability of stopping to further extend a family tree
            after a person has been added. (default=0)
        duplicate_names (bool): Allow/prevent duplicate names in the generation.
            (default=False)
        friendship_k (int): Average degree in friendship graph. (default=3)
        friendship_seed (int): Seed for friendship generation. (default=1)
        num_questions_per_type (int): Number of questions to generate per question type
            (i.e., template). (default=10)
        num_sampling_attempts (int): Number of attempts to sample a valid question.
            (default=100)
        question_depth (int): Depth of the question template. (default=6)
        easy_mode (bool): Sample from easy relations (hard mode is default).
            (default=False)
        skip_solution_traces (bool): Do not include solution traces in the dataset.
            (default=False)
        debug (bool): Enable debug output (DEBUG level). (default=False)
        quiet (bool): Enable quiet (no) output (WARNING level). (default=False)
        visualize (bool): Whether or not to visualize the friendship & family graphs.
            (default=False)
        use_multithreading (bool): Use multithreading for querying the database when
            generating questions/answers. Note: This flag works for Windows and Linux,
            but not for MacOS. Also very intensive for high universe size. (default=False)
        seed (int): Global seed for random number generator. (default=1)
        output_dir (str): Path to the output folder. (default="./out")
        article_format (str): Format to save the generated articles. Options: 'txt', 'json'.
            (default="txt")
        question_format (str): Format to save the generated questions and answers.
            Options: 'json_by_type', 'json'. (default="json_by_type")

    Returns:
        None, The function saves all generated data to the output directory as well as a
        `timings.csv` and does not return any value.
    """
    assert article_format in ["txt", "json"], "Article format not supported, use 'txt' or 'json'."
    assert question_format in [
        "json_by_type",
        "json",
    ], "Question format not supported, use 'json_by_type' or 'json'."

    if quiet:
        log_level = logging.WARNING
    elif debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(level=log_level, format="%(message)s", handlers=[logging.StreamHandler()])

    os.makedirs(output_dir, exist_ok=True)
    logging.info(f"Output dir: {output_dir}")

    # create dictionary to store timings
    timings = {}
    global_start = time.time()

    #
    # Step 1. Generate facts
    #
    db = get_database()

    blue("Generating facts")
    start = time.time()
    # generate family tree
    db_generate_family(
        db,
        seed,
        duplicate_names,
        debug,
        output_dir,
        visualize,
        max_family_tree_depth,
        max_branching_factor,
        max_family_tree_size,
        stop_prob,
        num_family_trees,
    )

    # generate friend relationships between people in the database
    db_generate_friendships(db, friendship_k, friendship_seed, visualize, output_dir)

    # generate jobs, hobbies for each person in the database
    db_generate_attributes(db, seed)

    timings["facts_generate"] = time.time() - start

    db_path = os.path.join(output_dir, "facts.pl")
    blue(f"Saving Prolog database to {db_path}")
    facts_time = time.time()
    db.save_to_disk(db_path)
    timings["facts_save"] = time.time() - facts_time

    #
    # Step 2. Generate articles
    # Currently, the articles comprise a list of facts.
    #
    blue("Generating articles")
    start = time.time()
    articles = get_articles(db, db.get_person_names())
    timings["articles_generate"] = time.time() - start

    blue("Saving articles")
    start = time.time()
    if article_format == "txt":
        article_dir = os.path.join(output_dir, "articles")
        logging.info(f"Saving articles to: {article_dir}")
        os.makedirs(article_dir, exist_ok=True)
        for name, (article, facts) in articles.items():
            with open(os.path.join(article_dir, f"{name}.txt"), "w") as file:
                file.write(article)
            with open(os.path.join(article_dir, f"{name}_facts.txt"), "w") as file:
                file.write("\n".join(facts))
    elif article_format == "json":
        save_path = os.path.join(output_dir, "articles.json")
        logging.info(f"Saving articles to: {save_path}")
        with open(save_path, "w") as file:
            json.dump(
                [
                    {"title": name, "article": article, "facts": facts}
                    for name, (article, facts) in articles.items()
                ],
                file,
                indent=4,
            )
    else:
        raise ValueError(f"Article format {article_format} not supported!")
    timings["articles_save"] = time.time() - start

    #
    # Step 3. Generate question-answer pairs
    #
    blue("Generating question answer pairs")
    start = time.time()
    # generate question templates with a given depth
    templates = generate_templates(depth=question_depth)
    # sample questions for each template (i.e., type)
    if question_format == "json_by_type":
        question_dir = os.path.join(output_dir, "questions")
        logging.info(f"Saving questions to: {question_dir}")
        os.makedirs(question_dir, exist_ok=True)

    progbar = tqdm(enumerate(templates), desc="Generating questions", total=len(templates))

    # Populate person name bank for the universe. The list is static across generating questions
    # so create it once and pass it to the question generation function
    person_name_bank: list[str] = db.get_person_names()

    # Create caches for person -> (attr name, attr value) and person -> (relation, related person) pairs
    # When we iterate over multiple questions, we can reuse the same cache to avoid recomputing
    # e.g. "John" -> [("dob", "1990-01-01"), ("job", "teacher"), ("hobby", "reading"),
    # ("hobby", "swimming"), ...]
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
        rng = np.random.default_rng(seed)

        # To store the questions and queries for the given template
        questions = []
        queries = []

        # for _ in range(args.num_questions_per_type):
        while (
            len(questions)
            < num_questions_per_type
            # TODO: handle potential edge cases where templates repeatedly fail to generate,
            # resulting in an infinite loop
        ):  # TODO: temporary fix to make sure that we generate the same number of questions for each template
            # sample a question
            question, query = sample_question(
                question_template,
                query_template,
                rng,
                db,
                person_name_bank,
                person_name2attr_name_and_val,
                person_name2relation_and_related,
                easy_mode=easy_mode,
                num_sampling_attempts=num_sampling_attempts,
            )

            questions.append(question)
            queries.append(query)

        all_questions.append(questions)
        all_queries.append(queries)

    # Get all possible answers/solution traces for the queries
    answers = [t[2] for t in templates]
    all_solution_traces, all_final_results = get_answer(
        copy.deepcopy(all_queries),
        db,
        answers,
        skip_solution_traces=skip_solution_traces,
        multi_threading=use_multithreading,
    )

    all_full_questions = []
    progbar = tqdm(enumerate(templates), desc="Generating questions #2", total=len(templates))

    for i, (question_template, query_template, answer) in progbar:
        questions = []

        for j in range(num_questions_per_type):
            # get the difficulty of the question
            question_difficulty = calculate_query_difficulty(all_queries[i][j])

            questions.append(
                {
                    "id": generate_unique_id(),
                    "question": all_questions[i][j],
                    "solution_traces": json.dumps(
                        all_solution_traces[i][j]
                    ),  # NOTE: serialize list of dicts so that it can be saved on HF
                    "answer": all_final_results[i][j],
                    "prolog": {"query": all_queries[i][j], "answer": answer},
                    "template": question_template,
                    "type": i,  # this references the template type
                    "difficulty": question_difficulty,
                }
            )
            if question_format == "json_by_type":
                with open(os.path.join(question_dir, f"type{i}.json"), "w") as file:
                    json.dump(questions, file, indent=4)

        all_full_questions.extend(questions)

        # update progbar
        progbar.set_description(f"Template ({i+1}/{len(templates)})")
    timings["questions_generate"] = time.time() - start

    blue("Saving questions")
    start = time.time()
    if question_format == "json":
        # save all questions to a single file
        save_path = os.path.join(output_dir, "questions.json")
        logging.info(f"Saving questions to: {save_path}")
        with open(save_path, "w") as file:
            json.dump(all_full_questions, file, indent=4)
    timings["questions_save"] = time.time() - start

    timings["total"] = time.time() - global_start

    logging.info("Benchmarking results:")
    df_timings = pd.DataFrame([timings])
    logging.info(df_timings.T.to_markdown())
    timings_path = os.path.join(output_dir, "timings.csv")
    logging.info(f"Saving timings to {timings_path}")
    df_timings.to_csv(timings_path, index=False)
    blue("Done!")
