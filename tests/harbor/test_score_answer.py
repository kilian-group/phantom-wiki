"""Tests for the verifier scoring, which mirrors phantom_eval.score (set-based F1)."""

import json

import score_answer as scorer


def test_exact_single_value():
    assert scorer.precision_recall_f1("Alice", "Alice")[2] == 1.0
    assert scorer.exact_match("Alice", "Alice") == 1.0


def test_case_and_whitespace_insensitive():
    assert scorer.exact_match(" alice ", "Alice") == 1.0


def test_order_invariant_set_match():
    assert scorer.exact_match("Bob, Alice", "Alice, Bob") == 1.0


def test_partial_overlap_f1():
    precision, recall, f1 = scorer.precision_recall_f1("Alice, Bob", "Alice, Carol")
    assert precision == 0.5
    assert recall == 0.5
    assert abs(f1 - 0.5) < 1e-9


def test_extra_predictions_lower_precision():
    precision, recall, f1 = scorer.precision_recall_f1("Alice, Bob, Carol", "Alice")
    assert abs(precision - 1 / 3) < 1e-9
    assert recall == 1.0


def test_empty_prediction_scores_zero():
    assert scorer.precision_recall_f1("", "Alice")[2] == 0.0


def test_missing_answer_file_is_empty(tmp_path):
    assert scorer.read_answer(tmp_path / "does_not_exist.txt") == ""


def test_main_writes_reward_and_result(tmp_path):
    questions = [{"id": "x", "question": "Who?", "answer": ["Alice", "Bob"], "type": 0, "difficulty": 3}]
    questions_path = tmp_path / "questions.json"
    questions_path.write_text(json.dumps(questions))
    answer_path = tmp_path / "answer.txt"
    answer_path.write_text("alice, bob")
    reward_path = tmp_path / "reward.txt"
    result_path = tmp_path / "result.json"

    scorer.main(
        [
            "--questions",
            str(questions_path),
            "--qid",
            "0",
            "--seed",
            "1",
            "--answer",
            str(answer_path),
            "--reward-file",
            str(reward_path),
            "--result-file",
            str(result_path),
        ]
    )

    assert float(reward_path.read_text()) == 1.0
    result = json.loads(result_path.read_text())
    assert result["difficulty"] == 3
    assert result["f1"] == 1.0
