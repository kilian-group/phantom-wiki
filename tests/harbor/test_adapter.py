"""Tests for the PhantomWiki -> Harbor adapter that stamps task directories."""

import stat

import adapter

PLACEHOLDERS = ["__SEED__", "__QID__", "__PW_SPEC__", "__GEN_FLAGS__"]


def _task_dirs(root):
    return sorted(p for p in root.iterdir() if p.is_dir())


def test_generate_dataset_stamps_expected_layout(tmp_path):
    meta = adapter.generate_dataset(tmp_path, num_tasks=3, seed=123)
    assert meta["seed"] == 123
    assert len(meta["tasks"]) == 3
    assert (tmp_path / "metadata.json").exists()

    dirs = _task_dirs(tmp_path)
    assert len(dirs) == 3
    for task_dir in dirs:
        for required in [
            "task.toml",
            "instruction.md",
            "environment/Dockerfile",
            "environment/select_question.py",
            "tests/Dockerfile",
            "tests/test.sh",
            "tests/select_question.py",
            "tests/score_answer.py",
        ]:
            assert (task_dir / required).exists(), f"missing {required} in {task_dir.name}"


def test_placeholders_fully_substituted(tmp_path):
    adapter.generate_dataset(tmp_path, num_tasks=2, seed=7)
    for task_dir in _task_dirs(tmp_path):
        for rel in ["task.toml", "environment/Dockerfile", "tests/Dockerfile", "tests/test.sh"]:
            text = (task_dir / rel).read_text()
            for placeholder in PLACEHOLDERS:
                assert placeholder not in text, f"{placeholder} left in {rel}"


def test_gold_scorer_absent_from_agent_environment(tmp_path):
    # The scorer (which resolves gold answers) must never be in the agent's build context.
    adapter.generate_dataset(tmp_path, num_tasks=1, seed=1)
    task_dir = _task_dirs(tmp_path)[0]
    assert not (task_dir / "environment" / "score_answer.py").exists()


def test_test_script_is_executable(tmp_path):
    adapter.generate_dataset(tmp_path, num_tasks=1, seed=1)
    task_dir = _task_dirs(tmp_path)[0]
    mode = (task_dir / "tests" / "test.sh").stat().st_mode
    assert mode & stat.S_IXUSR


def test_random_seed_when_unspecified(tmp_path):
    meta = adapter.generate_dataset(tmp_path, num_tasks=1, seed=None)
    assert isinstance(meta["seed"], int) and meta["seed"] > 0
