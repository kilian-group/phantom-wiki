"""Tests for the deterministic question selector shared by the agent/verifier images."""

import pytest
from select_question import select_question

QUESTIONS = [{"id": str(i), "question": f"q{i}", "answer": [f"a{i}"]} for i in range(20)]


def test_same_qid_and_seed_is_deterministic():
    assert select_question(QUESTIONS, 3, seed=42) == select_question(QUESTIONS, 3, seed=42)


def test_distinct_qids_map_to_distinct_questions():
    # A seeded shuffle is a permutation, so qids 0..N-1 cover every question exactly once.
    seen = {select_question(QUESTIONS, qid, seed=7)["id"] for qid in range(len(QUESTIONS))}
    assert len(seen) == len(QUESTIONS)


def test_different_seed_changes_ordering():
    order_a = [select_question(QUESTIONS, qid, seed=1)["id"] for qid in range(len(QUESTIONS))]
    order_b = [select_question(QUESTIONS, qid, seed=2)["id"] for qid in range(len(QUESTIONS))]
    assert order_a != order_b


def test_qid_wraps_around():
    n = len(QUESTIONS)
    assert select_question(QUESTIONS, n + 5, seed=3) == select_question(QUESTIONS, 5, seed=3)


def test_empty_questions_raises():
    with pytest.raises(ValueError):
        select_question([], 0, 0)
