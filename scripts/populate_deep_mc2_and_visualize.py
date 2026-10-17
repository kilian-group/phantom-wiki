#!/usr/bin/env python3
"""Generate questions from the NEW deep mc2 / deep superlative templates and
regenerate the grid_hops_constraints_easy visualization.

The existing out_1000_easy/questions already has type files up through type125.
This script appends new type files for the deep-chain templates added in
templates.py (deep comparison_mc2, deep superlative, deep superlative_mc2), so
the three previously-empty cells (3,2), (4,1), (4,2) get examples.
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
from phantom_wiki.facts.sample import sample_question
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

# Placeholder subscripts introduced by the new deep builders
DEEP_RC_SUBSCRIPTS = {200, 201, 202, 203, 220, 221, 222, 223,
                      240, 241, 242, 243, 260, 261, 262, 263}
DEEP_SUP_MC2_SUBSCRIPTS = {320, 321, 322, 330, 331, 332, 333}


def is_deep_template(q_tpl: list, subtype: str) -> bool:
    q_str = ' '.join(q_tpl)
    if '_mc2' in subtype:
        # Deep comparison_mc2 uses DEEP_RC_SUBSCRIPTS; deep superlative_mc2 uses DEEP_SUP_MC2
        return any(f'_{n}' in q_str for n in DEEP_RC_SUBSCRIPTS | DEEP_SUP_MC2_SUBSCRIPTS)
    if subtype.startswith('superlative_'):
        # Deep non-mc2 superlative uses DEEP_RC_SUBSCRIPTS in its R_c
        return any(f'_{n}' in q_str for n in DEEP_RC_SUBSCRIPTS)
    return False


def generate_for_template(tmpl, type_id, db, person_name_bank, p2attr, p2rel):
    q_tpl, query_tpl, answer_info, subtype = tmpl
    rng = np.random.default_rng(SEED)
    questions, queries = [], []
    attempts = 0
    max_att = NUM_PER_TYPE * NUM_ATTEMPTS
    while len(questions) < NUM_PER_TYPE and attempts < max_att:
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
            questions.append(q_text)
            queries.append(q_query)
        except Exception:
            continue

    out = []
    for q_text, q_query in zip(questions, queries):
        ans = _get_extended_cfg_answer(q_text, q_query, answer_info, subtype, db)
        out.append({
            'id': generate_unique_id(),
            'question': q_text,
            'solution_traces': json.dumps([]),
            'answer': ans,
            'prolog': {'query': q_query, 'answer': str(answer_info)},
            'template': q_tpl,
            'type': type_id,
            'difficulty': compute_difficulty(q_query),
            'is_aggregation_question': False,
            'question_category': subtype,
        })
    return out, attempts


def load_all_questions():
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
                 fontsize=16, y=0.98)

    col_labels = ['0 constraints', '1 constraint', '2 constraints']
    row_labels = ['0 hops', '1 hop', '2 hops', '3 hops', '4 hops']

    for row in range(rows):
        for col in range(cols):
            ax = axes[row][col]
            qs = all_qs.get((row, col), [])
            ax.set_xlim(0, 1); ax.set_ylim(0, 1)
            ax.set_xticks([]); ax.set_yticks([])
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
                ax.set_title(col_labels[col], fontsize=11, pad=8)
            if col == 0:
                ax.set_ylabel(row_labels[row], fontsize=11, rotation=90,
                              labelpad=6, va='center')

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

    templates = generate_templates(depth=6, question_types=ALL_QUESTION_TYPES)
    ext = [t for t in templates if len(t) == 4]

    deep_indices = [i for i, t in enumerate(ext) if is_deep_template(t[0], t[3])]
    print(f"Found {len(deep_indices)} deep templates to generate")

    # Determine next type id
    existing_ids = set()
    for fname in os.listdir(QUESTIONS_DIR):
        if fname.startswith('type') and fname.endswith('.json'):
            existing_ids.add(int(fname[4:-5]))
    next_id = max(existing_ids) + 1
    print(f"Next type id: {next_id}")

    for ext_idx in deep_indices:
        tmpl = ext[ext_idx]
        subtype = tmpl[3]
        type_qs, attempts = generate_for_template(
            tmpl, next_id, db, person_name_bank, p2attr, p2rel
        )
        if not type_qs:
            print(f"  ext[{ext_idx}] {subtype}: 0 questions (attempts={attempts}) — skip")
            continue
        out_path = os.path.join(QUESTIONS_DIR, f'type{next_id}.json')
        with open(out_path, 'w') as f:
            json.dump(type_qs, f, indent=4)
        # Quick dist summary
        dist: dict = {}
        for q in type_qs:
            d = q['difficulty']
            dist[(d['hops'], d['constraints'])] = dist.get((d['hops'], d['constraints']), 0) + 1
        print(f"  type{next_id} ({subtype}, ext[{ext_idx}]): {len(type_qs)} questions, dist={dist}")
        next_id += 1

    # Final coverage
    print("\nFinal (hops, constraints) coverage:")
    all_qs = load_all_questions()
    for k in sorted(all_qs):
        print(f"  hops={k[0]}, constraints={k[1]}: {len(all_qs[k])} questions")

    missing = [(h, c) for h in range(5) for c in range(3) if (h, c) not in all_qs]
    if missing:
        print(f"Still missing: {missing}")
    else:
        print("All grid cells filled!")

    make_visualization(all_qs)


if __name__ == '__main__':
    main()
