"""Profile bidirectional sampling with vs without count_solutions.

Compares the removed db.query() counting step against the current code.
"""

import itertools
import os
import sys
import time

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


def build_universe(n_target, seed=1):
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


def run_profile(sizes, num_questions, depth, seed):
    templates_all = generate_templates(depth=depth, question_types=["base"])
    base_templates = [t for t in templates_all if len(t) == 3]

    for n in sizes:
        print(f"\n{'='*70}")
        print(f"Universe size target: n={n}")
        print(f"{'='*70}")

        db = build_universe(n, seed=seed)
        person_names = db.get_person_names()
        actual_n = len(person_names)
        print(f"  Actual universe size: {actual_n}")

        attr_cache: dict = {}
        rel_cache: dict = {}
        for name in person_names:
            get_vals_and_update_cache(attr_cache, name, db, ATTRIBUTE_TYPES)
            get_vals_and_update_cache(rel_cache, name, db, RELATION)

        inverse_map = register_inverse_predicates(db)
        inv_cache: dict = {}
        prewarm_inverse_cache(inv_cache, db, RELATION)

        # ---- Run WITHOUT count (current code) ----
        rng = np.random.default_rng(seed)
        successes_no_count = 0
        t_sample_no_count = 0.0

        for i in range(num_questions):
            tmpl = base_templates[i % len(base_templates)]
            q_template, query_template, answer = tmpl

            t0 = time.perf_counter()
            result = sample_question_bidirectional(
                q_template, query_template, rng, db, person_names,
                attr_cache, rel_cache, inv_cache, inverse_map,
                easy_mode=False, num_sampling_attempts=100,
                anchor_strategy="random",
            )
            t_sample_no_count += time.perf_counter() - t0
            if result is not None:
                successes_no_count += 1

        # ---- Run WITH count (old behavior, inline) ----
        rng = np.random.default_rng(seed)
        successes_with_count = 0
        t_sample_with_count = 0.0
        t_counting_only = 0.0

        for i in range(num_questions):
            tmpl = base_templates[i % len(base_templates)]
            q_template, query_template, answer = tmpl

            t0 = time.perf_counter()
            result = sample_question_bidirectional(
                q_template, query_template, rng, db, person_names,
                attr_cache, rel_cache, inv_cache, inverse_map,
                easy_mode=False, num_sampling_attempts=100,
                anchor_strategy="random",
            )
            t_after_sample = time.perf_counter()
            t_sample_with_count += t_after_sample - t0

            # Simulate the removed count_solutions logic
            if result is not None:
                successes_with_count += 1
                _question, query, _meta = result
                joined_for_count = ", ".join(reversed(query))
                tc0 = time.perf_counter()
                try:
                    capped = list(itertools.islice(db.query(joined_for_count), 50))
                    _ = len(capped)
                except Exception:
                    pass
                tc1 = time.perf_counter()
                t_counting_only += tc1 - tc0
                t_sample_with_count += tc1 - tc0

        # ---- Report ----
        print(f"\n  {'Metric':<40s} {'Without count':>15s} {'With count':>15s} {'Diff':>12s}")
        print(f"  {'-'*82}")

        no_count_ms = t_sample_no_count * 1000
        with_count_ms = t_sample_with_count * 1000
        counting_ms = t_counting_only * 1000
        diff_ms = with_count_ms - no_count_ms
        pct = (diff_ms / no_count_ms * 100) if no_count_ms > 0 else 0

        print(f"  {'Total time (ms)':<40s} {no_count_ms:>15.1f} {with_count_ms:>15.1f} {diff_ms:>+11.1f}ms")
        print(f"  {'Per-question (ms)':<40s} {no_count_ms/num_questions:>15.3f} {with_count_ms/num_questions:>15.3f}")
        print(f"  {'Time in count_solutions only (ms)':<40s} {'n/a':>15s} {counting_ms:>15.1f}")
        print(f"  {'count_solutions % of total':<40s} {'n/a':>15s} {counting_ms/with_count_ms*100 if with_count_ms > 0 else 0:>14.1f}%")
        print(f"  {'Slowdown from count':<40s} {'':>15s} {pct:>+11.1f}%")
        print(f"  {'Successes':<40s} {successes_no_count:>15d} {successes_with_count:>15d}")

        # Also benchmark backward for reference
        rng = np.random.default_rng(seed)
        successes_bw = 0
        t0 = time.perf_counter()
        for i in range(num_questions):
            tmpl = base_templates[i % len(base_templates)]
            q_template, query_template, answer = tmpl
            result = sample_question(
                q_template, query_template, rng, db, person_names,
                attr_cache, rel_cache, easy_mode=False, num_sampling_attempts=100,
            )
            if result is not None:
                successes_bw += 1
        bw_ms = (time.perf_counter() - t0) * 1000

        print(f"\n  {'backward (reference)':<40s} {bw_ms:>15.1f}ms total, {bw_ms/num_questions:>7.3f} ms/q, success={successes_bw}/{num_questions}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", type=str, default="100,500,1000")
    parser.add_argument("--num-questions", type=int, default=200)
    parser.add_argument("--depth", type=int, default=5)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    sizes = [int(s.strip()) for s in args.sizes.split(",")]
    run_profile(sizes, args.num_questions, args.depth, args.seed)
