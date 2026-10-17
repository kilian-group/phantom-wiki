#!/usr/bin/env python3
"""Generate mc2 questions for missing (hops, constraints) cells and regenerate the grid viz."""

import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import copy
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from textwrap import fill

from phantom_wiki.facts.database import Database
from phantom_wiki.facts.templates import (
    generate_templates, ALL_QUESTION_TYPES, QUESTION_TYPE_BASE,
    classify_question_type, is_aggregation_question,
)
from phantom_wiki.facts.sample import (
    RELATION, RELATION_EASY, prewarm_inverse_cache, sample_question,
)
from phantom_wiki.facts.inverse_relations import register_inverse_predicates
from phantom_wiki.facts.bidirectional_sample import sample_question_bidirectional
from phantom_wiki.facts.difficulty import compute_difficulty
from phantom_wiki.generate_dataset import _get_extended_cfg_answer
from phantom_wiki.utils import generate_unique_id

# ── Config ──────────────────────────────────────────────────────────────────
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'out_1000_easy')
QUESTIONS_DIR = os.path.join(OUTPUT_DIR, 'questions')
FACTS_PATH = os.path.join(OUTPUT_DIR, 'facts.pl')
VIZ_PATH = os.path.join(os.path.dirname(__file__), '..', 'grid_hops_constraints_easy.png')

SEED = 1
EASY_MODE = True
NUM_PER_TYPE = 10
NUM_ATTEMPTS = 500


def load_existing_questions():
    """Read all existing type JSON files and return dict of (hops, constraints) -> list[question]."""
    all_qs = {}
    for fname in os.listdir(QUESTIONS_DIR):
        if not (fname.startswith('type') and fname.endswith('.json')):
            continue
        path = os.path.join(QUESTIONS_DIR, fname)
        qs = json.load(open(path))
        for q in qs:
            diff = q.get('difficulty', {})
            if not isinstance(diff, dict):
                continue
            key = (diff.get('hops', 0), diff.get('constraints', 0))
            all_qs.setdefault(key, []).append(q)
    return all_qs


def get_max_type_id():
    max_id = -1
    for fname in os.listdir(QUESTIONS_DIR):
        if fname.startswith('type') and fname.endswith('.json'):
            max_id = max(max_id, int(fname[4:-5]))
    return max_id


def generate_mc2_questions(db, person_name_bank, inverse_map,
                           p2attr, p2rel, p2inv):
    """Generate questions for the extended CFG (mc2) templates."""
    templates = generate_templates(depth=6, question_types=ALL_QUESTION_TYPES)
    base_templates = [t for t in templates if len(t) == 3]
    extended_cfg_templates = [t for t in templates if len(t) == 4]

    # Only process mc2 / superlative_mc2 subtypes
    mc2_subtypes = {
        'comparison_age_mc2', 'comparison_age_younger_mc2', 'comparison_born_first_mc2',
        'superlative_oldest_mc2', 'superlative_youngest_mc2',
    }

    max_id = get_max_type_id()
    new_type_offset = max_id + 1  # start new IDs after existing max

    all_new_questions = []

    for tmpl_idx, tmpl in enumerate(extended_cfg_templates):
        question_template, query_template, answer_info, question_subtype = tmpl
        if question_subtype not in mc2_subtypes:
            continue

        rng = np.random.default_rng(SEED)
        questions = []
        queries = []
        attempts = 0
        max_attempts = NUM_PER_TYPE * NUM_ATTEMPTS

        while len(questions) < NUM_PER_TYPE and attempts < max_attempts:
            attempts += 1
            try:
                result = sample_question(
                    question_template,
                    query_template,
                    rng,
                    db,
                    person_name_bank,
                    p2attr,
                    p2rel,
                    1,
                    easy_mode=EASY_MODE,
                    num_sampling_attempts=10,
                )
                if result is not None:
                    question, query = result
                    questions.append(question)
                    queries.append(query)
            except Exception:
                continue

        type_id = len(base_templates) + tmpl_idx
        print(f"  subtype={question_subtype}, type_id={type_id}: "
              f"{len(questions)}/{NUM_PER_TYPE} questions (attempts={attempts})")

        if not questions:
            continue

        type_qs = []
        for j, (q_text, q_query) in enumerate(zip(questions, queries)):
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

        out_path = os.path.join(QUESTIONS_DIR, f'type{type_id}.json')
        with open(out_path, 'w') as f:
            json.dump(type_qs, f, indent=4)
        print(f"    Saved {len(type_qs)} questions to {out_path}")
        all_new_questions.extend(type_qs)

    return all_new_questions


