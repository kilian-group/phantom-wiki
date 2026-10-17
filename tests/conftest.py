"""Shared pytest configuration for phantom-wiki tests.

Adds CLI options:
  --db-path:        Use a custom Prolog database instead of the default small test DB.
  --dump-questions:  Directory to write all questions generated during tests (JSON files by test name).

Usage:
    pytest tests/test_extended_cfg_composition.py -v -s --db-path ./out_100/facts.pl --dump-questions ./test_output
"""

import json
from pathlib import Path

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--db-path",
        action="store",
        default=None,
        type=Path,
        help="Path to a custom Prolog facts file (e.g. ./out_100/facts.pl). "
        "If not provided, tests use the default small test database.",
    )
    parser.addoption(
        "--dump-questions",
        action="store",
        default=None,
        type=Path,
        help="Directory to write generated questions to (JSON files grouped by test). "
        "If not provided, questions are not saved to disk.",
    )


class QuestionCollector:
    """Collects questions generated during tests and writes them to disk."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.questions: dict[str, list[dict]] = {}

    def add(self, test_name: str, question: str, query: list[str],
            answer: list[str] | str | None = None, subtype: str | None = None,
            template: list[str] | None = None):
        if test_name not in self.questions:
            self.questions[test_name] = []
        entry = {
            "question": question,
            "prolog_query": query,
        }
        if answer is not None:
            entry["answer"] = answer
        if subtype is not None:
            entry["subtype"] = subtype
        if template is not None:
            entry["template"] = " ".join(template) if isinstance(template, list) else template
        self.questions[test_name].append(entry)

    def flush(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Write per-test files
        for test_name, entries in self.questions.items():
            safe_name = test_name.replace("::", "__").replace("/", "_")
            path = self.output_dir / f"{safe_name}.json"
            with open(path, "w") as f:
                json.dump(entries, f, indent=2)

        # Write a combined summary
        all_questions = []
        for test_name, entries in sorted(self.questions.items()):
            for entry in entries:
                all_questions.append({"test": test_name, **entry})

        summary_path = self.output_dir / "_all_questions.json"
        with open(summary_path, "w") as f:
            json.dump(all_questions, f, indent=2)

        # Write a human-readable text file
        txt_path = self.output_dir / "_all_questions.txt"
        with open(txt_path, "w") as f:
            for test_name, entries in sorted(self.questions.items()):
                f.write(f"{'=' * 80}\n")
                f.write(f"TEST: {test_name}\n")
                f.write(f"{'=' * 80}\n\n")
                for i, entry in enumerate(entries, 1):
                    f.write(f"  [{i}] Q: {entry['question']}\n")
                    f.write(f"      Prolog: {', '.join(entry['prolog_query'])}\n")
                    if "answer" in entry:
                        f.write(f"      Answer: {entry['answer']}\n")
                    if "subtype" in entry:
                        f.write(f"      Type: {entry['subtype']}\n")
                    if "template" in entry:
                        f.write(f"      Template: {entry['template']}\n")
                    f.write("\n")

        total = sum(len(e) for e in self.questions.values())
        print(f"\n>>> Dumped {total} questions across {len(self.questions)} tests to {self.output_dir}/")
        print(f"    - {summary_path}  (all questions, JSON)")
        print(f"    - {txt_path}  (all questions, human-readable)")


@pytest.fixture(scope="module")
def question_collector(request):
    dump_dir = request.config.getoption("--dump-questions", default=None)
    if dump_dir is None:
        yield None
    else:
        collector = QuestionCollector(dump_dir.resolve())
        yield collector
        collector.flush()
