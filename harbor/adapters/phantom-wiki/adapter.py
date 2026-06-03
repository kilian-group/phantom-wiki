"""PhantomWiki -> Harbor adapter.

Stamps a fresh PhantomWiki evaluation dataset as a set of Harbor tasks -- one task per
question -- WITHOUT generating anything on the host. Generation is deferred into each
task's Docker build (see ``template/environment/Dockerfile`` and
``template/tests/Dockerfile``), so the only host requirements are Docker and Harbor; no
SWI-Prolog or ``phantom-wiki`` install is needed locally.

Each ``harbor run`` of the produced dataset evaluates a model (via the Terminus agent) on
a freshly generated universe -- the whole point of PhantomWiki: on-demand,
contamination-resistant evaluation.
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE_DIR = HERE / "template"
SHARED_DIR = HERE / "src"

# Default pip spec for the in-Docker generator. Pin to e.g. "phantom-wiki==0.x.y" for a
# fully reproducible universe across re-runs.
DEFAULT_PW_SPEC = "phantom-wiki"

# Files in the template whose __PLACEHOLDER__ tokens must be substituted.
_TEXT_SUFFIXES = {".toml", ".md", ".sh"}
_TEXT_NAMES = {"Dockerfile"}


def _git_commit() -> str | None:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=HERE, stderr=subprocess.DEVNULL)
        return out.decode().strip()
    except Exception:
        return None


def _substitute(text: str, mapping: dict[str, str]) -> str:
    for key, value in mapping.items():
        text = text.replace(key, value)
    return text


def _is_text_template(path: Path) -> bool:
    return path.suffix in _TEXT_SUFFIXES or path.name in _TEXT_NAMES


def _stamp_task(task_dir: Path, mapping: dict[str, str]) -> None:
    """Materialize one task directory from the template, substituting placeholders."""
    if task_dir.exists():
        shutil.rmtree(task_dir)

    for src in sorted(TEMPLATE_DIR.rglob("*")):
        dst = task_dir / src.relative_to(TEMPLATE_DIR)
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if _is_text_template(src):
            dst.write_text(_substitute(src.read_text(), mapping))
        else:
            shutil.copy2(src, dst)

    # Inject the shared selection/scoring code into the build contexts.
    shutil.copy2(SHARED_DIR / "select_question.py", task_dir / "environment" / "select_question.py")
    shutil.copy2(SHARED_DIR / "select_question.py", task_dir / "tests" / "select_question.py")
    shutil.copy2(SHARED_DIR / "score_answer.py", task_dir / "tests" / "score_answer.py")

    # Keep the verifier entrypoint executable (matches its shebang).
    (task_dir / "tests" / "test.sh").chmod(0o755)


def generate_dataset(
    output_dir: str | Path,
    num_tasks: int = 50,
    seed: int | None = None,
    pw_spec: str = DEFAULT_PW_SPEC,
    gen_flags: str = "",
) -> dict:
    """Stamp ``num_tasks`` Harbor tasks for one freshly-seeded PhantomWiki universe.

    Args:
        output_dir: Where to write the dataset (one subdirectory per task).
        num_tasks: Number of questions/tasks to stamp.
        seed: Universe seed. ``None`` picks a random seed => a fresh universe each run.
        pw_spec: pip spec for phantom-wiki installed inside the task images.
        gen_flags: Extra flags forwarded to ``pw-generate`` inside Docker (e.g. universe
            size). Left empty by default to keep generation single-threaded/deterministic.

    Returns:
        The dataset metadata dict (also written to ``output_dir/metadata.json``).
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if seed is None:
        seed = random.randrange(1, 2**31 - 1)

    base_mapping = {"__SEED__": str(seed), "__PW_SPEC__": pw_spec, "__GEN_FLAGS__": gen_flags}

    task_names = []
    for qid in range(num_tasks):
        task_name = f"phantom-wiki-seed{seed}-q{qid:05d}"
        _stamp_task(output_dir / task_name, dict(base_mapping, __QID__=str(qid)))
        task_names.append(task_name)

    metadata = {
        "dataset": "phantom-wiki",
        "seed": seed,
        "num_tasks": num_tasks,
        "pw_spec": pw_spec,
        "gen_flags": gen_flags,
        "git_commit": _git_commit(),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tasks": task_names,
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
    return metadata


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a PhantomWiki Harbor dataset.")
    parser.add_argument("--output-dir", required=True, help="Directory to write the dataset to.")
    parser.add_argument("--split", default=None, help="Accepted for Harbor compatibility; unused.")
    parser.add_argument("--num-tasks", type=int, default=50, help="Number of questions/tasks (default: 50).")
    parser.add_argument(
        "--seed", type=int, default=None, help="Universe seed (default: random => fresh each run)."
    )
    parser.add_argument("--pw-spec", default=DEFAULT_PW_SPEC, help='pip spec, e.g. "phantom-wiki==0.x.y".')
    parser.add_argument("--gen-flags", default="", help="Extra flags passed to pw-generate inside Docker.")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _build_arg_parser().parse_args(argv)
    metadata = generate_dataset(
        output_dir=args.output_dir,
        num_tasks=args.num_tasks,
        seed=args.seed,
        pw_spec=args.pw_spec,
        gen_flags=args.gen_flags,
    )
    print(
        f"Stamped {metadata['num_tasks']} PhantomWiki tasks "
        f"(seed={metadata['seed']}) to {args.output_dir}"
    )


if __name__ == "__main__":
    main()
