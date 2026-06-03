"""Determinism guarantee underpinning the separate agent/verifier images.

The Harbor integration generates the universe twice -- once in the agent image (corpus
only) and once in the verifier image (with gold answers) -- and relies on both producing
the *identical* universe from the same seed. This test verifies that guarantee by running
``pw-generate`` twice with the same seed and asserting the articles and question/answer
pairs match byte-for-byte.

Skipped automatically when phantom-wiki / SWI-Prolog are not installed.
"""

import json
import shutil
import subprocess

import pytest

pytestmark = pytest.mark.skipif(
    shutil.which("pw-generate") is None or shutil.which("swipl") is None,
    reason="Requires phantom-wiki (pw-generate) and SWI-Prolog (swipl) to be installed.",
)


def _generate(out_dir, seed):
    subprocess.run(
        ["pw-generate", "--seed", str(seed), "--question-format", "json", "-od", str(out_dir)],
        check=True,
    )


def test_same_seed_yields_identical_universe(tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    _generate(first, seed=1)
    _generate(second, seed=1)

    articles_first = sorted((first / "articles").glob("*.txt"))
    articles_second = sorted((second / "articles").glob("*.txt"))
    assert [p.name for p in articles_first] == [p.name for p in articles_second]
    assert articles_first, "expected at least one generated article"
    for a, b in zip(articles_first, articles_second):
        assert a.read_text() == b.read_text(), f"article {a.name} differs across identical seeds"

    qa_first = json.loads((first / "questions.json").read_text())
    qa_second = json.loads((second / "questions.json").read_text())
    keyed = lambda qs: [(q["question"], q["answer"]) for q in qs]  # noqa: E731
    assert keyed(qa_first) == keyed(qa_second)