def make_grid_visualization(all_qs):
    """Render the (hops x constraints) grid visualization."""
    max_hops = 4
    max_constraints = 2
    rows = max_hops + 1  # 0..4
    cols = max_constraints + 1  # 0..2

    fig_w = 14
    fig_h = 14
    fig, axes = plt.subplots(rows, cols, figsize=(fig_w, fig_h))

    fig.suptitle('Question examples by (hops × constraints) — out_1000_easy',
                 fontsize=16, fontweight='normal', y=0.98)

    col_labels = ['0 constraints', '1 constraint', '2 constraints']
    row_labels = ['0 hops', '1 hop', '2 hops', '3 hops', '4 hops']

    FONT_QUESTION = 10
    FONT_META = 8
    EMPTY_COLOR = '#f0f0f0'

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
                ax.set_facecolor(EMPTY_COLOR)
                ax.text(0.5, 0.5, '(no example)',
                        ha='center', va='center',
                        fontsize=FONT_META, color='#aaaaaa',
                        fontstyle='italic',
                        transform=ax.transAxes)
            else:
                q = qs[0]
                ax.set_facecolor('white')
                q_text = q['question']
                wrapped = fill(q_text, width=38)

                ax.text(0.5, 0.58, wrapped,
                        ha='center', va='center',
                        fontsize=FONT_QUESTION, color='#222222',
                        transform=ax.transAxes,
                        multialignment='center')

                n_ans = len(q['answer']) if isinstance(q['answer'], list) else 1
                meta = f"answers: {n_ans}   type: {q['type']}"
                ax.text(0.5, 0.12, meta,
                        ha='center', va='center',
                        fontsize=FONT_META, color='#888888',
                        transform=ax.transAxes)

            if row == 0:
                ax.set_title(col_labels[col], fontsize=11, pad=8, fontweight='normal')

            if col == 0:
                ax.set_ylabel(row_labels[row], fontsize=11, rotation=90,
                              labelpad=6, va='center')

    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plt.savefig(VIZ_PATH, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"\nVisualization saved to {VIZ_PATH}")


def main():
    # ── Step 1: load existing questions ─────────────────────────────────────
    print("Loading existing questions...")
    all_qs = load_existing_questions()
    print("Existing (hops, constraints) coverage:")
    for k in sorted(all_qs):
        print(f"  hops={k[0]}, constraints={k[1]}: {len(all_qs[k])} questions")

    missing = [(h, c) for h in range(5) for c in range(3)
               if (h, c) not in all_qs]
    print(f"\nMissing cells: {missing}")

    if not missing:
        print("All cells already have examples — regenerating visualization only.")
        make_grid_visualization(all_qs)
        return

    # ── Step 2: load Prolog database ─────────────────────────────────────────
    print(f"\nLoading database from {FACTS_PATH} ...")
    db = Database.from_disk(FACTS_PATH)
    person_name_bank = db.get_person_names()
    print(f"  {len(person_name_bank)} people in database")

    # ── Step 3: set up sampling caches ───────────────────────────────────────
    p2attr: dict = {}
    p2rel: dict = {}
    p2inv: dict = {}
    print("Registering inverse predicates...")
    inverse_map = register_inverse_predicates(db)
    print("Prewarming inverse cache...")
    prewarm_inverse_cache(p2inv, db, RELATION, 1)

    # ── Step 4: generate mc2 questions ───────────────────────────────────────
    print("\nGenerating mc2 template questions...")
    new_qs = generate_mc2_questions(db, person_name_bank, inverse_map,
                                    p2attr, p2rel, p2inv)

    # Merge new questions into all_qs
    for q in new_qs:
        diff = q.get('difficulty', {})
        if not isinstance(diff, dict):
            continue
        key = (diff.get('hops', 0), diff.get('constraints', 0))
        all_qs.setdefault(key, []).append(q)

    print("\nUpdated (hops, constraints) coverage:")
    for k in sorted(all_qs):
        print(f"  hops={k[0]}, constraints={k[1]}: {len(all_qs[k])} questions")

    still_missing = [(h, c) for h in range(5) for c in range(3)
                     if (h, c) not in all_qs]
    if still_missing:
        print(f"\nCells still missing (will show '(no example)'): {still_missing}")

    # ── Step 5: regenerate visualization ─────────────────────────────────────
    print("\nGenerating visualization...")
    make_grid_visualization(all_qs)


if __name__ == '__main__':
    main()
