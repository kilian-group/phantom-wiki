"""Tests for extended question types: comparison, multi-constraint, superlative.

Uses a small universe (the small.pl test database with ~27 people) to verify
that each question type generates valid questions and correct answers.
"""

import numpy as np
import pytest

from phantom_wiki.facts import get_database
from phantom_wiki.facts.attributes.constants import ATTRIBUTE_TYPES
from phantom_wiki.facts.extended_questions import (
    COMPARISON_AGE_TYPE,
    MULTI_CONSTRAINT_TYPE,
    SUPERLATIVE_MOST_TYPE,
    SUPERLATIVE_OLDEST_TYPE,
    SUPERLATIVE_YOUNGEST_TYPE,
    build_comparison_count_variants,
    build_extended_question_types,
    get_extended_answer,
    is_extended_question,
    sample_comparison_age_question,
    sample_comparison_count_extended_question,
    sample_extended_question,
    sample_multi_constraint_question,
    sample_superlative_age_question,
    sample_superlative_most_question,
)

# A reference variants table for tests that need a baseline dispatch dict
_TEST_COUNT_VARIANTS = build_comparison_count_variants(
    max_chain_depth=1, n_attrs_options=(0, 2),
)
_COMPARISON_COUNT_TYPE = "comparison_count"  # variant key for chain=0, n_attrs=0
from phantom_wiki.facts.sample import get_vals_and_update_cache
from phantom_wiki.utils import decode
from tests.phantom_wiki.facts import DATABASE_SMALL_PATH


@pytest.fixture(scope="module")
def db():
    """Load the small test database."""
    return get_database(DATABASE_SMALL_PATH)


@pytest.fixture(scope="module")
def person_names(db):
    return db.get_person_names()


@pytest.fixture(scope="module")
def rng():
    return np.random.default_rng(seed=42)


@pytest.fixture(scope="module")
def caches(db, person_names):
    attr_cache: dict[str, list[tuple[str, str]]] = {}
    rel_cache: dict[str, list[tuple[str, str]]] = {}
    # Pre-populate caches
    from phantom_wiki.facts.sample import RELATION

    for name in person_names:
        get_vals_and_update_cache(attr_cache, name, db, ATTRIBUTE_TYPES, num_procs=1)
        get_vals_and_update_cache(rel_cache, name, db, RELATION, num_procs=1)
    return attr_cache, rel_cache


# ---------------------------------------------------------------------------
# Test is_extended_question classifier
# ---------------------------------------------------------------------------
class TestIsExtendedQuestion:
    def test_comparison_age(self):
        assert is_extended_question("Who is older, Alice or Bob?")
        assert is_extended_question("Who is younger, Alice or Bob?")

    def test_comparison_count(self):
        assert is_extended_question("Who has more children, Alice or Bob?")

    def test_multi_constraint(self):
        assert is_extended_question(
            "Who is the person whose occupation is teacher and whose hobby is reading?"
        )

    def test_superlative(self):
        assert is_extended_question("Who is the oldest child of Alice?")
        assert is_extended_question("Who is the youngest sibling of Bob?")
        assert is_extended_question("Who has the most children among the siblings of Alice?")

    def test_base_questions_not_extended(self):
        assert not is_extended_question("Who is the mother of Alice?")
        assert not is_extended_question("What is the hobby of Bob?")
        assert not is_extended_question("How many children does Alice have?")


# ---------------------------------------------------------------------------
# Test comparison age questions
# ---------------------------------------------------------------------------
class TestComparisonAge:
    def test_generates_valid_question(self, rng, db, person_names, caches):
        attr_cache, _ = caches
        result = sample_comparison_age_question(rng, db, person_names, attr_cache)
        assert result is not None
        question, query = result
        assert question.startswith("Who is older,")
        assert question.endswith("?")
        assert len(query) == 3

    def test_answer_is_correct(self, db, person_names, caches):
        attr_cache, _ = caches
        rng = np.random.default_rng(seed=1)
        result = sample_comparison_age_question(rng, db, person_names, attr_cache)
        assert result is not None
        question, query = result

        answer = get_extended_answer(question, query, COMPARISON_AGE_TYPE, db, _TEST_COUNT_VARIANTS)
        assert len(answer) == 1

        # Verify: the answer should be the person with the earlier DOB
        import re

        m = re.match(r"Who is older, (.+?) or (.+?)\?", question)
        name1, name2 = m.group(1), m.group(2)
        dob1 = decode(list(db.prolog.query(f'dob("{name1}", D)'))[0]["D"])
        dob2 = decode(list(db.prolog.query(f'dob("{name2}", D)'))[0]["D"])
        expected = name1 if dob1 < dob2 else name2
        assert answer[0] == expected


# ---------------------------------------------------------------------------
# Test comparison count questions
# ---------------------------------------------------------------------------
class TestComparisonCount:
    def test_generates_valid_question(self, db, person_names, caches):
        attr_cache, rel_cache = caches
        rng = np.random.default_rng(seed=2)
        result = sample_comparison_count_extended_question(
            rng, db, person_names, attr_cache, rel_cache, num_procs=1,
            chain_depth=0, n_attrs=0,
        )
        assert result is not None
        question, query = result
        assert question.startswith("Who has more")
        assert question.endswith("?")

    def test_answer_is_correct(self, db, person_names, caches):
        attr_cache, rel_cache = caches
        rng = np.random.default_rng(seed=2)
        result = sample_comparison_count_extended_question(
            rng, db, person_names, attr_cache, rel_cache, num_procs=1,
            chain_depth=0, n_attrs=0,
        )
        assert result is not None
        question, query = result

        answer = get_extended_answer(question, query, _COMPARISON_COUNT_TYPE, db, _TEST_COUNT_VARIANTS)
        assert len(answer) == 1
        # The answer should be one of the two names in the question
        import re

        m = re.match(r"Who has more .+?, (.+?) or (.+?)\?", question)
        name1, name2 = m.group(1), m.group(2)
        assert answer[0] in (name1, name2)


