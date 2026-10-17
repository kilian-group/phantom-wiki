"""Benchmark sampling methods across universe sizes.

Measures wall-clock time, per-question time, and retry counts for:
- backward (current default)
- bidirectional_prolog (new Prolog-based bidirectional)

Usage:
    python scripts/benchmark_sampling_methods.py
    python scripts/benchmark_sampling_methods.py --sizes 50,500 --num-questions 100

Output: ASCII table to stdout + CSV to scripts/benchmark_results.csv
"""

import argparse
import csv
import gc
import os
import sys
import time
import tracemalloc

import numpy as np

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


def build_universe(n_target: int, seed: int = 1):
    """Build a universe of approximately n_target people."""
    db = get_database()

    num_trees = max(1, n_target // 25)
    max_size = min(n_target, 25)

    db_generate_family(
        db, seed=seed, duplicate_names=False, debug=False,
        output_dir="/tmp/bench_phantom",
        visualize=False, max_family_tree_depth=5, max_branching_factor=5,
        max_family_tree_size=max_size, stop_prob=0, num_family_trees=num_trees,
    )
    db_generate_friendships(db, friendship_k=3, friendship_seed=seed, visualize=False, output_dir="/tmp/bench_phantom")
    db_generate_attributes(db, seed=seed)
    return db


def benchmark_backward(templates, db, person_names, attr_cache, rel_cache,
                       num_questions, seed, easy_mode=False):
    rng = np.random.default_rng(seed)
    successes = 0
    start = time.perf_counter()
    for i in range(num_questions):
        tmpl = templates[i % len(templates)]
        q_template, query_template, answer = tmpl
        result = sample_question(
            q_template, query_template, rng, db, person_names,
            attr_cache, rel_cache, easy_mode=easy_mode,
            num_sampling_attempts=100,
        )
        if result is not None:
            successes += 1
    elapsed = time.perf_counter() - start
    return elapsed, successes, 0


def benchmark_bidirectional(templates, db, person_names, attr_cache, rel_cache,
                            num_questions, seed, easy_mode=False):
    inverse_map = register_inverse_predicates(db)
    inv_cache: dict[str, list[tuple[str, str]]] = {}
    prewarm_inverse_cache(inv_cache, db, RELATION)
    rng = np.random.default_rng(seed)
    successes = 0
    start = time.perf_counter()
    for i in range(num_questions):
        tmpl = templates[i % len(templates)]
        q_template, query_template, answer = tmpl
        result = sample_question_bidirectional(
            q_template, query_template, rng, db, person_names,
            attr_cache, rel_cache, inv_cache, inverse_map,
            easy_mode=easy_mode, num_sampling_attempts=100,
            anchor_strategy="random",
        )
        if result is not None:
            successes += 1
    elapsed = time.perf_counter() - start
    return elapsed, successes, 0


def run_benchmarks(sizes, num_questions, depth, seed):
    templates_all = generate_templates(depth=depth, question_types=["base"])
    base_templates = [t for t in templates_all if len(t) == 3]

    results = []
    methods = [
        ("backward", benchmark_backward),
        ("bidirectional_prolog", benchmark_bidirectional),
    ]

    for n in sizes:
        print(f"\n{'='*60}")
        print(f"Universe size target: n={n}")
        print(f"{'='*60}")

        db = build_universe(n, seed=seed)
        person_names = db.get_person_names()
        actual_n = len(person_names)
        print(f"  Actual universe size: {actual_n}")

        attr_cache: dict[str, list[tuple[str, str]]] = {}
        rel_cache: dict[str, list[tuple[str, str]]] = {}
        for name in person_names:
            get_vals_and_update_cache(attr_cache, name, db, ATTRIBUTE_TYPES)
            get_vals_and_update_cache(rel_cache, name, db, RELATION)

        for method_name, method_fn in methods:
            gc.collect()
            tracemalloc.start()

            elapsed, successes, retries = method_fn(
                base_templates, db, person_names, attr_cache, rel_cache,
                num_questions, seed,
            )

            _, peak_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            per_q = (elapsed / num_questions) * 1000
            row = {
                "n": actual_n,
                "method": method_name,
                "total_ms": round(elapsed * 1000, 1),
                "per_q_ms": round(per_q, 3),
                "successes": successes,
                "retries": retries,
                "peak_mem_mb": round(peak_mem / 1024 / 1024, 1),
            }
            results.append(row)
            print(f"  {method_name:30s}  {row['total_ms']:>8.1f} ms total, "
                  f"{row['per_q_ms']:>7.3f} ms/q, "
                  f"success={successes}/{num_questions}, "
                  f"mem={row['peak_mem_mb']:.1f} MB")

    return results


def print_table(results):
    print(f"\n{'='*70}")
    print(f"Sampling Method Performance (depth=5, per universe size)")
    print(f"{'='*70}")

    by_n = {}
    for r in results:
        by_n.setdefault(r["n"], []).append(r)

    for n, rows in sorted(by_n.items()):
        print(f"\nn={n}:")
        for r in rows:
            print(f"  {r['method']:30s}  {r['total_ms']:>8.1f} ms total, "
                  f"{r['per_q_ms']:>7.3f} ms/q, "
                  f"retries={r['retries']}, "
                  f"success={r['successes']}")


def save_csv(results, path):
    if not results:
        return
    keys = results[0].keys()
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)
    print(f"\nResults saved to {path}")


def main():
    parser = argparse.ArgumentParser(description="Benchmark sampling methods")
    parser.add_argument("--sizes", type=str, default="50,500",
                        help="Comma-separated universe sizes (default: 50,500)")
    parser.add_argument("--num-questions", type=int, default=100,
                        help="Questions per method per size (default: 100)")
    parser.add_argument("--depth", type=int, default=5,
                        help="Question template depth (default: 5)")
    parser.add_argument("--seed", type=int, default=1,
                        help="Random seed (default: 1)")
    parser.add_argument("--output", type=str, default="scripts/benchmark_results.csv",
                        help="Output CSV path")
    args = parser.parse_args()

    sizes = [int(s.strip()) for s in args.sizes.split(",")]
    results = run_benchmarks(sizes, args.num_questions, args.depth, args.seed)
    print_table(results)
    save_csv(results, args.output)


if __name__ == "__main__":
    main()
