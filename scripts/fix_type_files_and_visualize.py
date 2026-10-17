#!/usr/bin/env python3
"""Restore overwritten type files and save mc2 questions at non-conflicting IDs,
then regenerate the grid visualization.

In the OLD code (pre-mc2), template IDs were:
  0-7   base
  8-87  comparison (80 templates)
  88    multi_constraint_2
  89    multi_constraint_3
  90+   superlative (various)

In the NEW code (with mc2), template IDs are:
  0-7   base (same)
  8-87  comparison (same)
  88-99 comparison_mc2  ← new, inserted here
  100   multi_constraint_2  (was 88)
  101   multi_constraint_3  (was 89)
  102+  superlative         (was 90+)
  118-119 superlative_mc2  ← new

Running the old generate_mc2_and_visualize.py overwrote type88-91,94-95,98-99
with mc2 questions. This script:
  1. Regenerates the original content for those 8 files using the corresponding
     NEW template IDs (100/101/102/103/106/107/110/111) as the template source.
  2. Saves mc2 questions to NEW IDs starting at 120 (after all existing types).
  3. Regenerates the grid visualization.
"""

import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from textwrap import fill

from phantom_wiki.facts.database import Database
from phantom_wiki.facts.templates import generate_templates, ALL_QUESTION_TYPES
from phantom_wiki.facts.sample import sample_question, RELATION, prewarm_inverse_cache
from phantom_wiki.facts.inverse_relations import register_inverse_predicates
from phantom_wiki.facts.difficulty import compute_difficulty
from phantom_wiki.generate_dataset import _get_extended_cfg_answer
from phantom_wiki.utils import generate_unique_id

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'out_1000_easy')
QUESTIONS_DIR = os.path.join(OUTPUT_DIR, 'questions')
FACTS_PATH = os.path.join(OUTPUT_DIR, 'facts.pl')
VIZ_PATH = os.path.join(os.path.dirname(__file__), '..', 'grid_hops_constraints_easy.png')

SEED = 1
EASY_MODE = True
NUM_PER_TYPE = 10
NUM_ATTEMPTS = 500

# Mapping: old_type_id → new_template_idx in current extended_cfg_templates list
# (verified by checking (hops, constraints) match)
OLD_TO_NEW_TMPL_IDX = {
    88: 100 - 8,  # multi_constraint_2 = extended_cfg idx 92
    89: 101 - 8,  # multi_constraint_3 = extended_cfg idx 93
    90: 102 - 8,  # superlative_oldest (2-hop attr)
    91: 103 - 8,  # superlative_youngest (2-hop attr)
    94: 106 - 8,  # superlative_oldest (2-hop name)
    95: 107 - 8,  # superlative_youngest (2-hop name)
    98: 110 - 8,  # superlative_oldest (1-hop attr)
    99: 111 - 8,  # superlative_youngest (1-hop attr)
}

MC2_SUBTYPES = {
    'comparison_age_mc2', 'comparison_age_younger_mc2', 'comparison_born_first_mc2',
    'superlative_oldest_mc2', 'superlative_youngest_mc2',
}


def get_templates():
    templates = generate_templates(depth=6, question_types=ALL_QUESTION_TYPES)
    base_templates = [t for t in templates if len(t) == 3]
    extended_cfg_templates = [t for t in templates if len(t) == 4]
    return base_templates, extended_cfg_templates


def generate_type_questions(tmpl, type_id, db, person_name_bank, p2attr, p2rel, seed=SEED):
    """Generate NUM_PER_TYPE questions for one extended CFG template."""
    question_template, query_template, answer_info, question_subtype = tmpl
    rng = np.random.default_rng(seed)
    questions, queries = [], []
    attempts = 0
    max_attempts = NUM_PER_TYPE * NUM_ATTEMPTS

    while len(questions) < NUM_PER_TYPE and attempts < max_attempts:
        attempts += 1
        try:
            result = sample_question(
                question_template, query_template, rng, db, person_name_bank,
                p2attr, p2rel, 1,
                easy_mode=EASY_MODE, num_sampling_attempts=10,
            )
            if result is not None:
                q, qr = result
                questions.append(q)
                queries.append(qr)
        except Exception:
            continue

    type_qs = []
    for q_text, q_query in zip(questions, queries):
        answer_list = _get_extended_cfg_answer(q_text, q_query, answer_info, question_subtype, db)
        type_qs.append({
            'id': generate_unique_id(),
            'question': q_text,
            'solution_traces': json.dumps([]),
            'answer': answer_list,
            'prolog': {'query': q_query, 'answer': str(answer_info)},
            'template': question_template,
            'type': type_id,
            'difficulty': compute_difficulty(q_query),
            'is_aggregation_question': False,
            'question_category': question_subtype,
        })

    return type_qs, attempts


def load_all_questions():
    """Return dict: (hops, constraints) → list of question dicts."""
    all_qs: dict[tuple, list] = {}
    for fname in os.listdir(QUESTIONS_DIR):
        if not (fname.startswith('type') and fname.endswith('.json')):
            continue
        qs = json.load(open(os.path.join(QUESTIONS_DIR, fname)))
        for q in qs:
            diff = q.get('difficulty', {})
            if not isinstance(diff, dict):
                continue
            key = (diff.get('hops', 0), diff.get('constraints', 0))
            all_qs.setdefault(key, []).append(q)
    return all_qs


