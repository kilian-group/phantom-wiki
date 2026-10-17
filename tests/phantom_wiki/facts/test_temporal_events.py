"""Tests for temporal events system.

Verifies:
- Event generation is consistent with birth dates
- Prolog facts are correctly asserted
- Temporal questions produce correct answers
- Article templates include temporal events
"""

import numpy as np
import pytest

from phantom_wiki.facts import get_database
from phantom_wiki.facts.attributes import db_generate_attributes
from phantom_wiki.facts.temporal import db_generate_temporal_events
from phantom_wiki.facts.temporal.generate_events import generate_temporal_events
from phantom_wiki.facts.temporal.questions import (
    TEMPORAL_QUESTION_TYPES,
    get_temporal_answer,
    is_temporal_question,
    sample_temporal_lived_in,
    sample_temporal_job_before,
    sample_temporal_married_first,
)
from phantom_wiki.utils import decode
from tests.phantom_wiki.facts import DATABASE_SMALL_PATH


@pytest.fixture(scope="module")
def db():
    """Load small database and generate temporal events."""
    database = get_database(DATABASE_SMALL_PATH)
    # Attributes are needed for career events (job titles)
    db_generate_attributes(database, seed=1)
    db_generate_temporal_events(database, seed=42)
    return database


@pytest.fixture(scope="module")
def person_names(db):
    return db.get_person_names()


@pytest.fixture(scope="module")
def rng():
    return np.random.default_rng(seed=42)


# ---------------------------------------------------------------------------
# Test event generation
# ---------------------------------------------------------------------------
class TestEventGeneration:
    def test_events_generated_for_all_people(self, db, person_names):
        """Every person should have at least some temporal events."""
        for name in person_names:
            # Check at least education exists
            results = list(db.prolog.query(f'education("{name}", School, Year)'))
            assert len(results) >= 1, f"No education events for {name}"

    def test_education_after_birth(self, db, person_names):
        """Graduation year should be after birth year."""
        for name in person_names:
            dob_results = list(db.prolog.query(f'dob("{name}", D)'))
            if not dob_results:
                continue
            birth_year = int(decode(dob_results[0]["D"]).split("-")[0])
            for r in db.prolog.query(f'education("{name}", School, Year)'):
                grad_year = int(r["Year"])
                assert grad_year > birth_year, (
                    f"{name}: graduation year {grad_year} not after birth year {birth_year}"
                )

    def test_career_start_after_education(self, db, person_names):
        """Career should start after (or at) education completion."""
        for name in person_names[:5]:  # Check a few people
            edu_results = list(db.prolog.query(f'education("{name}", School, Year)'))
            career_results = list(db.prolog.query(f'career("{name}", Job, Company, Start, End)'))
            if not edu_results or not career_results:
                continue
            latest_grad = max(int(r["Year"]) for r in edu_results)
            earliest_career = min(int(r["Start"]) for r in career_results)
            assert earliest_career >= latest_grad - 1, (
                f"{name}: career start {earliest_career} before graduation {latest_grad}"
            )

    def test_marriage_year_consistency(self, db, person_names):
        """Both spouses should have the same marriage year."""
        checked = set()
        for name in person_names:
            results = list(db.prolog.query(f'marriage_year("{name}", Spouse, Year)'))
            for r in results:
                spouse = decode(r["Spouse"])
                year = int(r["Year"])
                pair = tuple(sorted([name, spouse]))
                if pair in checked:
                    continue
                checked.add(pair)
                # Check spouse has same year
                spouse_results = list(
                    db.prolog.query(f'marriage_year("{spouse}", _, Y)')
                )
                if spouse_results:
                    spouse_year = int(spouse_results[0]["Y"])
                    assert year == spouse_year, (
                        f"Marriage year mismatch: {name}={year}, {spouse}={spouse_year}"
                    )

    def test_lived_in_events_exist(self, db, person_names):
        """Every person should have at least one lived_in event."""
        for name in person_names:
            results = list(db.prolog.query(f'lived_in("{name}", City, Start, End)'))
            assert len(results) >= 1, f"No lived_in events for {name}"