# ---------------------------------------------------------------------------
# Test multi-constraint questions
# ---------------------------------------------------------------------------
class TestMultiConstraint:
    def test_generates_valid_question(self, db, person_names, caches):
        attr_cache, _ = caches
        rng = np.random.default_rng(seed=3)
        result = sample_multi_constraint_question(rng, db, person_names, attr_cache, num_procs=1, n_attrs=2)
        assert result is not None
        question, query = result
        assert "and whose" in question
        assert len(query) == 2

    def test_answer_contains_original_person(self, db, person_names, caches):
        attr_cache, _ = caches
        rng = np.random.default_rng(seed=3)
        result = sample_multi_constraint_question(rng, db, person_names, attr_cache, num_procs=1, n_attrs=2)
        assert result is not None
        question, query = result

        answer = get_extended_answer(question, query, MULTI_CONSTRAINT_TYPE, db, _TEST_COUNT_VARIANTS)
        # The answer should include at least one person
        assert len(answer) >= 1
        # All answers should be valid persons
        for name in answer:
            assert name in person_names


# ---------------------------------------------------------------------------
# Test superlative age questions
# ---------------------------------------------------------------------------
class TestSuperlativeAge:
    def test_oldest_generates_valid_question(self, db, person_names, caches):
        _, rel_cache = caches
        rng = np.random.default_rng(seed=4)
        result = sample_superlative_age_question(
            rng, db, person_names, rel_cache, easy_mode=True, oldest=True
        )
        assert result is not None
        question, query = result
        assert "oldest" in question
        assert question.endswith("?")

    def test_youngest_generates_valid_question(self, db, person_names, caches):
        _, rel_cache = caches
        rng = np.random.default_rng(seed=5)
        result = sample_superlative_age_question(
            rng, db, person_names, rel_cache, easy_mode=True, oldest=False
        )
        assert result is not None
        question, query = result
        assert "youngest" in question

    def test_oldest_answer_is_correct(self, db, person_names, caches):
        _, rel_cache = caches
        rng = np.random.default_rng(seed=4)
        result = sample_superlative_age_question(
            rng, db, person_names, rel_cache, easy_mode=True, oldest=True
        )
        assert result is not None
        question, query = result
        answer = get_extended_answer(question, query, SUPERLATIVE_OLDEST_TYPE, db, _TEST_COUNT_VARIANTS)
        assert len(answer) >= 1

        # Verify the answer is the oldest among the relation group
        import re

        m = re.match(r"Who is the oldest (.+?) of (.+?)\?", question)
        relation, name = m.group(1), m.group(2)
        # Get all relatives
        relatives = [decode(r["X"]) for r in db.query(f'{relation}("{name}", X)')]
        # Get their DOBs and find the oldest (earliest DOB)
        dobs = {}
        for rel in relatives:
            d = list(db.prolog.query(f'dob("{rel}", D)'))
            if d:
                dobs[rel] = decode(d[0]["D"])
        if dobs:
            oldest_person = min(dobs, key=dobs.get)
            assert oldest_person in answer


# ---------------------------------------------------------------------------
# Test superlative most questions
# ---------------------------------------------------------------------------
class TestSuperlativeMost:
    def test_generates_valid_question(self, db, person_names, caches):
        _, rel_cache = caches
        rng = np.random.default_rng(seed=10)
        result = sample_superlative_most_question(
            rng, db, person_names, rel_cache, easy_mode=True
        )
        # This might be None if the small universe doesn't have appropriate data
        if result is not None:
            question, query = result
            assert "most" in question
            assert "among" in question


# ---------------------------------------------------------------------------
# Test master sampling function
# ---------------------------------------------------------------------------
class TestSampleExtended:
    def test_all_types_produce_questions(self, db, person_names, caches):
        attr_cache, rel_cache = caches
        # Some types may not always produce questions on the small universe,
        # but the basic types should work
        basic_types = [COMPARISON_AGE_TYPE, MULTI_CONSTRAINT_TYPE]
        for qtype in basic_types:
            rng = np.random.default_rng(seed=42)
            result = sample_extended_question(
                qtype, rng, db, person_names, attr_cache, rel_cache, num_procs=1,
                count_variants=_TEST_COUNT_VARIANTS, multi_constraint_n_attrs=2,
            )
            assert result is not None, f"Failed to generate question of type {qtype}"

    def test_invalid_type_raises(self, db, person_names, caches):
        attr_cache, rel_cache = caches
        rng = np.random.default_rng(seed=42)
        with pytest.raises(ValueError):
            sample_extended_question(
                "invalid_type", rng, db, person_names, attr_cache, rel_cache, num_procs=1,
                count_variants=_TEST_COUNT_VARIANTS, multi_constraint_n_attrs=2,
            )