def make_visualization(all_qs):
    max_hops = 4
    max_constraints = 2
    rows = max_hops + 1
    cols = max_constraints + 1

    fig, axes = plt.subplots(rows, cols, figsize=(14, 14))
    fig.suptitle('Question examples by (hops × constraints) — out_1000_easy',
                 fontsize=16, fontweight='normal', y=0.98)

    col_labels = ['0 constraints', '1 constraint', '2 constraints']
    row_labels = ['0 hops', '1 hop', '2 hops', '3 hops', '4 hops']

    for row in range(rows):
        for col in range(cols):
            ax = axes[row][col]
            key = (row, col)
            qs = all_qs.get(key, [])

            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.set_xticks([])
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_linewidth(0.8)
                spine.set_edgecolor('#aaaaaa')

            if not qs:
                ax.set_facecolor('#f0f0f0')
                ax.text(0.5, 0.5, '(no example)', ha='center', va='center',
                        fontsize=8, color='#aaaaaa', fontstyle='italic',
                        transform=ax.transAxes)
            else:
                q = qs[0]
                ax.set_facecolor('white')
                wrapped = fill(q['question'], width=38)
                ax.text(0.5, 0.58, wrapped, ha='center', va='center',
                        fontsize=10, color='#222222', transform=ax.transAxes,
                        multialignment='center')
                n_ans = len(q['answer']) if isinstance(q['answer'], list) else 1
                ax.text(0.5, 0.12, f"answers: {n_ans}   type: {q['type']}",
                        ha='center', va='center', fontsize=8, color='#888888',
                        transform=ax.transAxes)

            if row == 0:
                ax.set_title(col_labels[col], fontsize=11, pad=8, fontweight='normal')
            if col == 0:
                ax.set_ylabel(row_labels[row], fontsize=11, rotation=90, labelpad=6, va='center')

    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plt.savefig(VIZ_PATH, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"\nVisualization saved: {VIZ_PATH}")


def main():
    print("Loading database...")
    db = Database.from_disk(FACTS_PATH)
    person_name_bank = db.get_person_names()
    print(f"  {len(person_name_bank)} people")

    p2attr: dict = {}
    p2rel: dict = {}

    base_templates, extended_cfg_templates = get_templates()
    n_base = len(base_templates)
    print(f"Templates: {n_base} base, {len(extended_cfg_templates)} extended")

    # ── Step 1: Restore the 8 overwritten type files ─────────────────────────
    print("\nRestoring overwritten type files...")
    for old_id, new_tmpl_idx in sorted(OLD_TO_NEW_TMPL_IDX.items()):
        tmpl = extended_cfg_templates[new_tmpl_idx]
        _, _, _, subtype = tmpl
        print(f"  Regenerating type{old_id} (subtype={subtype})...")
        type_qs, attempts = generate_type_questions(
            tmpl, old_id, db, person_name_bank, p2attr, p2rel
        )
        # Fix the type field to old_id
        for q in type_qs:
            q['type'] = old_id
        out_path = os.path.join(QUESTIONS_DIR, f'type{old_id}.json')
        with open(out_path, 'w') as f:
            json.dump(type_qs, f, indent=4)
        diff_counts: dict = {}
        for q in type_qs:
            d = q['difficulty']
            k = (d['hops'], d['constraints'])
            diff_counts[k] = diff_counts.get(k, 0) + 1
        print(f"    → {len(type_qs)} questions, dist={diff_counts} (attempts={attempts})")

    # ── Step 2: Save mc2 questions at NEW IDs (120+) ─────────────────────────
    # Remove the conflicting mc2 files written earlier (88-99, 118, 119)
    to_remove = [88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 118, 119]
    print(f"\nRemoving stale mc2 files at conflicting IDs: {to_remove}")
    for tid in to_remove:
        p = os.path.join(QUESTIONS_DIR, f'type{tid}.json')
        if os.path.exists(p):
            # Only remove if the file was an mc2 file (check subtype)
            qs = json.load(open(p))
            if qs and qs[0].get('question_category', '') in MC2_SUBTYPES:
                os.remove(p)
                print(f"  Removed type{tid}.json (was mc2)")

    # Find max existing type id after restoration
    existing_ids = set()
    for fname in os.listdir(QUESTIONS_DIR):
        if fname.startswith('type') and fname.endswith('.json'):
            existing_ids.add(int(fname[4:-5]))
    next_id = max(existing_ids) + 1
    print(f"\nSaving mc2 questions starting at type{next_id}...")

    mc2_type_id = next_id
    for tmpl_idx, tmpl in enumerate(extended_cfg_templates):
        _, _, _, subtype = tmpl
        if subtype not in MC2_SUBTYPES:
            continue
        print(f"  Generating type{mc2_type_id} ({subtype})...")
        type_qs, attempts = generate_type_questions(
            tmpl, mc2_type_id, db, person_name_bank, p2attr, p2rel
        )
        if not type_qs:
            print(f"    → 0 questions, skipping")
            continue
        out_path = os.path.join(QUESTIONS_DIR, f'type{mc2_type_id}.json')
        with open(out_path, 'w') as f:
            json.dump(type_qs, f, indent=4)
        diff_counts: dict = {}
        for q in type_qs:
            d = q['difficulty']
            k = (d['hops'], d['constraints'])
            diff_counts[k] = diff_counts.get(k, 0) + 1
        print(f"    → {len(type_qs)} questions, dist={diff_counts}")
        mc2_type_id += 1

    # ── Step 3: Show final coverage and make visualization ───────────────────
    print("\nFinal (hops, constraints) coverage:")
    all_qs = load_all_questions()
    for k in sorted(all_qs):
        print(f"  hops={k[0]}, constraints={k[1]}: {len(all_qs[k])} questions")

    still_missing = [(h, c) for h in range(5) for c in range(3) if (h, c) not in all_qs]
    if still_missing:
        print(f"Still missing (will show 'no example'): {still_missing}")

    print("\nGenerating visualization...")
    make_visualization(all_qs)


if __name__ == '__main__':
    main()
