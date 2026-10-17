"""Profile bidirectional sampling with n=1000 using cProfile + pstats."""

import cProfile
import io
import os
import pstats
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
from phantom_wiki.facts.sample import RELATION, get_vals_and_update_cache, prewarm_forward_cache, prewarm_inverse_cache
from phantom_wiki.facts.templates import generate_templates


N_TARGET = 1000
NUM_QUESTIONS = 300
DEPTH = 5
SEED = 42
TOP_N = 30  # number of functions to show in profile report


def build_universe(n_target, seed):
    db = get_database()
    num_trees = max(1, n_target // 25)
    max_size = min(n_target, 25)
    db_generate_family(
        db, seed=seed, duplicate_names=False, debug=False,
        output_dir="/tmp/profile_phantom",
        visualize=False, max_family_tree_depth=5, max_branching_factor=5,
        max_family_tree_size=max_size, stop_prob=0, num_family_trees=num_trees,
    )
    db_generate_friendships(
        db, friendship_k=3, friendship_seed=seed,
        visualize=False, output_dir="/tmp/profile_phantom",
    )
    db_generate_attributes(db, seed=seed)
    return db


def warmup_caches_old(db, person_names):
    """Original per-person approach (O(N*Q) queries)."""
    attr_cache: dict = {}
    rel_cache: dict = {}
    for name in person_names:
        get_vals_and_update_cache(attr_cache, name, db, ATTRIBUTE_TYPES, num_procs=1)
        get_vals_and_update_cache(rel_cache, name, db, RELATION, num_procs=1)

    inverse_map = register_inverse_predicates(db)
    inv_cache: dict = {}
    prewarm_inverse_cache(inv_cache, db, RELATION, num_procs=1)
    return attr_cache, rel_cache, inv_cache, inverse_map


def warmup_caches_new(db):
    """New bulk approach (O(total_facts) queries)."""
    attr_cache: dict = {}
    prewarm_forward_cache(attr_cache, db, ATTRIBUTE_TYPES, num_procs=1)

    rel_cache: dict = {}
    prewarm_forward_cache(rel_cache, db, RELATION, num_procs=1)

    inverse_map = register_inverse_predicates(db)
    inv_cache: dict = {}
    prewarm_inverse_cache(inv_cache, db, RELATION, num_procs=1)
    return attr_cache, rel_cache, inv_cache, inverse_map


def run_sampling(db, person_names, attr_cache, rel_cache, inv_cache, inverse_map, templates, rng):
    """The core sampling loop — everything inside gets profiled."""
    base_templates = [t for t in templates if len(t) == 3]
    successes = 0
    for i in range(NUM_QUESTIONS):
        q_template, query_template, _ = base_templates[i % len(base_templates)]
        result = sample_question_bidirectional(
            q_template, query_template, rng, db, person_names,
            attr_cache, rel_cache, inv_cache, inverse_map,
            num_procs=1,
            easy_mode=False,
            num_sampling_attempts=100,
            anchor_strategy="random",
        )
        if result is not None:
            successes += 1
    return successes


def print_stats(pr, sort_by="cumulative", label=""):
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats(sort_by)
    ps.print_stats(TOP_N)
    print(f"\n{'='*80}")
    print(f"  Profile: {label}  (sorted by {sort_by}, top {TOP_N})")
    print(f"{'='*80}")
    print(s.getvalue())


def profile_cache_warmup(db, person_names):
    """Profile the cache warming phase (the DB-query heavy part)."""
    pr = cProfile.Profile()
    pr.enable()
    t0 = time.perf_counter()
    attr_cache: dict = {}
    rel_cache: dict = {}
    for name in person_names:
        get_vals_and_update_cache(attr_cache, name, db, ATTRIBUTE_TYPES, num_procs=1)
        get_vals_and_update_cache(rel_cache, name, db, RELATION, num_procs=1)
    inverse_map = register_inverse_predicates(db)
    inv_cache: dict = {}
    prewarm_inverse_cache(inv_cache, db, RELATION, num_procs=1)
    elapsed = time.perf_counter() - t0
    pr.disable()
    return pr, elapsed, attr_cache, rel_cache, inv_cache, inverse_map


def main():
    print(f"Building universe (n≈{N_TARGET})...")
    t0 = time.perf_counter()
    db = build_universe(N_TARGET, SEED)
    person_names = db.get_person_names()
    build_time = time.perf_counter() - t0
    print(f"  Universe built: {len(person_names)} people ({build_time:.1f}s)")

    print("Generating templates...")
    templates = generate_templates(depth=DEPTH, question_types=["base"])
    print(f"  {len(templates)} templates")

    # ── Phase 1a: old per-person warmup (for comparison) ────────────────────
    print(f"\nPhase 1a: OLD per-person cache warmup ({len(person_names)} people)...")
    t0 = time.perf_counter()
    attr_cache_old, rel_cache_old, inv_cache_old, inverse_map = warmup_caches_old(db, person_names)
    old_warm_time = time.perf_counter() - t0
    print(f"  OLD warmup took {old_warm_time:.2f}s")

    # ── Phase 1b: new bulk warmup ────────────────────────────────────────────
    print(f"\nPhase 1b: NEW bulk cache warmup...")
    pr_warm = cProfile.Profile()
    pr_warm.enable()
    t0 = time.perf_counter()
    attr_cache, rel_cache, inv_cache, _ = warmup_caches_new(db)
    warm_time = time.perf_counter() - t0
    pr_warm.disable()
    print(f"  NEW warmup took {warm_time:.2f}s  ({old_warm_time/warm_time:.1f}x faster)")

    # Sanity-check: both caches should agree on every person
    for name in person_names:
        assert sorted(attr_cache.get(name, [])) == sorted(attr_cache_old.get(name, [])), \
            f"attr_cache mismatch for {name}"
        assert sorted(rel_cache.get(name, [])) == sorted(rel_cache_old.get(name, [])), \
            f"rel_cache mismatch for {name}"
    print("  Cache contents verified identical to old approach.")

    print_stats(pr_warm, sort_by="cumulative", label="NEW CACHE WARMUP — cumulative time")
    print_stats(pr_warm, sort_by="tottime",    label="NEW CACHE WARMUP — self time (tottime)")

    # ── Phase 2: profile the sampling loop (caches already warm) ────────────
    # Dry run first to avoid any one-time JIT cost
    run_sampling(db, person_names, attr_cache, rel_cache, inv_cache, inverse_map, templates,
                 np.random.default_rng(0))

    print(f"\nPhase 2: profiling {NUM_QUESTIONS} questions (warm caches)...")
    rng = np.random.default_rng(SEED)
    pr_sample = cProfile.Profile()
    pr_sample.enable()
    t0 = time.perf_counter()
    successes = run_sampling(db, person_names, attr_cache, rel_cache, inv_cache, inverse_map, templates, rng)
    sample_time = time.perf_counter() - t0
    pr_sample.disable()

    print(f"  Sampled {successes}/{NUM_QUESTIONS} in {sample_time:.3f}s "
          f"({sample_time/NUM_QUESTIONS*1000:.3f} ms/question)")
    print_stats(pr_sample, sort_by="cumulative", label="SAMPLING LOOP — cumulative time")
    print_stats(pr_sample, sort_by="tottime",    label="SAMPLING LOOP — self time (tottime)")

    # ── Summary ──────────────────────────────────────────────────────────────
    total_old = build_time + old_warm_time + sample_time
    total_new = build_time + warm_time + sample_time
    print("\n" + "="*60)
    print("  TIMING SUMMARY")
    print("="*60)
    print(f"  {'Phase':<35s} {'OLD':>8s}  {'NEW':>8s}")
    print(f"  {'-'*55}")
    print(f"  {'Universe build':<35s} {build_time:>7.2f}s  {build_time:>7.2f}s")
    print(f"  {'Cache warmup':<35s} {old_warm_time:>7.2f}s  {warm_time:>7.2f}s  ({old_warm_time/warm_time:.1f}x faster)")
    print(f"  {'Sampling ' + str(NUM_QUESTIONS) + ' questions':<35s} {sample_time:>7.3f}s  {sample_time:>7.3f}s")
    print(f"  {'Total':<35s} {total_old:>7.2f}s  {total_new:>7.2f}s")

    # Save both profiles
    warm_path   = os.path.join(os.path.dirname(__file__), "bidir_warmup_n1000.prof")
    sample_path = os.path.join(os.path.dirname(__file__), "bidir_sample_n1000.prof")
    pr_warm.dump_stats(warm_path)
    pr_sample.dump_stats(sample_path)
    print(f"\nProfiles saved:")
    print(f"  snakeviz {warm_path}")
    print(f"  snakeviz {sample_path}")


if __name__ == "__main__":
    main()
