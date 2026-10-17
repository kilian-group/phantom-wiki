"""Temporal question types for PhantomWiki.

Supports:
- "Where did <name> live in <year>?"
- "What was <name>'s job before becoming a <job>?"
- "Who was married first, <name_1> or <name_2>?"
"""

import re

from numpy.random import Generator

from ...utils import decode
from ..database import Database

TEMPORAL_QUESTION_TYPES = [
    "temporal_lived_in",
    "temporal_job_before",
    "temporal_married_first",
]


def is_temporal_question(question: str) -> bool:
    """Returns True if the question matches a temporal question pattern."""
    patterns = [
        r"^Where did .+ live in \d+\?",
        r"^What was .+'s job before becoming a ",
        r"^Who was married first,",
    ]
    return any(re.match(p, question.strip()) for p in patterns)


def sample_temporal_lived_in(
    rng: Generator,
    db: Database,
    person_name_bank: list[str],
    num_sampling_attempts: int = 100,
) -> tuple[str, list[str]] | None:
    """Sample: 'Where did <name> live in <year>?'

    Prolog query: lived_in_at("<name>", City, <year>)
    Answer variable: City
    """
    for _ in range(num_sampling_attempts):
        name = rng.choice(person_name_bank)
        # Get all lived_in facts for this person
        results = list(db.prolog.query(f'lived_in("{name}", City, Start, End)'))
        if not results:
            continue

        # Pick a random period and a year within it
        period = results[int(rng.integers(0, len(results)))]
        start = int(period["Start"])
        end = int(period["End"])
        if end == 9999:
            end = start + 20  # cap current period for question purposes
        if start >= end:
            continue
        year = int(rng.integers(start, end + 1))

        question = f"Where did {name} live in {year}?"
        query = [f'lived_in_at("{name}", City, {year})']
        return question, query

    return None


def sample_temporal_job_before(
    rng: Generator,
    db: Database,
    person_name_bank: list[str],
    num_sampling_attempts: int = 100,
) -> tuple[str, list[str]] | None:
    """Sample: "What was <name>'s job before becoming a <job>?"

    Prolog query: career_before("<name>", JobBefore, "<current_job>")
    Answer variable: JobBefore
    """
    for _ in range(num_sampling_attempts):
        name = rng.choice(person_name_bank)
        # Get career history
        results = list(db.prolog.query(f'career("{name}", Job, Company, Start, End)'))
        if len(results) < 2:
            continue

        # Find a job that has a predecessor
        pairs = list(db.prolog.query(f'career_before("{name}", JobBefore, JobAfter)'))
        if not pairs:
            continue

        pair = pairs[int(rng.integers(0, len(pairs)))]
        job_after = decode(pair["JobAfter"])

        question = f"What was {name}'s job before becoming a {job_after}?"
        query = [f'career_before("{name}", JobBefore, "{job_after}")']
        return question, query

    return None


def sample_temporal_married_first(
    rng: Generator,
    db: Database,
    person_name_bank: list[str],
    num_sampling_attempts: int = 100,
) -> tuple[str, list[str]] | None:
    """Sample: 'Who was married first, <name_1> or <name_2>?'

    Prolog query: married_first("<name_1>", "<name_2>")
    """
    for _ in range(num_sampling_attempts):
        if len(person_name_bank) < 2:
            return None
        idxs = rng.choice(len(person_name_bank), size=2, replace=False)
        name1 = person_name_bank[idxs[0]]
        name2 = person_name_bank[idxs[1]]

        # Both must have marriage_year facts
        m1 = list(db.prolog.query(f'marriage_year("{name1}", _, Y)'))
        m2 = list(db.prolog.query(f'marriage_year("{name2}", _, Y)'))
        if not m1 or not m2:
            continue

        year1 = int(m1[0]["Y"])
        year2 = int(m2[0]["Y"])
        if year1 == year2:
            continue

        question = f"Who was married first, {name1} or {name2}?"
        query = [f'married_first("{name1}", "{name2}")']
        return question, query

    return None


def sample_temporal_question(
    question_type: str,
    rng: Generator,
    db: Database,
    person_name_bank: list[str],
    num_sampling_attempts: int = 100,
) -> tuple[str, list[str]] | None:
    """Sample a temporal question of the given type."""
    if question_type == "temporal_lived_in":
        return sample_temporal_lived_in(rng, db, person_name_bank, num_sampling_attempts)
    elif question_type == "temporal_job_before":
        return sample_temporal_job_before(rng, db, person_name_bank, num_sampling_attempts)
    elif question_type == "temporal_married_first":
        return sample_temporal_married_first(rng, db, person_name_bank, num_sampling_attempts)
    else:
        raise ValueError(f"Unknown temporal question type: {question_type}")


def get_temporal_answer(
    question: str,
    query: list[str],
    question_type: str,
    db: Database,
) -> list[str]:
    """Execute a temporal question's Prolog query and return the answer."""
    joined = ", ".join(query)

    if question_type == "temporal_lived_in":
        results = list(db.prolog.query(joined))
        return sorted({decode(r["City"]) for r in results})

    elif question_type == "temporal_job_before":
        results = list(db.prolog.query(joined))
        return sorted({decode(r["JobBefore"]) for r in results})

    elif question_type == "temporal_married_first":
        results = list(db.prolog.query(joined))
        m = re.match(r"Who was married first, (.+?) or (.+?)\?", question)
        if not m:
            return []
        name1, name2 = m.group(1), m.group(2)
        if results:
            return [name1]
        else:
            return [name2]

    return []
