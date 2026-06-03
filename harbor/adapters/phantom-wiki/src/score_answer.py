"""Score a PhantomWiki answer inside the Harbor verifier container.

This runs in the *separate* verifier image, which has regenerated the same universe
(same pinned deps + seed) the agent saw and therefore holds the gold answers. It reads
the agent's answer from ``/logs/artifacts/answer.txt`` (forwarded by Harbor), computes
set-based F1 against the gold answer, writes the reward to ``/logs/verifier/reward.txt``
and a per-question diagnostic row (including ``difficulty``) to
``/logs/verifier/result.json``.

The metrics here mirror ``phantom_eval.score`` exactly (comma-separated, lowercased,
stripped, set-based precision/recall/F1) but are reimplemented inline so the verifier
image only needs ``phantom-wiki`` (for generation) -- importing ``phantom_eval`` would
pull in heavy eval-only dependencies (datasets, transformers, ...).

This file depends on the standard library plus ``select_question`` (copied alongside it
into the ``tests/`` build context) only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from select_question import load_questions, select_question

# Matches phantom_eval.constants.answer_sep.
ANSWER_SEP = ","


def normalize(text: str, sep: str = ANSWER_SEP) -> set[str]:
    """Split on ``sep``, strip + lowercase each item, and dedupe into a set."""
    return {item.strip().lower() for item in text.split(sep)}


def precision_recall_f1(pred: str, true: str, sep: str = ANSWER_SEP) -> tuple[float, float, float]:
    """Set-based precision/recall/F1, matching phantom_eval.score."""
    preds = normalize(pred, sep)
    trues = normalize(true, sep)
    if not preds:
        return 0.0, 0.0, 0.0
    precision = sum(word in trues for word in preds) / len(preds)
    recall = (sum(word in preds for word in trues) / len(trues)) if trues else 0.0
    if precision + recall == 0:
        return precision, recall, 0.0
    return precision, recall, 2 * precision * recall / (precision + recall)


def exact_match(pred: str, true: str, sep: str = ANSWER_SEP) -> float:
    return float(normalize(pred, sep) == normalize(true, sep))


def read_answer(path: str | Path) -> str:
    """Read the agent's answer file, treating a missing/unreadable file as empty."""
    try:
        return Path(path).read_text()
    except (FileNotFoundError, IsADirectoryError):
        return ""


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Score a PhantomWiki answer and emit the Harbor reward.")
    parser.add_argument("--questions", required=True, help="Path to the regenerated questions.json.")
    parser.add_argument("--qid", type=int, required=True, help="Task index.")
    parser.add_argument("--seed", type=int, required=True, help="Universe generation seed.")
    parser.add_argument("--answer", required=True, help="Path to the agent's answer file.")
    parser.add_argument("--reward-file", default="/logs/verifier/reward.txt")
    parser.add_argument("--result-file", default="/logs/verifier/result.json")
    args = parser.parse_args(argv)

    question = select_question(load_questions(args.questions), args.qid, args.seed)
    gold = question["answer"]
    true = ANSWER_SEP.join(map(str, gold)) if isinstance(gold, list) else str(gold)
    pred = read_answer(args.answer)

    precision, recall, f1 = precision_recall_f1(pred, true)
    em = exact_match(pred, true)

    result = {
        "id": question.get("id"),
        "qid": args.qid,
        "seed": args.seed,
        "type": question.get("type"),
        "difficulty": question.get("difficulty"),
        "is_aggregation_question": question.get("is_aggregation_question"),
        "question": question.get("question"),
        "true": true,
        "pred": pred.strip(),
        "EM": em,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }

    for path in (args.reward_file, args.result_file):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    # Harbor reads a single float reward from reward.txt; we use F1.
    Path(args.reward_file).write_text(f"{f1:.6f}\n")
    Path(args.result_file).write_text(json.dumps(result, indent=2))
    print(f"qid={args.qid} difficulty={result['difficulty']} F1={f1:.3f} EM={em:.0f}")


if __name__ == "__main__":
    main()
