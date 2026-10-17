"""Validate that hop counts stored in generated JSON files match what
compute_difficulty() derives from the Prolog rules.

Usage:
    python scripts/validate_hop_counts.py <output_dir> [<output_dir> ...]

    # default: validates out_1000_easy/questions/
    python scripts/validate_hop_counts.py

compute_difficulty() is imported directly from phantom_wiki.facts.difficulty —
no hop-count logic is reimplemented here.
"""

import argparse
import json
import sys
from pathlib import Path

# Make sure the src package is importable when running from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from phantom_wiki.facts.difficulty import compute_difficulty  # noqa: E402


def _check_file(path: Path) -> list[dict]:
    """Return a list of mismatch records for a single JSON file."""
    mismatches = []
    with open(path) as f:
        questions = json.load(f)

    for q in questions:
        stored = q.get("difficulty")
        query = q.get("prolog", {}).get("query")

        if stored is None or query is None:
            continue

        recomputed = compute_difficulty(query)

        if (
            recomputed["hops"] != stored.get("hops")
            or recomputed["constraints"] != stored.get("constraints")
            or recomputed["composite"] != stored.get("composite")
        ):
            mismatches.append(
                {
                    "file": path.name,
                    "id": q.get("id", "<no-id>"),
                    "question": q.get("question", ""),
                    "query": query,
                    "stored": stored,
                    "recomputed": recomputed,
                }
            )

    return mismatches


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate hop counts in generated JSON files.")
    parser.add_argument(
        "output_dirs",
        nargs="*",
        default=["out_1000_easy"],
        help="Output directories to validate (default: out_1000_easy)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print every mismatch with full query details",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    all_mismatches: list[dict] = []
    total_questions = 0

    for out_dir in args.output_dirs:
        questions_dir = repo_root / out_dir / "questions"
        if not questions_dir.exists():
            print(f"[WARN] Directory not found: {questions_dir}")
            continue

        json_files = sorted(questions_dir.glob("type*.json"))
        if not json_files:
            print(f"[WARN] No type*.json files found in {questions_dir}")
            continue

        for path in json_files:
            with open(path) as f:
                qs = json.load(f)
            total_questions += len(qs)
            mismatches = _check_file(path)
            all_mismatches.extend(mismatches)

    # -----------------------------------------------------------------------
    # Report
    # -----------------------------------------------------------------------
    if not all_mismatches:
        print(f"OK  All {total_questions} questions have correct hop counts.")
        return

    print(f"FAIL  {len(all_mismatches)} / {total_questions} questions have mismatched hop counts.\n")

    by_file: dict[str, list[dict]] = {}
    for m in all_mismatches:
        by_file.setdefault(m["file"], []).append(m)

    for fname, items in sorted(by_file.items()):
        print(f"  {fname}: {len(items)} mismatch(es)")
        for m in items:
            print(f"    id       : {m['id']}")
            print(f"    question : {m['question']}")
            if args.verbose:
                print(f"    query    : {m['query']}")
            stored = m["stored"]
            recomp = m["recomputed"]
            print(
                f"    stored   : hops={stored.get('hops')}  constraints={stored.get('constraints')}  "
                f"composite={stored.get('composite')}  level={stored.get('level')}"
            )
            print(
                f"    recomputed: hops={recomp['hops']}  constraints={recomp['constraints']}  "
                f"composite={recomp['composite']}  level={recomp['level']}"
            )
            print()

    sys.exit(1)


if __name__ == "__main__":
    main()
