"""Validate anchor position distribution across sampling methods.

Generates questions and reports:
- Anchor position distribution (start/middle/end)
- Chi-square test against uniform distribution
- Polarity distribution (anchor-answer relationship)
- Per-position answer correctness

Usage:
    python scripts/validate_anchor_distribution.py
    python scripts/validate_anchor_distribution.py --num-questions 5000
"""

import argparse
import os
import sys
from collections import Counter

import numpy as np
from scipy import stats

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from phantom_wiki.facts import get_database
from phantom_wiki.facts.attributes import db_generate_attributes
from phantom_wiki.facts.attributes.constants import ATTRIBUTE_TYPES
from phantom_wiki.facts.bidirectional_sample import sample_question_bidirectional
from phantom_wiki.facts.family import db_generate_family
from phantom_wiki.facts.friends import db_generate_friendships
from phantom_wiki.facts.inverse_relations import register_inverse_predicates
from phantom_wiki.facts.sample import RELATION, get_vals_and_update_cache, prewarm_inverse_cache, sample_question
from phantom_wiki.facts.templates import generate_templates
from phantom_wiki.utils import decode


def build_test_universe(seed=42):
    db = get_database()
    db_generate_family(
        db, seed=seed, duplicate_names=False, debug=False,
        output_dir="/tmp/validate_phantom",
        visualize=False, max_family_tree_depth=5, max_branching_factor=5,
        max_family_tree_size=25, stop_prob=0, num_family_trees=4,
    )
    db_generate_friendships(db, friendship_k=3, friendship_seed=seed, visualize=False,
                            output_dir="/tmp/validate_phantom")
    db_generate_attributes(db, seed=seed)
    return db


def generate_backward_questions(templates, db, person_names, attr_cache, rel_cache,
                                num_questions, seed):
    rng = np.random.default_rng(seed)
    results = []
    attempts = 0
    while len(results) < num_questions and attempts < num_questions * 20:
        attempts += 1
        tmpl = templates[attempts % len(templates)]
        q_template, query_template, answer = tmpl
        result = sample_question(
            q_template, query_template, rng, db, person_names,
            attr_cache, rel_cache, num_sampling_attempts=50,
        )
        if result is not None:
            question, query = result
            chain_len = len(query_template)
            results.append({
                "question": question,
                "query": query,
                "anchor_position": "end",
                "anchor_slot_index": chain_len - 1,
                "polarity": "opposite",
                "answer_position": "head",
            })
    return results


def generate_bidirectional_questions(templates, db, person_names, attr_cache, rel_cache,
                                     num_questions, seed, anchor_strategy="random"):
    inverse_map = register_inverse_predicates(db)
    inv_cache: dict[str, list[tuple[str, str]]] = {}
    prewarm_inverse_cache(inv_cache, db, RELATION)
    rng = np.random.default_rng(seed)
    results = []
    attempts = 0
    while len(results) < num_questions and attempts < num_questions * 20:
        attempts += 1
        tmpl = templates[attempts % len(templates)]
        q_template, query_template, answer = tmpl
        result = sample_question_bidirectional(
            q_template, query_template, rng, db, person_names,
            attr_cache, rel_cache, inv_cache, inverse_map,
            num_sampling_attempts=50,
            anchor_strategy=anchor_strategy,
        )
        if result is not None:
            question, query, metadata = result
            results.append({
                "question": question,
                "query": query,
                **metadata,
            })
    return results


def check_correctness(questions, db):
    correct = 0
    total = len(questions)
    for q in questions:
        query = q["query"]
        joined = ", ".join(reversed(query))
        try:
            results = list(db.prolog.query(joined))
            if results:
                correct += 1
        except Exception:
            pass
    return correct, total


