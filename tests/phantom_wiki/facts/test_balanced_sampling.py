"""Tests for difficulty-balanced question sampling."""

import pytest

from phantom_wiki.facts.balanced_sampling import (
    DIFFICULTY_BUCKETS,
    balanced_sample,
    filter_by_difficulty,
    get_difficulty_bucket,
)


# ---------------------------------------------------------------------------
# Test difficulty bucket classification
# ---------------------------------------------------------------------------
class TestGetDifficultyBucket:
    def test_easy(self):
        assert get_difficulty_bucket(1) == "easy"
        assert get_difficulty_bucket(2) == "easy"
        assert get_difficulty_bucket(3) == "easy"

    def test_medium(self):
        assert get_difficulty_bucket(4) == "medium"
        assert get_difficulty_bucket(6) == "medium"

    def test_hard(self):
        assert get_difficulty_bucket(7) == "hard"
        assert get_difficulty_bucket(9) == "hard"

    def test_very_hard(self):
        assert get_difficulty_bucket(10) == "very_hard"
        assert get_difficulty_bucket(12) == "very_hard"

    def test_extreme(self):
        assert get_difficulty_bucket(13) == "extreme"
        assert get_difficulty_bucket(50) == "extreme"


# ---------------------------------------------------------------------------
# Test balanced sampling
# ---------------------------------------------------------------------------
def _make_questions(difficulties: list[int]) -> list[dict]:
    """Helper to create question dicts with given difficulties."""
    return [
        {"id": str(i), "question": f"Q{i}", "difficulty": d}
        for i, d in enumerate(difficulties)
    ]


class TestBalancedSample:
    def test_balances_across_buckets(self):
        # 10 easy, 5 medium, 3 hard
        difficulties = [1] * 10 + [5] * 5 + [8] * 3
        questions = _make_questions(difficulties)
        result = balanced_sample(questions)

        # Should have 3 per non-empty bucket (min bucket size = 3)
        bucket_counts = {}
        for q in result:
            b = q["difficulty_bucket"]
            bucket_counts[b] = bucket_counts.get(b, 0) + 1

        assert bucket_counts["easy"] == 3
        assert bucket_counts["medium"] == 3
        assert bucket_counts["hard"] == 3

    def test_target_per_bucket(self):
        difficulties = [1] * 10 + [5] * 10 + [8] * 10
        questions = _make_questions(difficulties)
        result = balanced_sample(questions, target_per_bucket=5)

        bucket_counts = {}
        for q in result:
            b = q["difficulty_bucket"]
            bucket_counts[b] = bucket_counts.get(b, 0) + 1

        assert all(c == 5 for c in bucket_counts.values())

    def test_empty_input(self):
        result = balanced_sample([])
        assert result == []

    def test_single_bucket(self):
        questions = _make_questions([1, 2, 3])
        result = balanced_sample(questions)
        assert len(result) == 3  # all in one bucket

    def test_adds_difficulty_bucket_field(self):
        questions = _make_questions([1, 5, 8])
        result = balanced_sample(questions)
        for q in result:
            assert "difficulty_bucket" in q

    def test_bucket_with_fewer_than_target(self):
        # 10 easy, 2 hard
        difficulties = [1] * 10 + [8] * 2
        questions = _make_questions(difficulties)
        result = balanced_sample(questions)  # target = min(10, 2) = 2

        bucket_counts = {}
        for q in result:
            b = q["difficulty_bucket"]
            bucket_counts[b] = bucket_counts.get(b, 0) + 1

        assert bucket_counts["easy"] == 2
        assert bucket_counts["hard"] == 2


# ---------------------------------------------------------------------------
# Test difficulty filtering
# ---------------------------------------------------------------------------
class TestFilterByDifficulty:
    def test_min_difficulty(self):
        questions = _make_questions([1, 3, 5, 7, 10])
        result = filter_by_difficulty(questions, min_difficulty=5)
        assert len(result) == 3
        assert all(q["difficulty"] >= 5 for q in result)

    def test_max_difficulty(self):
        questions = _make_questions([1, 3, 5, 7, 10])
        result = filter_by_difficulty(questions, max_difficulty=5)
        assert len(result) == 3
        assert all(q["difficulty"] <= 5 for q in result)

    def test_range(self):
        questions = _make_questions([1, 3, 5, 7, 10])
        result = filter_by_difficulty(questions, min_difficulty=3, max_difficulty=7)
        assert len(result) == 3
        assert all(3 <= q["difficulty"] <= 7 for q in result)

    def test_no_filter(self):
        questions = _make_questions([1, 3, 5])
        result = filter_by_difficulty(questions)
        assert len(result) == 3

    def test_empty_result(self):
        questions = _make_questions([1, 2, 3])
        result = filter_by_difficulty(questions, min_difficulty=10)
        assert len(result) == 0