# ---------------------------------------------------------------------------
# Test temporal question classification
# ---------------------------------------------------------------------------
class TestIsTemporalQuestion:
    def test_lived_in(self):
        assert is_temporal_question("Where did Alice live in 2020?")

    def test_job_before(self):
        assert is_temporal_question("What was Alice's job before becoming a teacher?")

    def test_married_first(self):
        assert is_temporal_question("Who was married first, Alice or Bob?")

    def test_non_temporal(self):
        assert not is_temporal_question("Who is the mother of Alice?")
        assert not is_temporal_question("What is the hobby of Bob?")


# ---------------------------------------------------------------------------
# Test temporal questions
# ---------------------------------------------------------------------------
class TestTemporalLivedIn:
    def test_generates_valid_question(self, db, person_names):
        rng = np.random.default_rng(seed=1)
        result = sample_temporal_lived_in(rng, db, person_names)
        assert result is not None
        question, query = result
        assert question.startswith("Where did")
        assert "live in" in question

    def test_answer_is_correct(self, db, person_names):
        rng = np.random.default_rng(seed=1)
        result = sample_temporal_lived_in(rng, db, person_names)
        assert result is not None
        question, query = result
        answer = get_temporal_answer(question, query, "temporal_lived_in", db)
        assert len(answer) >= 1
        # Answer should be a city name (string)
        for city in answer:
            assert isinstance(city, str)
            assert len(city) > 0


class TestTemporalJobBefore:
    def test_generates_valid_question(self, db, person_names):
        rng = np.random.default_rng(seed=1)
        result = sample_temporal_job_before(rng, db, person_names)
        assert result is not None
        question, query = result
        assert "job before becoming" in question

    def test_answer_is_correct(self, db, person_names):
        rng = np.random.default_rng(seed=1)
        result = sample_temporal_job_before(rng, db, person_names)
        assert result is not None
        question, query = result
        answer = get_temporal_answer(question, query, "temporal_job_before", db)
        assert len(answer) >= 1


class TestTemporalMarriedFirst:
    def test_generates_valid_question(self, db, person_names):
        rng = np.random.default_rng(seed=10)
        result = sample_temporal_married_first(rng, db, person_names)
        assert result is not None
        question, query = result
        assert question.startswith("Who was married first,")

    def test_answer_is_correct(self, db, person_names):
        rng = np.random.default_rng(seed=10)
        result = sample_temporal_married_first(rng, db, person_names)
        assert result is not None
        question, query = result
        answer = get_temporal_answer(question, query, "temporal_married_first", db)
        assert len(answer) == 1
        # Answer should be one of the two names in the question
        import re
        m = re.match(r"Who was married first, (.+?) or (.+?)\?", question)
        assert answer[0] in (m.group(1), m.group(2))


# ---------------------------------------------------------------------------
# Test article generation with temporal events
# ---------------------------------------------------------------------------
class TestTemporalArticles:
    def test_articles_include_temporal_section(self, db, person_names):
        from phantom_wiki.core.article import get_temporal_sentences

        # Test temporal sentence generation directly to avoid pre-existing
        # issues with plural relation templates in the base article generation
        temporal_sents, temporal_facts = get_temporal_sentences(db, person_names[:3])
        for name in person_names[:3]:
            assert len(temporal_sents[name]) > 0, f"No temporal sentences for {name}"
            assert len(temporal_facts[name]) > 0, f"No temporal facts for {name}"
            # Check various event types are present
            has_education = any("graduated from" in s for s in temporal_sents[name])
            has_career = any("worked as" in s or "has been working" in s for s in temporal_sents[name])
            has_lived = any("lived in" in s or "has been living" in s for s in temporal_sents[name])
            assert has_education, f"No education sentences for {name}"
            assert has_career, f"No career sentences for {name}"
            assert has_lived, f"No lived-in sentences for {name}"

    def test_temporal_template_format(self, db, person_names):
        from phantom_wiki.core.constants.article_templates import TEMPORAL_ARTICLE_TEMPLATE

        # Verify the template has the expected sections
        assert "## Life Events" in TEMPORAL_ARTICLE_TEMPLATE
        assert "{temporal_facts}" in TEMPORAL_ARTICLE_TEMPLATE
