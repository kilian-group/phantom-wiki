"""Difficulty-balanced question sampling.

When enabled via --balanced, samples equal numbers of questions per difficulty bucket
instead of uniform sampling from templates (which leads to imbalanced difficulty distribution).

Difficulty buckets:
    - easy:       1-3 steps
    - medium:     4-6 steps
    - hard:       7-9 steps
    - very_hard:  10-12 steps
    - extreme:    13+ steps
"""

import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

DIFFICULTY_BUCKETS = {
    "easy": (1, 3),
    "medium": (4, 6),
    "hard": (7, 9),
    "very_hard": (10, 12),
    "extreme": (13, float("inf")),
}


def _extract_composite(difficulty) -> int:
    """Extract the scalar composite from a difficulty field (int or dict)."""
    if isinstance(difficulty, dict):
        return difficulty.get("composite", 0)
    return difficulty


def get_difficulty_bucket(difficulty) -> str:
    """Map a difficulty score to a bucket name."""
    composite = _extract_composite(difficulty)
    for bucket_name, (low, high) in DIFFICULTY_BUCKETS.items():
        if low <= composite <= high:
            return bucket_name
    return "extreme"  # fallback


def balanced_sample(
    all_questions: list[dict],
    target_per_bucket: int | None = None,
) -> list[dict]:
    """Sample questions to achieve balanced difficulty distribution.

    Groups all questions by difficulty bucket, then samples equal numbers
    from each bucket. If a bucket has fewer questions than the target,
    all questions from that bucket are included.

    Args:
        all_questions: List of question dicts with 'difficulty' field.
        target_per_bucket: Number of questions per bucket. If None,
            uses the minimum bucket size for perfect balance.

    Returns:
        Balanced list of questions, each annotated with 'difficulty_bucket'.
    """
    # Group by bucket
    buckets: dict[str, list[dict]] = defaultdict(list)
    for q in all_questions:
        bucket = get_difficulty_bucket(q["difficulty"])
        q["difficulty_bucket"] = bucket
        buckets[bucket].append(q)

    # Log distribution
    logger.info("Question distribution by difficulty bucket:")
    for bucket_name in DIFFICULTY_BUCKETS:
        count = len(buckets.get(bucket_name, []))
        logger.info(f"  {bucket_name}: {count} questions")

    # Determine target
    non_empty_counts = [len(v) for v in buckets.values() if len(v) > 0]
    if not non_empty_counts:
        return all_questions

    if target_per_bucket is None:
        target_per_bucket = min(non_empty_counts)

    logger.info(f"Sampling {target_per_bucket} questions per bucket")

    # Sample from each bucket
    import numpy as np

    rng = np.random.default_rng(seed=42)
    sampled = []
    for bucket_name in DIFFICULTY_BUCKETS:
        bucket_qs = buckets.get(bucket_name, [])
        if not bucket_qs:
            continue
        n = min(target_per_bucket, len(bucket_qs))
        indices = rng.choice(len(bucket_qs), size=n, replace=False)
        for idx in indices:
            sampled.append(bucket_qs[idx])

    logger.info(f"Balanced sampling: {len(sampled)} questions total")
    return sampled


# Type-based balanced proportions when --balanced is used with extended types
TYPE_PROPORTIONS = {
    "base": 0.40,
    "comparison": 0.20,
    "multi_constraint": 0.20,
    "superlative": 0.20,
}


def balanced_sample_by_type(
    all_questions: list[dict],
    total_target: int | None = None,
) -> list[dict]:
    """Sample questions to achieve balanced type distribution (40/20/20/20).

    Groups questions by question_category type, then samples proportionally.
    Within each type, applies difficulty-balanced sampling.

    Args:
        all_questions: List of question dicts with 'question_category' and 'difficulty' fields.
        total_target: Total number of questions desired. If None, uses all available.

    Returns:
        Balanced list of questions.
    """
    from .templates import classify_question_type

    # Group by type
    type_buckets: dict[str, list[dict]] = defaultdict(list)
    for q in all_questions:
        cat = q.get("question_category", "")
        # Map specific subtypes to broad categories
        if "comparison" in cat:
            qtype = "comparison"
        elif "multi_constraint" in cat:
            qtype = "multi_constraint"
        elif "superlative" in cat:
            qtype = "superlative"
        else:
            qtype = "base"
        type_buckets[qtype].append(q)

    if total_target is None:
        total_target = len(all_questions)

    import numpy as np

    rng = np.random.default_rng(seed=42)
    sampled = []

    for qtype, proportion in TYPE_PROPORTIONS.items():
        bucket = type_buckets.get(qtype, [])
        if not bucket:
            continue
        target = min(int(total_target * proportion), len(bucket))
        if target > 0:
            indices = rng.choice(len(bucket), size=target, replace=False)
            for idx in indices:
                sampled.append(bucket[idx])

    logger.info(f"Type-balanced sampling: {len(sampled)} questions total")
    return sampled


