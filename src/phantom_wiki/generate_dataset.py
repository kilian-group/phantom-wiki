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
from .facts.balanced_sampling import balanced_sample, filter_by_difficulty, sample_questions
from .facts.balanced_sampling import describe_pool as _describe_pool
from .facts.extended_questions import (
    build_comparison_count_variants,
    build_extended_question_category,
    build_extended_question_types,
    get_extended_answer,
    is_extended_question,
    sample_extended_question,
)
from .facts.family import db_generate_family
from .facts.friends import db_generate_friendships
from .facts.difficulty import compute_difficulty
from .facts.question_difficulty import calculate_query_difficulty
from .facts.bidirectional_sample import sample_question_bidirectional
from .facts.inverse_relations import register_inverse_predicates
from .facts.attributes.constants import ATTRIBUTE_TYPES
from .facts.sample import get_relation_bank, prewarm_forward_cache, prewarm_inverse_cache, sample_question
from .facts.templates import (
    ALL_QUESTION_TYPES,
    QUESTION_TYPE_BASE,
    classify_question_type,
    generate_templates,
    is_aggregation_question,
    is_comparison_older_subtype,
    is_comparison_subtype,
    is_comparison_younger_subtype,
)
from .utils import blue, generate_unique_id
from .utils.get_answer import get_answer


def _lookup_dob(name: str, attr_cache: dict[str, list[tuple[str, str]]]) -> str | None:
    for attr, val in attr_cache.get(name, ()):
        if attr == "dob":
            return val
    return None



def _get_extended_cfg_answer(
    question: str,
    query: list[str],
    answer_info,
    question_subtype: str,
    db,
    bindings: dict[str, str] | None = None,
    attr_cache: dict[str, list[tuple[str, str]]] | None = None,
) -> list[str]:
    """Extract answers for extended CFG question types.

    Fast path (comparisons): when ``bindings`` and ``attr_cache`` are provided, resolve
    both branches to concrete names via the sampler's bindings and compare DOBs in
    Python using the cache — no Prolog calls needed.

    Slow path (superlative / multi-constraint, or cache miss): run the Prolog query.
    """
    from .utils import decode

    # Fast path: age/born-first comparisons via cached DOB lookups.
    if (
        bindings is not None
        and attr_cache is not None
        and is_comparison_subtype(question_subtype)
    ):
        left_var, right_var = answer_info
        left_name = bindings.get(left_var)
        right_name = bindings.get(right_var)
        if left_name and right_name:
            left_dob = _lookup_dob(left_name, attr_cache)
            right_dob = _lookup_dob(right_name, attr_cache)
            if left_dob is not None and right_dob is not None:
                if is_comparison_younger_subtype(question_subtype):
                    # younger = later DOB
                    return [left_name] if left_dob > right_dob else [right_name]
                # older / born first = earlier DOB
                return [left_name] if left_dob < right_dob else [right_name]

    joined = ", ".join(reversed(query))

    # Slow path for comparisons (missing bindings/cache/DOB): existence-check Prolog.
    if is_comparison_older_subtype(question_subtype):
        left_var, right_var = answer_info
        first = next(iter(db.prolog.query(joined)), None)
        if first is not None:
            if left_var in first:
                return [str(decode(first[left_var]))]
            import re
            m = re.match(r'Who is older, (.+?) or', question) or re.match(
                r'Who was born first, (.+?) or', question
            )
            return [m.group(1)] if m else []
        import re
        m = re.match(r'.+ or (.+?)\?', question)
        return [m.group(1)] if m else []

    if is_comparison_younger_subtype(question_subtype):
        first = next(iter(db.prolog.query(joined)), None)
        if first is not None:
            # Left won the older/born-first comparison → right is younger (answer)
            import re
            m = re.match(r'.+ or (.+?)\?', question)
            return [m.group(1)] if m else []
        import re
        m = re.match(r'Who is younger, (.+?) or', question)
        return [m.group(1)] if m else []

    # Superlative and multi-constraint: answer_info is a variable name like 'Y_5'
    answers = {
        str(decode(r[answer_info]))
        for r in db.prolog.query(joined)
        if answer_info in r
    }
    return sorted(answers)


