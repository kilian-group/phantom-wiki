#!/usr/bin/env python3
"""Test that the new deep mc2/superlative templates fill the 3 previously-empty cells."""

import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
from collections import Counter

from phantom_wiki.facts.database import Database
from phantom_wiki.facts.templates import generate_templates, ALL_QUESTION_TYPES
from phantom_wiki.facts.sample import sample_question

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'out_1000_easy')
FACTS_PATH = os.path.join(OUTPUT_DIR, 'facts.pl')

SEED = 1
EASY_MODE = True
NUM_PER_TEMPLATE = 10
NUM_ATTEMPTS = 500


def main():
    from phantom_wiki.facts.difficulty import compute_difficulty

    print("Loading database...")
    db = Database.from_disk(FACTS_PATH)
    person_name_bank = db.get_person_names()
    print(f"  {len(person_name_bank)} people")

    p2attr: dict = {}
    p2rel: dict = {}

    templates = generate_templates(depth=6, question_types=ALL_QUESTION_TYPES)
    ext = [t for t in templates if len(t) == 4]
    print(f"Extended CFG templates: {len(ext)}")

    # Identify templates that use the new deep fragments (subscripts 200+ or 300+)
    deep_mc2_indices = []
    deep_sup_indices = []
    deep_sup_mc2_indices = []
    for i, (q_tpl, query_tpl, ai, subtype) in enumerate(ext):
        q_str = ' '.join(q_tpl)
        has_deep_rc = any(f'_{n}' in q_str for n in [200, 201, 202, 220, 221, 222, 240, 241, 242, 243, 260, 261, 262, 263])
        has_deep_sup = any(f'_{n}' in q_str for n in [320, 321, 322, 330, 331, 332, 333])
        if '_mc2' in subtype:
            if has_deep_rc or has_deep_sup:
                if subtype.startswith('superlative_'):
                    deep_sup_mc2_indices.append(i)
                else:
                    deep_mc2_indices.append(i)
        elif subtype.startswith('superlative_') and has_deep_rc:
            deep_sup_indices.append(i)

    print(f"Deep comparison_mc2 templates: {len(deep_mc2_indices)}")
    print(f"Deep superlative (non-mc2) templates: {len(deep_sup_indices)}")
    print(f"Deep superlative_mc2 templates: {len(deep_sup_mc2_indices)}")

    # Sample questions from each deep template and tally (hops, constraints)
    combos = Counter()
    target_cells = {(3, 2), (4, 1), (4, 2)}
    cell_examples: dict = {c: [] for c in target_cells}

    all_deep = [(i, 'deep_cmp_mc2') for i in deep_mc2_indices] + \
               [(i, 'deep_sup') for i in deep_sup_indices] + \
               [(i, 'deep_sup_mc2') for i in deep_sup_mc2_indices]

    for idx, kind in all_deep:
        q_tpl, query_tpl, ai, subtype = ext[idx]
        rng = np.random.default_rng(SEED)
        attempts = 0
        max_att = NUM_PER_TEMPLATE * NUM_ATTEMPTS
        generated = 0
        while generated < NUM_PER_TEMPLATE and attempts < max_att:
            attempts += 1
            try:
                result = sample_question(
                    q_tpl, query_tpl, rng, db, person_name_bank,
                    p2attr, p2rel, 1,
                    easy_mode=EASY_MODE, num_sampling_attempts=10,
                )
                if result is None:
                    continue
                q_text, q_query = result
                diff = compute_difficulty(q_query)
                key = (diff['hops'], diff['constraints'])
                combos[key] += 1
                if key in target_cells and len(cell_examples[key]) < 2:
                    cell_examples[key].append((q_text, subtype, idx))
                generated += 1
            except Exception:
                continue

    print(f"\n(hops, constraints) distribution from deep templates:")
    for k in sorted(combos):
        marker = '  ← TARGET!' if k in target_cells else ''
        print(f"  {k}: {combos[k]} questions{marker}")

    print("\nExamples for target cells:")
    for cell in sorted(target_cells):
        print(f"\n  Cell {cell}:")
        if not cell_examples[cell]:
            print("    ✗ still no example")
        for q_text, subtype, idx in cell_examples[cell]:
            print(f"    ✓ [{subtype}, ext_idx={idx}] {q_text[:120]}")


if __name__ == '__main__':
    main()