def filter_by_difficulty(
    questions: list[dict],
    min_difficulty: int | None = None,
    max_difficulty: int | None = None,
) -> list[dict]:
    """Filter questions by difficulty range (uses composite score).

    Args:
        questions: List of question dicts with 'difficulty' field (int or dict).
        min_difficulty: Minimum composite difficulty (inclusive). None = no minimum.
        max_difficulty: Maximum composite difficulty (inclusive). None = no maximum.

    Returns:
        Filtered list of questions.
    """
    filtered = []
    for q in questions:
        d = _extract_composite(q["difficulty"])
        if min_difficulty is not None and d < min_difficulty:
            continue
        if max_difficulty is not None and d > max_difficulty:
            continue
        filtered.append(q)
    return filtered


# ---------------------------------------------------------------------------
# Step-range-based sampling (--sample-count with numeric min/max filters)
# ---------------------------------------------------------------------------


def _matches_step_range(
    difficulty: int,
    min_steps: int | None,
    max_steps: int | None,
) -> bool:
    """Check whether a difficulty value falls within [min_steps, max_steps]."""
    if min_steps is not None and difficulty < min_steps:
        return False
    if max_steps is not None and difficulty > max_steps:
        return False
    return True


def sample_questions(
    questions: list[dict],
    count: int,
    question_types: list[str] | None = None,
    min_steps: int | None = None,
    max_steps: int | None = None,
    seed: int = 42,
) -> list[dict]:
    """Sample an exact number of questions, optionally filtered by step range and type.

    Filtering is applied first to build a pool, then ``count`` questions are
    drawn uniformly at random (without replacement) from that pool.

    Args:
        questions: Full list of question dicts (must have ``difficulty`` field,
            and optionally ``question_category``).
        count: Exact number of questions to return.
        question_types: If given, only include questions whose
            ``question_category`` contains one of these strings.
        min_steps: Minimum reasoning steps (inclusive).
        max_steps: Maximum reasoning steps (inclusive).
        seed: RNG seed for reproducibility.

    Returns:
        List of ``count`` question dicts.

    Raises:
        ValueError: If the filtered pool is smaller than ``count``.
    """
    # Build filtered pool
    pool: list[dict] = []
    for q in questions:
        d = _extract_composite(q["difficulty"])

        # Step range filter
        if not _matches_step_range(d, min_steps, max_steps):
            continue

        # Type filter
        if question_types is not None:
            cat = q.get("question_category", "")
            if not any(t in cat for t in question_types):
                continue

        pool.append(q)

    # Check pool size
    if len(pool) < count:
        raise ValueError(
            f"Requested {count} questions but only {len(pool)} match the filters "
            f"(min_steps={min_steps}, max_steps={max_steps}, "
            f"question_types={question_types}). Reduce count or loosen filters."
        )

    # Sample
    import numpy as np

    rng = np.random.default_rng(seed=seed)
    indices = rng.choice(len(pool), size=count, replace=False)
    sampled = [pool[int(i)] for i in indices]

    logger.info(
        f"Sampled {count} questions (pool size {len(pool)}, "
        f"steps=[{min_steps}, {max_steps}], types={question_types})"
    )
    return sampled


def describe_pool(questions: list[dict]) -> dict:
    """Compute a breakdown of the question pool by composite difficulty and type.

    Args:
        questions: Full list of question dicts with ``difficulty`` and
            optionally ``question_category`` fields.

    Returns:
        Dictionary with keys:

        - ``total``: Total number of questions.
        - ``by_composite``: ``{composite_int: count}``.
        - ``by_type``: ``{type_name: count}`` where type is derived from
          ``question_category``.
        - ``by_composite_and_type``: ``{composite_int: {type_name: count}}``.
    """
    by_composite: dict[int, int] = defaultdict(int)
    by_type: dict[str, int] = defaultdict(int)
    by_both: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for q in questions:
        d = _extract_composite(q["difficulty"])
        cat = q.get("question_category", "")
        qtype = _classify_broad_type(cat)

        by_composite[d] += 1
        by_type[qtype] += 1
        by_both[d][qtype] += 1

    return {
        "total": len(questions),
        "by_composite": dict(sorted(by_composite.items())),
        "by_type": dict(by_type),
        "by_composite_and_type": {k: dict(v) for k, v in sorted(by_both.items())},
    }


def _classify_broad_type(question_category: str) -> str:
    """Map a question_category string to a broad type name."""
    if "comparison" in question_category:
        return "comparison"
    elif "multi_constraint" in question_category:
        return "multi_constraint"
    elif "superlative" in question_category:
        return "superlative"
    else:
        return "base"
