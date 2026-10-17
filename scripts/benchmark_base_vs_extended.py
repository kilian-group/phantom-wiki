"""End-to-end timing: bidirectional base-only vs base+extended, n=1000."""

import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from phantom_wiki.facts import get_database
from phantom_wiki.facts.attributes import db_generate_attributes
from phantom_wiki.facts.attributes.constants import ATTRIBUTE_TYPES
from phantom_wiki.facts.bidirectional_sample import sample_question_bidirectional
from phantom_wiki.facts.extended_questions import EXTENDED_QUESTION_TYPES, sample_extended_question
from phantom_wiki.facts.family import db_generate_family
from phantom_wiki.facts.friends import db_generate_friendships
from phantom_wiki.facts.inverse_relations import register_inverse_predicates
from phantom_wiki.facts.sample import RELATION, prewarm_forward_cache, prewarm_inverse_cache
from phantom_wiki.facts.templates import ALL_QUESTION_TYPES, QUESTION_TYPE_BASE, generate_templates
from phantom_wiki.generate_dataset import _get_extended_cfg_answer


N_TARGET     = 1000
N_Q_PER_TYPE = 200   # questions per template type
DEPTH        = 6
SEED         = 42


def build_universe(seed):
    db = get_database()
    num_trees = max(1, N_TARGET // 25)
    db_generate_family(
        db, seed=seed, duplicate_names=False, debug=False,
        output_dir="/tmp/bench_bidir",
        visualize=False, max_family_tree_depth=5, max_branching_factor=5,
        max_family_tree_size=25, stop_prob=0, num_family_trees=num_trees,
    )
    db_generate_friendships(db, friendship_k=3, friendship_seed=seed,
                            visualize=False, output_dir="/tmp/bench_bidir")
    db_generate_attributes(db, seed=seed)
    return db


def prewarm(db):
    attr_cache, rel_cache, inv_cache = {}, {}, {}
    prewarm_forward_cache(attr_cache, db, ATTRIBUTE_TYPES, num_procs=1)
    prewarm_forward_cache(rel_cache,  db, RELATION,        num_procs=1)
    inverse_map = register_inverse_predicates(db)
    prewarm_inverse_cache(inv_cache,  db, RELATION,        num_procs=1)
    return attr_cache, rel_cache, inv_cache, inverse_map


def run_base_sampling(db, person_names, attr_cache, rel_cache, inv_cache, inverse_map,
                      base_templates, seed):
    """Sample N_Q_PER_TYPE questions for each base template."""
    timings = {}
    rng = np.random.default_rng(seed)
    for i, (q_tmpl, qr_tmpl, _) in enumerate(base_templates):
        t0 = time.perf_counter()
        successes = 0
        attempts = 0
        max_attempts = N_Q_PER_TYPE * 100
        while successes < N_Q_PER_TYPE and attempts < max_attempts:
            attempts += 1
            result = sample_question_bidirectional(
                q_tmpl, qr_tmpl, rng, db, person_names,
                attr_cache, rel_cache, inv_cache, inverse_map,
                num_procs=1, easy_mode=False, num_sampling_attempts=1,
                anchor_strategy="random",
            )
            if result is not None:
                successes += 1
        timings[f"base_type{i}"] = (time.perf_counter() - t0, successes)
    return timings


def run_extended_cfg_sampling(db, person_names, attr_cache, rel_cache, inv_cache, inverse_map,
                               base_templates, extended_cfg_templates, seed):
    """Sample base templates + extended CFG templates (comparison/superlative/mc)."""
    timings = run_base_sampling(db, person_names, attr_cache, rel_cache, inv_cache,
                                inverse_map, base_templates, seed)

    rng = np.random.default_rng(seed)
    from phantom_wiki.facts.sample import sample_question
    for i, tmpl in enumerate(extended_cfg_templates):
        q_tmpl, qr_tmpl, answer_info, question_subtype = tmpl
        t0 = time.perf_counter()
        successes, answer_time = 0, 0.0
        attempts = 0
        max_attempts = N_Q_PER_TYPE * 100
        while successes < N_Q_PER_TYPE and attempts < max_attempts:
            attempts += 1
            try:
                result = sample_question(
                    q_tmpl, qr_tmpl, rng, db, person_names,
                    attr_cache, rel_cache, num_procs=1,
                    easy_mode=False, num_sampling_attempts=1,
                    return_bindings=True,
                )
            except Exception:
                continue
            if result is None:
                continue
            question, query, bindings = result
            ta = time.perf_counter()
            _get_extended_cfg_answer(
                question, query, answer_info, question_subtype, db,
                bindings=bindings, attr_cache=attr_cache,
            )
            answer_time += time.perf_counter() - ta
            successes += 1
        elapsed = time.perf_counter() - t0
        # use index so same-subtype templates at different hop depths don't overwrite
        timings[f"ext_cfg_{i:03d}_{question_subtype}"] = (elapsed, successes, answer_time)

    return timings


def run_legacy_extended(db, person_names, attr_cache, rel_cache, seed):
    """Legacy extended question types (standalone 1-hop)."""
    timings = {}
    rng = np.random.default_rng(seed)
    for qtype in EXTENDED_QUESTION_TYPES:
        t0 = time.perf_counter()
        successes = 0
        attempts = 0
        max_attempts = N_Q_PER_TYPE * 100
        while successes < N_Q_PER_TYPE and attempts < max_attempts:
            attempts += 1
            result = sample_extended_question(
                qtype, rng, db, person_names, attr_cache, rel_cache, num_procs=1,
            )
            if result is not None:
                successes += 1
        timings[f"legacy_{qtype}"] = (time.perf_counter() - t0, successes)
    return timings


def fmt(t):
    return f"{t:6.2f}s"


def main():
    print(f"Building universe n≈{N_TARGET}, {N_Q_PER_TYPE} q/type, depth={DEPTH}...")
    t0 = time.perf_counter()
    db = build_universe(SEED)
    person_names = db.get_person_names()
    build_time = time.perf_counter() - t0
    print(f"  {len(person_names)} people ({build_time:.2f}s)")

    print("Prewarming caches (bidirectional)...")
    t0 = time.perf_counter()
    attr_cache, rel_cache, inv_cache, inverse_map = prewarm(db)
    warm_time = time.perf_counter() - t0
    print(f"  done ({warm_time:.2f}s)")

    all_templates = generate_templates(depth=DEPTH, question_types=ALL_QUESTION_TYPES)
    base_templates      = [t for t in all_templates if len(t) == 3]
    extended_cfg_templates = [t for t in all_templates if len(t) == 4]
    print(f"  {len(base_templates)} base templates, {len(extended_cfg_templates)} extended-CFG templates")

    # ── Scenario A: base only (old behaviour) ───────────────────────────────
    print(f"\n{'='*65}")
    print(f"  SCENARIO A: bidirectional + BASE templates only  (old)")
    print(f"{'='*65}")
    tA0 = time.perf_counter()
    timA = run_base_sampling(db, person_names, attr_cache, rel_cache, inv_cache,
                             inverse_map, base_templates, SEED)
    tA_sample = time.perf_counter() - tA0
    tA_total  = build_time + warm_time + tA_sample

    for key, val in timA.items():
        elapsed, successes = val
        print(f"  {key:<30s}  {fmt(elapsed)}  ({successes}/{N_Q_PER_TYPE} sampled)")
    print(f"  {'─'*52}")
    print(f"  {'sampling subtotal':<30s}  {fmt(tA_sample)}")
    print(f"  {'universe build':<30s}  {fmt(build_time)}")
    print(f"  {'cache prewarm':<30s}  {fmt(warm_time)}")
    print(f"  {'TOTAL':<30s}  {fmt(tA_total)}")

    # ── Scenario B: base + all extended (current) ───────────────────────────
    print(f"\n{'='*65}")
    print(f"  SCENARIO B: bidirectional + ALL templates  (current)")
    print(f"{'='*65}")
    tB0 = time.perf_counter()
    timB = run_extended_cfg_sampling(db, person_names, attr_cache, rel_cache, inv_cache,
                                      inverse_map, base_templates, extended_cfg_templates, SEED)
    tB_base_sample = sum(v[0] for k, v in timB.items() if k.startswith("base_"))
    tB_ext_sample  = sum(v[0] for k, v in timB.items() if k.startswith("ext_cfg_"))
    tB_answer_time = sum(v[2] for k, v in timB.items() if k.startswith("ext_cfg_"))
    tB_sample      = time.perf_counter() - tB0
    tB_total       = build_time + warm_time + tB_sample

    print("  Base templates:")
    for key, val in timB.items():
        if key.startswith("base_"):
            elapsed, successes = val
            print(f"    {key:<30s}  {fmt(elapsed)}  ({successes}/{N_Q_PER_TYPE})")

    print("  Extended CFG templates (grouped by subtype):")
    from collections import defaultdict
    subtype_agg = defaultdict(lambda: [0.0, 0, 0.0, 0])  # time, successes, ans_time, count
    for key, val in timB.items():
        if key.startswith("ext_cfg_"):
            elapsed, successes, ans_t = val
            # key format: ext_cfg_NNN_subtype
            subtype = "_".join(key.split("_")[3:])
            subtype_agg[subtype][0] += elapsed
            subtype_agg[subtype][1] += successes
            subtype_agg[subtype][2] += ans_t
            subtype_agg[subtype][3] += 1
    for subtype, (t, s, at, cnt) in sorted(subtype_agg.items(), key=lambda x: -x[1][0]):
        print(f"    {subtype:<30s}  {fmt(t)}  ({s}/{N_Q_PER_TYPE*cnt} across {cnt} tmpls)"
              f"  [answer lookup: {at:.2f}s]")

    print(f"  {'─'*60}")
    print(f"  {'base sampling subtotal':<35s}  {fmt(tB_base_sample)}")
    print(f"  {'extended-CFG sampling subtotal':<35s}  {fmt(tB_ext_sample)}")
    print(f"    of which answer lookup (Prolog)':<35s  {fmt(tB_answer_time)}")
    print(f"  {'universe build':<35s}  {fmt(build_time)}")
    print(f"  {'cache prewarm':<35s}  {fmt(warm_time)}")
    print(f"  {'TOTAL':<35s}  {fmt(tB_total)}")

    # ── Legacy extended ──────────────────────────────────────────────────────
    print(f"\n{'='*65}")
    print(f"  Legacy extended question types (both scenarios share this)")
    print(f"{'='*65}")
    tL0 = time.perf_counter()
    timL = run_legacy_extended(db, person_names, attr_cache, rel_cache, SEED)
    tL_total = time.perf_counter() - tL0
    for key, val in timL.items():
        elapsed, successes = val
        print(f"  {key:<40s}  {fmt(elapsed)}  ({successes}/{N_Q_PER_TYPE})")
    print(f"  {'─'*55}")
    print(f"  {'legacy extended subtotal':<40s}  {fmt(tL_total)}")

    # ── Side-by-side summary ─────────────────────────────────────────────────
    print(f"\n{'='*65}")
    print(f"  SUMMARY  (n={len(person_names)}, {N_Q_PER_TYPE} q/type)")
    print(f"{'='*65}")
    print(f"  {'Phase':<38s}  {'base-only':>9s}  {'all-types':>9s}")
    print(f"  {'─'*62}")
    print(f"  {'Universe build':<38s}  {fmt(build_time)}  {fmt(build_time)}")
    print(f"  {'Cache prewarm (bidir)':<38s}  {fmt(warm_time)}  {fmt(warm_time)}")
    print(f"  {'Base template sampling':<38s}  {fmt(tA_sample)}  {fmt(tB_base_sample)}")
    print(f"  {'Extended-CFG sampling':<38s}  {'n/a':>9s}  {fmt(tB_ext_sample)}")
    print(f"    of which Prolog answer lookups:<38s  {'n/a':>9s}  {fmt(tB_answer_time)}")
    print(f"  {'Legacy extended sampling':<38s}  {fmt(tL_total)}  {fmt(tL_total)}")
    print(f"  {'─'*62}")
    total_A = tA_total + tL_total
    total_B = tB_total + tL_total
    print(f"  {'TOTAL':<38s}  {fmt(total_A)}  {fmt(total_B)}")
    print(f"  Extended overhead: +{total_B - total_A:.2f}s  ({(total_B/total_A - 1)*100:.0f}% slower)")


if __name__ == "__main__":
    main()
