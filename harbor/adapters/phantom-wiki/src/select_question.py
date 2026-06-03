"""Deterministic question selection shared by the agent and verifier images.

Both the agent's environment image and the (separate) verifier image regenerate the
*same* PhantomWiki universe from the same seed. They must therefore agree on which
question a given task refers to. This module provides that mapping: given the flat list
of generated questions, a task index ``qid``, and the generation ``seed``, it returns
the same question record in both images.

The selection deterministically shuffles the question list with ``seed`` so that the N
stamped tasks spread across question types/difficulties instead of clustering on the
first type. Because the shuffle is seeded identically in both images, the environment
(which shows the agent the question text) and the verifier (which scores against the
gold answer) always resolve ``qid`` to the same question.

This file is copied verbatim into both the ``environment/`` and ``tests/`` Docker build
contexts by the adapter, so it must depend on the standard library only.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


def load_questions(path: str | Path) -> list[dict]:
    """Load the flat list of question records written by ``pw-generate --question-format json``."""
    with open(path) as f:
        return json.load(f)


def select_question(questions: list[dict], qid: int, seed: int) -> dict:
    """Resolve ``qid`` to a single question record, deterministically given ``seed``.

    The same ``(qid, seed)`` always maps to the same question, both in the agent image
    and in the verifier image, as long as ``questions`` was produced from that seed.
    """
    if not questions:
        raise ValueError("No questions available to select from.")
    order = list(range(len(questions)))
    random.Random(seed).shuffle(order)
    return questions[order[qid % len(questions)]]


def main() -> None:
    parser = argparse.ArgumentParser(description="Print one field of the question selected for a task.")
    parser.add_argument("--questions", required=True, help="Path to questions.json.")
    parser.add_argument("--qid", type=int, required=True, help="Task index.")
    parser.add_argument("--seed", type=int, required=True, help="Universe generation seed.")
    parser.add_argument("--field", default="question", help="Field to print (default: question).")
    args = parser.parse_args()

    question = select_question(load_questions(args.questions), args.qid, args.seed)
    value = question[args.field]
    if isinstance(value, list):
        print(", ".join(map(str, value)))
    else:
        print(value)


if __name__ == "__main__":
    main()