def analyze_distribution(questions, method_name):
    print(f"\n{'='*60}")
    print(f"  {method_name}")
    print(f"{'='*60}")
    print(f"  Total questions: {len(questions)}")

    # Anchor position distribution
    anchor_positions = Counter(q.get("anchor_position", "unknown") for q in questions)
    print(f"\n  Anchor position distribution:")
    for pos in ["start", "middle", "end", "unknown"]:
        count = anchor_positions.get(pos, 0)
        pct = (count / len(questions) * 100) if questions else 0
        print(f"    {pos:>8s}: {count:>5d} ({pct:.1f}%)")

    # Chi-square test for uniformity over observed categories
    all_positions = ["start", "middle", "end"]
    observed_positions = [p for p in all_positions if anchor_positions.get(p, 0) > 0]
    observed_counts = [anchor_positions[p] for p in observed_positions]
    if len(observed_positions) >= 2:
        total_obs = sum(observed_counts)
        k = len(observed_positions)
        expected = [total_obs / k] * k
        chi2, p_value = stats.chisquare(observed_counts, expected)
        uniform = "YES" if p_value > 0.05 else "NO"
        print(f"\n  Chi-square test for uniformity ({'/'.join(observed_positions)}):")
        print(f"    chi2={chi2:.2f}, p={p_value:.4f}  → Uniform: {uniform}")
    else:
        print(f"\n  Chi-square test: SKIPPED (only {len(observed_positions)} non-zero categories)")

    # Polarity distribution
    polarities = Counter(q.get("polarity", "unknown") for q in questions)
    print(f"\n  Polarity distribution:")
    for pol, count in sorted(polarities.items()):
        pct = (count / len(questions) * 100) if questions else 0
        print(f"    {pol:>10s}: {count:>5d} ({pct:.1f}%)")

    # Answer position distribution
    answer_positions = Counter(q.get("answer_position", "head") for q in questions)
    print(f"\n  Answer position distribution:")
    for pos, count in sorted(answer_positions.items()):
        pct = (count / len(questions) * 100) if questions else 0
        print(f"    {pos:>6s}: {count:>5d} ({pct:.1f}%)")

    return anchor_positions


def main():
    parser = argparse.ArgumentParser(description="Validate anchor distribution")
    parser.add_argument("--num-questions", type=int, default=500,
                        help="Questions to generate per method (default: 500)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--depth", type=int, default=5)
    args = parser.parse_args()

    print("Building test universe...")
    db = build_test_universe(seed=args.seed)
    person_names = db.get_person_names()
    print(f"Universe size: {len(person_names)} people")

    attr_cache: dict[str, list[tuple[str, str]]] = {}
    rel_cache: dict[str, list[tuple[str, str]]] = {}
    for name in person_names:
        get_vals_and_update_cache(attr_cache, name, db, ATTRIBUTE_TYPES)
        get_vals_and_update_cache(rel_cache, name, db, RELATION)

    templates_all = generate_templates(depth=args.depth, question_types=["base"])
    base_templates = [t for t in templates_all if len(t) == 3]
    print(f"Templates: {len(base_templates)}")

    # Backward sampling
    print("\nGenerating backward questions...")
    backward_qs = generate_backward_questions(
        base_templates, db, person_names, attr_cache, rel_cache,
        args.num_questions, args.seed,
    )
    analyze_distribution(backward_qs, "backward (baseline)")
    correct, total = check_correctness(backward_qs, db)
    print(f"\n  Correctness: {correct}/{total}")

    # Bidirectional sampling (random anchor)
    print("\nGenerating bidirectional (random) questions...")
    bidir_qs = generate_bidirectional_questions(
        base_templates, db, person_names, attr_cache, rel_cache,
        args.num_questions, args.seed, anchor_strategy="random",
    )
    analyze_distribution(bidir_qs, "bidirectional_prolog (anchor=random)")
    correct, total = check_correctness(bidir_qs, db)
    print(f"\n  Correctness: {correct}/{total}")

    # Bidirectional sampling (balanced anchor)
    print("\nGenerating bidirectional (balanced) questions...")
    bidir_balanced_qs = generate_bidirectional_questions(
        base_templates, db, person_names, attr_cache, rel_cache,
        args.num_questions, args.seed, anchor_strategy="balanced",
    )
    analyze_distribution(bidir_balanced_qs, "bidirectional_prolog (anchor=balanced)")
    correct, total = check_correctness(bidir_balanced_qs, db)
    print(f"\n  Correctness: {correct}/{total}")

    print(f"\n{'='*60}")
    print("Validation complete.")


if __name__ == "__main__":
    main()