def _filter_by_constraints(questions: list[dict], min_constraints: int = None, max_constraints: int = None) -> list[dict]:
    """Filter questions by constraint count from the structured difficulty field."""
    filtered = []
    for q in questions:
        diff = q.get("difficulty", {})
        constraints = diff.get("constraints", 0) if isinstance(diff, dict) else 0
        if min_constraints is not None and constraints < min_constraints:
            continue
        if max_constraints is not None and constraints > max_constraints:
            continue
        filtered.append(q)
    return filtered


def _filter_by_hops(questions: list[dict], min_hops: int = None, max_hops: int = None) -> list[dict]:
    """Filter questions by hop count from the structured difficulty field."""
    filtered = []
    for q in questions:
        diff = q.get("difficulty", {})
        if isinstance(diff, dict):
            hops = diff.get("hops", 0)
        else:
            hops = diff
        if min_hops is not None and hops < min_hops:
            continue
        if max_hops is not None and hops > max_hops:
            continue
        filtered.append(q)
    return filtered


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
    max_hops: int = 4,
    max_constraints: int = 3,
    easy_mode: bool = False,
    skip_solution_traces: bool = False,
    debug: bool = False,
    quiet: bool = False,
    visualize: bool = False,
    num_multiprocesses: int = 1,
    seed: int = 1,
    output_dir: str = "./out",
    article_format: str = "txt",
    question_format: str = "json_by_type",
    balanced: bool = False,
    min_difficulty: int = None,
    max_difficulty: int = None,
    question_types: str = "base",
    min_hops: int = None,
    min_constraints: int = None,
    sample_count: int = None,
    sample_min_steps: int = None,
    sample_max_steps: int = None,
    sample_types: str = None,
    describe_pool: bool = False,
    sampling_method: str = "bidirectional",
    anchor_strategy: str = "random",
    answer_position: str = "head",
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
        max_hops (int): Largest number of relation hops in any generated question.
            Drives both base CFG depth and the chain builders. (default=4)
        max_constraints (int): Largest number of attribute constraints in any
            generated question. Determines mc-N anchor sizes (n in 2..max_constraints)
            and the standalone multi-constraint sizes. (default=3)
        easy_mode (bool): Sample from easy relations (hard mode is default).
            (default=False)
        skip_solution_traces (bool): Do not include solution traces in the dataset.
            (default=False)
        debug (bool): Enable debug output (DEBUG level). (default=False)
        quiet (bool): Enable quiet (no) output (WARNING level). (default=False)
        visualize (bool): Whether or not to visualize the friendship & family graphs.
            (default=False)
        num_multiprocesses (int): Number of worker processes for batched Prolog queries.
            1 (default) runs serially; values >1 use multiprocessing.Pool(processes=N).
            Note: multiprocessing works on Windows and Linux but not on macOS; also
            memory-intensive for high universe sizes. (default=1)
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

    # Register inverse predicates for bidirectional sampling
    inverse_map = None
    if sampling_method == "bidirectional":
        blue("Registering inverse predicates for bidirectional sampling")
        inverse_map = register_inverse_predicates(db)

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
    articles = get_articles(db, db.get_person_names(), num_multiprocesses)
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

    # Parse question types
    if question_types is not None:
        parsed_qtypes = [t.strip() for t in question_types.split(",")]
    else:
        parsed_qtypes = list(ALL_QUESTION_TYPES)

    # Build the comparison_count variants table from CLI knobs. Used both as
    # the dispatch table for sampling and as the EXTENDED_QUESTION_TYPES /
    # EXTENDED_QUESTION_CATEGORY source for filtering.
    n_attrs_options: tuple[int, ...] = (0,) + tuple(range(2, max_constraints + 1))
    count_variants = build_comparison_count_variants(
        max_chain_depth=max(0, max_hops - 1),  # +1 from aggregate_all -> hops up to max_hops
        n_attrs_options=n_attrs_options,
    )
    extended_question_types = build_extended_question_types(count_variants)
    extended_question_category = build_extended_question_category(count_variants)
    multi_constraint_n_attrs = max(2, max_constraints)

    # generate question templates
    templates = generate_templates(
        max_hops=max_hops, max_constraints=max_constraints, question_types=parsed_qtypes,
    )

    # Separate base templates (3-tuples) from extended templates (4-tuples)
    base_templates = [t for t in templates if len(t) == 3]
    extended_cfg_templates = [t for t in templates if len(t) == 4]

    # sample questions for each template (i.e., type)
    if question_format == "json_by_type":
        question_dir = os.path.join(output_dir, "questions")
        logging.info(f"Saving questions to: {question_dir}")
        os.makedirs(question_dir, exist_ok=True)

    progbar = tqdm(enumerate(base_templates), desc="Generating questions", total=len(base_templates))

    # Populate person name bank for the universe. The list is static across generating questions
    # so create it once and pass it to the question generation function
    person_name_bank: list[str] = db.get_person_names()

    person_name2attr_name_and_val: dict[str, list[tuple[str, str]]] = {}
    person_name2relation_and_related: dict[str, list[tuple[str, str]]] = {}
    # Inverse relation cache for bidirectional sampling: R(A, "key") lookups
    person_name2inverse_relation: dict[str, list[tuple[str, str]]] = {}
    if sampling_method == "bidirectional":
        # Bulk-populate all three caches at once before sampling begins so there
        # are no cold-cache DB queries interleaved with sampling.
        prewarm_forward_cache(person_name2attr_name_and_val, db, ATTRIBUTE_TYPES, num_multiprocesses)
        relation_bank = get_relation_bank(easy_mode)
        prewarm_forward_cache(person_name2relation_and_related, db, relation_bank, num_multiprocesses)
        prewarm_inverse_cache(person_name2inverse_relation, db, relation_bank, num_multiprocesses)

    # To store all the questions and queries for all templates
    all_questions = []
    all_queries = []
    # Sampling metadata per template (only populated for bidirectional)
    all_sampling_metadata: list[list[dict | None]] = []

    # Balanced counter for bidirectional anchor strategy
    balanced_counter = [0]

    for i, (question_template, query_template, answer) in progbar:
        # Reset the seed at the start of each question type
        # so that sampled questions are the same for each question type
        rng = np.random.default_rng(seed)

        # To store the questions and queries for the given template
        questions = []
        queries = []
        metadata_list = []

        # Cap total sampling attempts to avoid infinite loops when
        # difficulty filtering rejects most samples for a template.
        max_total_attempts = num_questions_per_type * num_sampling_attempts
        total_attempts = 0

        while len(questions) < num_questions_per_type and total_attempts < max_total_attempts:
            total_attempts += 1
            if sampling_method == "bidirectional" and inverse_map is not None:
                result = sample_question_bidirectional(
                    question_template,
                    query_template,
                    rng,
                    db,
                    person_name_bank,
                    person_name2attr_name_and_val,
                    person_name2relation_and_related,
                    person_name2inverse_relation,
                    inverse_map,
                    num_multiprocesses,
                    easy_mode=easy_mode,
                    num_sampling_attempts=num_sampling_attempts,
                    anchor_strategy=anchor_strategy,
                    answer_position=answer_position,
                    _balanced_counter=balanced_counter,
                )
                if result is not None:
                    question, query, metadata = result
                else:
                    # Bidirectional failed — fall back to backward sampling
                    fallback = sample_question(
                        question_template,
                        query_template,
                        rng,
                        db,
                        person_name_bank,
                        person_name2attr_name_and_val,
                        person_name2relation_and_related,
                        num_multiprocesses,
                        easy_mode=easy_mode,
                        num_sampling_attempts=num_sampling_attempts,
                    )
                    if fallback is None:
                        continue
                    question, query = fallback
                    metadata = {"method": "backward_fallback"}
            else:
                # Default backward sampling
                fallback = sample_question(
                    question_template,
                    query_template,
                    rng,
                    db,
                    person_name_bank,
                    person_name2attr_name_and_val,
                    person_name2relation_and_related,
                    num_multiprocesses,
                    easy_mode=easy_mode,
                    num_sampling_attempts=num_sampling_attempts,
                )
                if fallback is None:
                    continue
                question, query = fallback
                metadata = None

            questions.append(question)
            queries.append(query)
            metadata_list.append(metadata)

        if len(questions) < num_questions_per_type:
            logging.warning(
                f"Template {i}: only generated {len(questions)}/{num_questions_per_type} questions"
            )

        all_questions.append(questions)
        all_queries.append(queries)
        all_sampling_metadata.append(metadata_list)

    # Generate extended CFG-based question types (comparison, multi-constraint, superlative)
    extended_cfg_questions_data = []
    if extended_cfg_templates:
        blue("Generating extended CFG question types")
        for tmpl_idx, tmpl in enumerate(extended_cfg_templates):
            question_template, query_template, answer_info, question_subtype = tmpl
            rng = np.random.default_rng(seed)
            questions = []
            queries = []
            bindings_list: list[dict[str, str]] = []
            attempts = 0
            max_attempts = num_questions_per_type * num_sampling_attempts

            while len(questions) < num_questions_per_type and attempts < max_attempts:
                attempts += 1
                try:
                    result = sample_question(
                        question_template,
                        query_template,
                        rng,
                        db,
                        person_name_bank,
                        person_name2attr_name_and_val,
                        person_name2relation_and_related,
                        num_multiprocesses,
                        easy_mode=easy_mode,
                        num_sampling_attempts=1,
                        return_bindings=True,
                    )
                    if result is not None:
                        question, query, bindings = result
                        questions.append(question)
                        queries.append(query)
                        bindings_list.append(bindings)
                except (ValueError, AssertionError):
                    continue

            # Get answers for extended CFG questions
            for j in range(len(questions)):
                answer_list = _get_extended_cfg_answer(
                    questions[j], queries[j], answer_info, question_subtype, db,
                    bindings=bindings_list[j],
                    attr_cache=person_name2attr_name_and_val,
                )
                q_type = classify_question_type(question_template)
                extended_cfg_questions_data.append(
                    {
                        "id": generate_unique_id(),
                        "question": questions[j],
                        "solution_traces": json.dumps([]),
                        "answer": answer_list,
                        "prolog": {"query": queries[j], "answer": str(answer_info)},
                        "template": question_template,
                        "type": len(base_templates) + tmpl_idx,
                        "difficulty": compute_difficulty(queries[j], answer_var=str(answer_info)),
                        "is_aggregation_question": False,
                        "question_category": question_subtype,
                    }
                )

    # Generate legacy extended question types (backward compat, standalone 1-hop)
    extended_questions_data = []
    if QUESTION_TYPE_BASE in parsed_qtypes:
        # Only generate extended variants whose high-level qtype is also in
        # parsed_qtypes — so e.g. dropping ``comparison_age`` from
        # --question-types skips "Who is older, A or B?" too.
        # Exclude "comparison_age": the CFG composer (`_build_comparison_templates`)
        # already covers the 0-hop "Who is older, NameA or NameB?" case via the
        # `(R_c → N) × (R_c → N)` pair, AND covers younger/born-first phrasings
        # the legacy sampler doesn't emit. Keeping legacy here would duplicate the
        # 0-hop "older" form.
        legacy_qtypes_to_run = [
            t for t in extended_question_types
            if extended_question_category[t] in parsed_qtypes
            and t != "comparison_age"
        ]
        blue("Generating extended question types")
        for qtype in legacy_qtypes_to_run:
            rng = np.random.default_rng(seed)
            questions = []
            queries = []
            attempts = 0
            max_attempts = num_questions_per_type * num_sampling_attempts
            while len(questions) < num_questions_per_type and attempts < max_attempts:
                attempts += 1
                result = sample_extended_question(
                    qtype,
                    rng,
                    db,
                    person_name_bank,
                    person_name2attr_name_and_val,
                    person_name2relation_and_related,
                    num_multiprocesses,
                    count_variants=count_variants,
                    multi_constraint_n_attrs=multi_constraint_n_attrs,
                    easy_mode=easy_mode,
                    num_sampling_attempts=num_sampling_attempts,
                )
                if result is not None:
                    question, query = result
                    questions.append(question)
                    queries.append(query)

            # Get answers for extended questions
            for j in range(len(questions)):
                answer_list = get_extended_answer(questions[j], queries[j], qtype, db, count_variants)
                extended_questions_data.append(
                    {
                        "id": generate_unique_id(),
                        "question": questions[j],
                        "solution_traces": json.dumps([]),
                        "answer": answer_list,
                        "prolog": {"query": queries[j], "answer": "X"},
                        "template": [qtype],
                        "type": len(base_templates) + len(extended_cfg_templates) + extended_question_types.index(qtype),
                        "difficulty": compute_difficulty(queries[j], answer_var="X"),
                        "is_aggregation_question": False,
                        "question_category": qtype,
                    }
                )

    # Get all possible answers/solution traces for the base queries
    answers = [t[2] for t in base_templates]
    all_solution_traces, all_final_results = get_answer(
        copy.deepcopy(all_queries),
        db,
        answers,
        skip_solution_traces=skip_solution_traces,
        num_procs=num_multiprocesses,
    )

    all_full_questions = []
    progbar = tqdm(enumerate(base_templates), desc="Generating questions #2", total=len(base_templates))

    for i, (question_template, query_template, answer) in progbar:
        questions = []

        for j in range(len(all_questions[i])):
            question = all_questions[i][j]
            query = all_queries[i][j]

            q_dict = {
                "id": generate_unique_id(),
                "question": question,
                "solution_traces": json.dumps(
                    all_solution_traces[i][j]
                ),  # NOTE: serialize list of dicts so that it can be saved on HF
                "answer": all_final_results[i][j],
                "prolog": {"query": query, "answer": answer},
                "template": question_template,
                "type": i,  # this references the template type
                "difficulty": compute_difficulty(query, answer_var=answer),
                "is_aggregation_question": is_aggregation_question(question),
            }
            # Add sampling metadata for bidirectional sampling
            sm = all_sampling_metadata[i][j] if i < len(all_sampling_metadata) else None
            if sm is not None:
                q_dict["sampling_metadata"] = sm
            questions.append(q_dict)
            if question_format == "json_by_type":
                with open(os.path.join(question_dir, f"type{i}.json"), "w") as file:
                    json.dump(questions, file, indent=4)

        all_full_questions.extend(questions)

        # update progbar
        progbar.set_description(f"Template ({i+1}/{len(base_templates)})")

    # Append extended CFG questions
    all_full_questions.extend(extended_cfg_questions_data)

    # Append legacy extended questions
    all_full_questions.extend(extended_questions_data)
    if question_format == "json_by_type" and extended_questions_data:
        for qtype in extended_question_types:
            type_qs = [q for q in extended_questions_data if q.get("question_category") == qtype]
            if type_qs:
                type_idx = len(base_templates) + len(extended_cfg_templates) + extended_question_types.index(qtype)
                with open(os.path.join(question_dir, f"type{type_idx}.json"), "w") as file:
                    json.dump(type_qs, file, indent=4)

    # Apply hop-count filtering
    if min_hops is not None or max_hops is not None:
        blue("Filtering questions by hop count")
        all_full_questions = _filter_by_hops(all_full_questions, min_hops, max_hops)
        logging.info(f"After hop filtering: {len(all_full_questions)} questions")

    # Apply constraint filtering
    if min_constraints is not None or max_constraints is not None:
        blue("Filtering questions by constraint count")
        all_full_questions = _filter_by_constraints(all_full_questions, min_constraints, max_constraints)
        logging.info(f"After constraint filtering: {len(all_full_questions)} questions")

    # Apply difficulty-based filtering and balanced sampling
    if min_difficulty is not None or max_difficulty is not None:
        blue("Filtering questions by difficulty range")
        all_full_questions = filter_by_difficulty(all_full_questions, min_difficulty, max_difficulty)
        logging.info(f"After filtering: {len(all_full_questions)} questions")

    if balanced:
        blue("Applying difficulty-balanced sampling")
        all_full_questions = balanced_sample(all_full_questions)
        logging.info(f"After balanced sampling: {len(all_full_questions)} questions")

    # Describe pool (print breakdown and exit)
    if describe_pool:
        pool_info = _describe_pool(all_full_questions)
        blue("Question Pool Breakdown")
        logging.info(f"Total questions: {pool_info['total']}")
        logging.info("")
        logging.info("By composite difficulty:")
        for composite, count in pool_info["by_composite"].items():
            logging.info(f"  {composite:>4d}: {count}")
        logging.info("")
        logging.info("By question type:")
        for qtype, count in pool_info["by_type"].items():
            logging.info(f"  {qtype:>20s}: {count}")
        logging.info("")
        logging.info("By composite difficulty and type:")
        for composite, type_counts in pool_info["by_composite_and_type"].items():
            if type_counts:
                logging.info(f"  {composite}:")
                for qtype, count in type_counts.items():
                    logging.info(f"    {qtype:>20s}: {count}")
        return

    # Apply exact sampling (--sample-count)
    if sample_count is not None:
        blue("Sampling exact number of questions")
        parsed_sample_types = None
        if sample_types is not None:
            parsed_sample_types = [t.strip() for t in sample_types.split(",")]
        all_full_questions = sample_questions(
            all_full_questions,
            count=sample_count,
            question_types=parsed_sample_types,
            min_steps=sample_min_steps,
            max_steps=sample_max_steps,
            seed=seed,
        )
        logging.info(f"After sampling: {len(all_full_questions)} questions")

    timings["questions_generate"] = time.time() - start

    blue("Saving questions")
    start = time.time()
    if question_format == "json":
        save_path = os.path.join(output_dir, "questions.json")
        logging.info(f"Saving questions to: {save_path}")
        with open(save_path, "w") as file:
            json.dump(all_full_questions, file, indent=4)
    elif question_format == "json_by_type":
        # Re-write type files after filtering/sampling
        by_type: dict[int, list[dict]] = {}
        for q in all_full_questions:
            by_type.setdefault(q["type"], []).append(q)
        for type_id, type_qs in by_type.items():
            with open(os.path.join(question_dir, f"type{type_id}.json"), "w") as file:
                json.dump(type_qs, file, indent=4)
        # Remove type files that no longer have questions after filtering
        for fname in os.listdir(question_dir):
            if fname.startswith("type") and fname.endswith(".json"):
                type_id = int(fname[4:-5])
                if type_id not in by_type:
                    os.remove(os.path.join(question_dir, fname))
    timings["questions_save"] = time.time() - start

    timings["total"] = time.time() - global_start

    logging.info("Benchmarking results:")
    df_timings = pd.DataFrame([timings])
    logging.info(df_timings.T.to_markdown())
    timings_path = os.path.join(output_dir, "timings.csv")
    logging.info(f"Saving timings to {timings_path}")
    df_timings.to_csv(timings_path, index=False)
    blue("Done!")
