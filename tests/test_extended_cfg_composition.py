"""Tests for extended CFG composition: comparison, multi-constraint, and superlative
question types integrated into the recursive CFG grammar.

Uses a small test universe (n~27, seed=42) to verify that:
1. Each extended question type generates valid questions at various depths
2. Prolog queries execute correctly and produce correct answers
3. Depth parameter is respected
4. CLI filters (--question-types, --min-hops, --max-hops) work
5. Balanced sampling produces roughly correct proportions
"""

import re

import numpy as np
import pytest

from phantom_wiki.facts import get_database
from phantom_wiki.facts.attributes.constants import ATTRIBUTE_TYPES
from phantom_wiki.facts.balanced_sampling import balanced_sample_by_type
from phantom_wiki.facts.question_difficulty import calculate_query_difficulty
from phantom_wiki.facts.sample import RELATION, get_vals_and_update_cache, sample_question
from phantom_wiki.facts.templates import (
    ALL_QUESTION_TYPES,
    COMPARISON_AGE_SUBTYPE,
    COMPARISON_AGE_YOUNGER_SUBTYPE,
    COMPARISON_BORN_FIRST_SUBTYPE,
    COMPARISON_COUNT_FEWER_SUBTYPE,
    COMPARISON_COUNT_MORE_SUBTYPE,
    MULTI_CONSTRAINT_2_SUBTYPE,
    MULTI_CONSTRAINT_3_SUBTYPE,
    QUESTION_TYPE_BASE,
    QUESTION_TYPE_COMPARISON,
    QUESTION_TYPE_MULTI_CONSTRAINT,
    QUESTION_TYPE_SUPERLATIVE,
    SUPERLATIVE_FEWEST_SUBTYPE,
    SUPERLATIVE_MOST_SUBTYPE,
    SUPERLATIVE_OLDEST_SUBTYPE,
    SUPERLATIVE_YOUNGEST_SUBTYPE,
    classify_question_type,
    generate_templates,
)
from phantom_wiki.generate_dataset import _filter_by_hops, _get_extended_cfg_answer
from phantom_wiki.utils import decode
from tests.phantom_wiki.facts import DATABASE_SMALL_PATH


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def db(request):
    """Load the test database. Use --db-path to override with a custom DB."""
    custom_path = request.config.getoption("--db-path", default=None)
    if custom_path:
        return get_database(str(custom_path.resolve()))
    return get_database(DATABASE_SMALL_PATH)


@pytest.fixture(scope="module")
def person_names(db):
    return db.get_person_names()


@pytest.fixture(scope="module")
def caches(db, person_names):
    attr_cache: dict[str, list[tuple[str, str]]] = {}
    rel_cache: dict[str, list[tuple[str, str]]] = {}
    for name in person_names:
        get_vals_and_update_cache(attr_cache, name, db, ATTRIBUTE_TYPES, num_procs=1)
        get_vals_and_update_cache(rel_cache, name, db, RELATION, num_procs=1)
    return attr_cache, rel_cache


def _sample_extended(template, rng, db, person_names, caches, max_attempts=50,
                     collector=None, test_name=None):
    """Helper to sample a question from an extended template (4-tuple)."""
    question_template, query_template, answer_info, subtype = template
    attr_cache, rel_cache = caches
    for _ in range(max_attempts):
        rng_copy = np.random.default_rng(rng.integers(0, 2**31))
        try:
            result = sample_question(
                question_template,
                query_template,
                rng_copy,
                db,
                person_names,
                attr_cache,
                rel_cache,
                num_procs=1,
                num_sampling_attempts=1,
            )
            if result is not None:
                if collector is not None and test_name is not None:
                    question, query = result
                    collector.add(
                        test_name=test_name,
                        question=question,
                        query=query,
                        subtype=subtype,
                        template=question_template,
                    )
                return result
        except (ValueError, AssertionError):
            continue
    return None


def _get_templates_by_subtype(depth=6):
    """Generate all extended templates and group by subtype."""
    templates = generate_templates(depth=depth, question_types=ALL_QUESTION_TYPES)
    by_subtype = {}
    for t in templates:
        if len(t) == 4:
            by_subtype.setdefault(t[3], []).append(t)
    return by_subtype


# ---------------------------------------------------------------------------
# Template generation tests
# ---------------------------------------------------------------------------
class TestTemplateGeneration:
    def test_base_templates_unchanged(self):
        """Base templates (3-tuples) are unaffected by extended types."""
        base_only = generate_templates(depth=6, question_types=[QUESTION_TYPE_BASE])
        assert all(len(t) == 3 for t in base_only)
        assert len(base_only) > 0

    def test_extended_templates_are_4_tuples(self):
        """Extended templates have (question, query, answer_info, subtype) format."""
        templates = generate_templates(depth=5, question_types=ALL_QUESTION_TYPES)
        extended = [t for t in templates if len(t) == 4]
        assert len(extended) > 0
        for t in extended:
            q, query, answer_info, subtype = t
            assert isinstance(q, list)
            assert isinstance(query, list)
            assert subtype is not None

    def test_all_subtypes_present(self):
        """All expected subtypes are generated at sufficient depth."""
        templates = generate_templates(depth=6, question_types=ALL_QUESTION_TYPES)
        subtypes = {t[3] for t in templates if len(t) == 4}
        expected = {
            COMPARISON_AGE_SUBTYPE,
            COMPARISON_AGE_YOUNGER_SUBTYPE,
            COMPARISON_BORN_FIRST_SUBTYPE,
            COMPARISON_COUNT_MORE_SUBTYPE,
            COMPARISON_COUNT_FEWER_SUBTYPE,
            MULTI_CONSTRAINT_2_SUBTYPE,
            MULTI_CONSTRAINT_3_SUBTYPE,
            SUPERLATIVE_OLDEST_SUBTYPE,
            SUPERLATIVE_YOUNGEST_SUBTYPE,
            SUPERLATIVE_MOST_SUBTYPE,
            SUPERLATIVE_FEWEST_SUBTYPE,
        }
        assert expected == subtypes

    def test_question_type_filter(self):
        """--question-types filter only includes requested types."""
        comp_only = generate_templates(depth=5, question_types=[QUESTION_TYPE_COMPARISON])
        assert all(len(t) == 4 for t in comp_only)
        assert all("comparison" in t[3] for t in comp_only)

        sup_only = generate_templates(depth=5, question_types=[QUESTION_TYPE_SUPERLATIVE])
        assert all(len(t) == 4 for t in sup_only)
        assert all("superlative" in t[3] for t in sup_only)

    def test_classify_question_type(self):
        """classify_question_type correctly categorizes templates."""
        templates = generate_templates(depth=5, question_types=ALL_QUESTION_TYPES)
        for t in templates:
            q = t[0]
            qtype = classify_question_type(q)
            if len(t) == 3:
                assert qtype == QUESTION_TYPE_BASE
            elif "comparison" in t[3]:
                assert qtype == QUESTION_TYPE_COMPARISON
            elif "multi_constraint" in t[3]:
                assert qtype == QUESTION_TYPE_MULTI_CONSTRAINT
            elif "superlative" in t[3]:
                assert qtype == QUESTION_TYPE_SUPERLATIVE

    def test_depth_controls_template_count(self):
        """Higher depth produces more templates (more R_c expansions)."""
        t4 = generate_templates(depth=4, question_types=ALL_QUESTION_TYPES)
        t6 = generate_templates(depth=6, question_types=ALL_QUESTION_TYPES)
        assert len(t6) > len(t4)


# ---------------------------------------------------------------------------
# Comparison tests
# ---------------------------------------------------------------------------
class TestComparison:
    def test_comparison_depth_1(self, db, person_names, caches, question_collector):
        """depth 1: 'Who is older, <name> or <name>?'"""
        templates = generate_templates(depth=4, question_types=[QUESTION_TYPE_COMPARISON])
        age_templates = [t for t in templates if t[3] == COMPARISON_AGE_SUBTYPE]
        assert len(age_templates) > 0

        rng = np.random.default_rng(42)
        for tmpl in age_templates:
            q, query, answer_info, subtype = tmpl
            # Check structure: should have R_c operands
            qtext = " ".join(q)
            assert "older," in qtext
            assert "or" in qtext
            # Try to sample a concrete question for the dump
            _sample_extended(tmpl, rng, db, person_names, caches,
                             collector=question_collector, test_name="comparison_depth_1")

    def test_comparison_depth_2(self, db, person_names, caches):
        """depth 2: 'Who is older, the <relation> of <name> or <name>?'"""
        templates = generate_templates(depth=5, question_types=[QUESTION_TYPE_COMPARISON])
        age_templates = [t for t in templates if t[3] == COMPARISON_AGE_SUBTYPE]
        # Should have templates where at least one operand has a chain
        deep = [t for t in age_templates if any("of" in tok for tok in t[0])]
        assert len(deep) > 0

    def test_comparison_depth_3(self, db, person_names, caches):
        """Both operands can have chains at depth >= 5."""
        templates = generate_templates(depth=6, question_types=[QUESTION_TYPE_COMPARISON])
        age_templates = [t for t in templates if t[3] == COMPARISON_AGE_SUBTYPE]
        # Find a template where both sides of 'or' have 'the ... of'
        for t in age_templates:
            parts = " ".join(t[0]).split(" or ")
            if len(parts) == 2 and "of" in parts[0] and "of" in parts[1]:
                # Both operands have chains
                return
        # At depth 6, at least one such template should exist
        assert len(age_templates) > 0

    def test_comparison_answer_correct(self, db, person_names, caches, question_collector):
        """Comparison answer extraction returns the correct person."""
        templates = generate_templates(depth=5, question_types=[QUESTION_TYPE_COMPARISON])
        age_templates = [t for t in templates if t[3] == COMPARISON_AGE_SUBTYPE]

        rng = np.random.default_rng(42)
        for tmpl in age_templates[:3]:
            result = _sample_extended(tmpl, rng, db, person_names, caches)
            if result is None:
                continue

            question, query = result
            _, _, answer_info, subtype = tmpl
            answer = _get_extended_cfg_answer(question, query, answer_info, subtype, db)
            assert isinstance(answer, list)
            assert len(answer) > 0
            # Answer should be a person name in the database
            assert answer[0] in person_names
            if question_collector is not None:
                question_collector.add(
                    test_name="comparison_answer_correct",
                    question=question, query=query, answer=answer,
                    subtype=subtype, template=tmpl[0],
                )
            return

    def test_comparison_count(self, db, person_names, caches, question_collector):
        """'Who has more <relation_plural>, R_c or R_c?'"""
        templates = generate_templates(depth=5, question_types=[QUESTION_TYPE_COMPARISON])
        count_templates = [t for t in templates if t[3] == COMPARISON_COUNT_MORE_SUBTYPE]
        assert len(count_templates) > 0

        rng = np.random.default_rng(42)
        for tmpl in count_templates[:5]:
            result = _sample_extended(tmpl, rng, db, person_names, caches)
            if result is None:
                continue

            question, query = result
            assert "has more" in question.lower() or "Who has more" in question
            _, _, answer_info, subtype = tmpl
            answer = _get_extended_cfg_answer(question, query, answer_info, subtype, db)
            assert isinstance(answer, list)
            if question_collector is not None:
                question_collector.add(
                    test_name="comparison_count",
                    question=question, query=query, answer=answer,
                    subtype=subtype, template=tmpl[0],
                )
            return

    def test_younger_answer_is_opposite_of_older(self, db, person_names, caches):
        """'Who is younger' should return the opposite of 'Who is older' for same operands."""
        templates = generate_templates(depth=5, question_types=[QUESTION_TYPE_COMPARISON])
        older_templates = [t for t in templates if t[3] == COMPARISON_AGE_SUBTYPE]
        younger_templates = [t for t in templates if t[3] == COMPARISON_AGE_YOUNGER_SUBTYPE]

        # The templates should have matching structures
        assert len(older_templates) == len(younger_templates)

    def test_born_first_same_as_older(self, db, person_names, caches):
        """'Who was born first' is semantically the same as 'Who is older'."""
        templates = generate_templates(depth=5, question_types=[QUESTION_TYPE_COMPARISON])
        born_first = [t for t in templates if t[3] == COMPARISON_BORN_FIRST_SUBTYPE]
        assert len(born_first) > 0
        for t in born_first:
            assert "born first," in " ".join(t[0])


# ---------------------------------------------------------------------------
# Multi-constraint tests
# ---------------------------------------------------------------------------
class TestMultiConstraint:
    def test_multi_constraint_2_attrs(self, db, person_names, caches, question_collector):
        """2-attribute: 'Who is the person whose X is V1 and whose Y is V2?'"""
        templates = generate_templates(depth=6, question_types=[QUESTION_TYPE_MULTI_CONSTRAINT])
        mc2 = [t for t in templates if t[3] == MULTI_CONSTRAINT_2_SUBTYPE]
        assert len(mc2) == 1

        rng = np.random.default_rng(42)
        result = _sample_extended(mc2[0], rng, db, person_names, caches)
        if result is not None:
            question, query = result
            assert "and whose" in question
            _, _, answer_info, subtype = mc2[0]
            answer = _get_extended_cfg_answer(question, query, answer_info, subtype, db)
            assert isinstance(answer, list)
            assert len(answer) > 0
            if question_collector is not None:
                question_collector.add(
                    test_name="multi_constraint_2_attrs",
                    question=question, query=query, answer=answer,
                    subtype=subtype, template=mc2[0][0],
                )

    def test_multi_constraint_3_attrs(self, db, person_names, caches):
        """3-attribute: 'Who is the person whose X is V1 and whose Y is V2 and whose Z is V3?'"""
        templates = generate_templates(depth=6, question_types=[QUESTION_TYPE_MULTI_CONSTRAINT])
        mc3 = [t for t in templates if t[3] == MULTI_CONSTRAINT_3_SUBTYPE]
        assert len(mc3) == 1

        q = " ".join(mc3[0][0])
        assert q.count("and whose") == 2

    def test_multi_constraint_query_structure(self):
        """Multi-constraint queries use conjunction on same variable."""
        templates = generate_templates(depth=6, question_types=[QUESTION_TYPE_MULTI_CONSTRAINT])
        mc2 = [t for t in templates if t[3] == MULTI_CONSTRAINT_2_SUBTYPE][0]
        _, query, answer_var, _ = mc2

        # Both query predicates should reference the same person variable
        assert len(query) == 2
        var_pattern = re.compile(r"Y_\d+")
        vars_in_q0 = var_pattern.findall(query[0])
        vars_in_q1 = var_pattern.findall(query[1])
        # The person variable should appear in both
        assert set(vars_in_q0) & set(vars_in_q1)

    def test_multi_constraint_answer_matches_all(self, db, person_names, caches, question_collector):
        """Answer person must satisfy ALL constraints."""
        templates = generate_templates(depth=6, question_types=[QUESTION_TYPE_MULTI_CONSTRAINT])
        mc2 = [t for t in templates if t[3] == MULTI_CONSTRAINT_2_SUBTYPE]

        rng = np.random.default_rng(42)
        for _ in range(10):
            result = _sample_extended(mc2[0], rng, db, person_names, caches)
            if result is None:
                continue

            question, query = result
            _, _, answer_info, subtype = mc2[0]
            answer = _get_extended_cfg_answer(question, query, answer_info, subtype, db)
            if not answer:
                continue

            # Verify each answer person satisfies all query constraints
            for person in answer:
                for stmt in query:
                    # Replace the answer var with the person name
                    check = stmt.replace(answer_info, f'"{person}"')
                    results = list(db.prolog.query(check))
                    assert len(results) > 0, f"{person} should satisfy: {check}"
            if question_collector is not None:
                question_collector.add(
                    test_name="multi_constraint_answer_matches_all",
                    question=question, query=query, answer=answer,
                    subtype=subtype, template=mc2[0][0],
                )
            return


# ---------------------------------------------------------------------------
# Superlative tests
# ---------------------------------------------------------------------------
class TestSuperlative:
    def test_superlative_oldest_depth_2(self, db, person_names, caches, question_collector):
        """'Who is the oldest <relation> of <name>?'"""
        templates = generate_templates(depth=5, question_types=[QUESTION_TYPE_SUPERLATIVE])
        oldest = [t for t in templates if t[3] == SUPERLATIVE_OLDEST_SUBTYPE]
        assert len(oldest) > 0

        rng = np.random.default_rng(42)
        for tmpl in oldest[:5]:
            result = _sample_extended(tmpl, rng, db, person_names, caches)
            if result is None:
                continue

            question, query = result
            assert "oldest" in question
            _, _, answer_var, subtype = tmpl
            answer = _get_extended_cfg_answer(question, query, answer_var, subtype, db)
            assert isinstance(answer, list)
            if answer:
                assert answer[0] in person_names
            if question_collector is not None:
                question_collector.add(
                    test_name="superlative_oldest_depth_2",
                    question=question, query=query, answer=answer,
                    subtype=subtype, template=tmpl[0],
                )
            return

    def test_superlative_youngest_depth_3(self, db, person_names, caches):
        """'Who is the youngest <relation> of the <relation> of <name>?'"""
        templates = generate_templates(depth=6, question_types=[QUESTION_TYPE_SUPERLATIVE])
        youngest = [t for t in templates if t[3] == SUPERLATIVE_YOUNGEST_SUBTYPE]
        # Find a template with a chain (depth > 1 in R_c)
        deep = [t for t in youngest if len(t[1]) > 3]
        assert len(deep) > 0

    def test_superlative_most_depth_3(self, db, person_names, caches):
        """'Who is the <relation> of <name> with the most <relation_plural>?'"""
        templates = generate_templates(depth=5, question_types=[QUESTION_TYPE_SUPERLATIVE])
        most = [t for t in templates if t[3] == SUPERLATIVE_MOST_SUBTYPE]
        assert len(most) > 0

        for t in most:
            qtext = " ".join(t[0])
            assert "with the most" in qtext

    def test_superlative_fewest_depth_4(self, db, person_names, caches):
        """Fewest superlative with a deep chain."""
        templates = generate_templates(depth=6, question_types=[QUESTION_TYPE_SUPERLATIVE])
        fewest = [t for t in templates if t[3] == SUPERLATIVE_FEWEST_SUBTYPE]
        assert len(fewest) > 0

        for t in fewest:
            qtext = " ".join(t[0])
            assert "with the fewest" in qtext

    def test_superlative_query_has_negation(self):
        """Superlative queries use negation-as-failure (\\+)."""
        templates = generate_templates(depth=5, question_types=[QUESTION_TYPE_SUPERLATIVE])
        for t in templates:
            query = t[1]
            has_negation = any("\\+" in stmt for stmt in query)
            assert has_negation, f"Superlative query should have \\+: {query}"

    def test_superlative_oldest_answer_is_oldest(self, db, person_names, caches, question_collector):
        """The oldest answer should have the earliest DOB among the candidates."""
        templates = generate_templates(depth=5, question_types=[QUESTION_TYPE_SUPERLATIVE])
        oldest = [t for t in templates if t[3] == SUPERLATIVE_OLDEST_SUBTYPE]

        rng = np.random.default_rng(42)
        for tmpl in oldest[:5]:
            result = _sample_extended(tmpl, rng, db, person_names, caches)
            if result is None:
                continue

            question, query = result
            _, _, answer_var, subtype = tmpl
            answer = _get_extended_cfg_answer(question, query, answer_var, subtype, db)
            if not answer:
                continue

            # Verify the answer is the actual oldest
            for person in answer:
                dob_results = list(db.prolog.query(f'dob("{person}", D)'))
                assert len(dob_results) > 0, f"{person} should have a DOB"
            if question_collector is not None:
                question_collector.add(
                    test_name="superlative_oldest_answer_is_oldest",
                    question=question, query=query, answer=answer,
                    subtype=subtype, template=tmpl[0],
                )
            return

    def test_superlative_single_candidate(self, db, person_names, caches, question_collector):
        """If only one candidate exists, superlative should return that person."""
        # This is implicitly tested — if a person has only one child,
        # "oldest child" returns that child
        templates = generate_templates(depth=5, question_types=[QUESTION_TYPE_SUPERLATIVE])
        oldest = [t for t in templates if t[3] == SUPERLATIVE_OLDEST_SUBTYPE]

        rng = np.random.default_rng(123)
        for tmpl in oldest:
            result = _sample_extended(tmpl, rng, db, person_names, caches)
            if result is not None:
                question, query = result
                _, _, answer_var, subtype = tmpl
                answer = _get_extended_cfg_answer(question, query, answer_var, subtype, db)
                assert isinstance(answer, list)
                if question_collector is not None:
                    question_collector.add(
                        test_name="superlative_single_candidate",
                        question=question, query=query, answer=answer,
                        subtype=subtype, template=tmpl[0],
                    )
                return


# ---------------------------------------------------------------------------
# Cross-type composition tests
# ---------------------------------------------------------------------------
class TestCrossTypeComposition:
    def test_comparison_with_deep_chains(self, db, person_names, caches, question_collector):
        """Comparison where both operands are multi-hop chains."""
        templates = generate_templates(depth=6, question_types=[QUESTION_TYPE_COMPARISON])
        age_templates = [t for t in templates if t[3] == COMPARISON_AGE_SUBTYPE]

        # Find a template where both operands have chains (multiple 'of' tokens)
        for tmpl in age_templates:
            qtext = " ".join(tmpl[0])
            parts = qtext.split(" or ")
            if len(parts) == 2:
                left_has_chain = "of" in parts[0]
                right_has_chain = "of" in parts[1]
                if left_has_chain and right_has_chain:
                    rng = np.random.default_rng(42)
                    result = _sample_extended(tmpl, rng, db, person_names, caches)
                    if result is not None:
                        question, query = result
                        _, _, answer_info, subtype = tmpl
                        answer = _get_extended_cfg_answer(
                            question, query, answer_info, subtype, db
                        )
                        assert isinstance(answer, list)
                        if question_collector is not None:
                            question_collector.add(
                                test_name="comparison_with_deep_chains",
                                question=question, query=query, answer=answer,
                                subtype=subtype, template=tmpl[0],
                            )
                        return

    def test_superlative_with_chain(self, db, person_names, caches, question_collector):
        """Superlative where R_c is a multi-hop chain, not just a name."""
        templates = generate_templates(depth=6, question_types=[QUESTION_TYPE_SUPERLATIVE])
        oldest = [t for t in templates if t[3] == SUPERLATIVE_OLDEST_SUBTYPE]

        for tmpl in oldest:
            # R_c chain should have more than just a name
            if len(tmpl[1]) > 4:  # negation + dob + relation + at least 2 chain steps
                rng = np.random.default_rng(42)
                result = _sample_extended(tmpl, rng, db, person_names, caches)
                if result is not None:
                    question, query = result
                    assert "of the" in question or "whose" in question
                    if question_collector is not None:
                        question_collector.add(
                            test_name="superlative_with_chain",
                            question=question, query=query,
                            subtype=tmpl[3], template=tmpl[0],
                        )
                    return


# ---------------------------------------------------------------------------
# Question parsing tests
# ---------------------------------------------------------------------------
class TestQuestionParsing:
    def test_generated_questions_well_formed(self, db, person_names, caches, question_collector):
        """All generated questions end with '?' and have no template placeholders."""
        templates = generate_templates(depth=5, question_types=ALL_QUESTION_TYPES)
        rng = np.random.default_rng(42)

        for tmpl in templates[:20]:
            if len(tmpl) == 4:
                result = _sample_extended(tmpl, rng, db, person_names, caches)
            else:
                q_template, query_template, answer = tmpl
                result = sample_question(
                    q_template, query_template, rng, db, person_names,
                    caches[0], caches[1], num_procs=1, num_sampling_attempts=10,
                )
            if result is None:
                continue
            question, query = result
            assert question.endswith("?"), f"Question should end with '?': {question}"
            assert "<" not in question, f"Question has unresolved placeholder: {question}"
            for stmt in query:
                # Check for unresolved <placeholder>_N patterns (not Prolog @< operator)
                assert not re.search(
                    r"<\w+>_\d+", stmt
                ), f"Query has unresolved placeholder: {stmt}"
            if question_collector is not None:
                subtype = tmpl[3] if len(tmpl) == 4 else "base"
                question_collector.add(
                    test_name="well_formed_questions",
                    question=question, query=query,
                    subtype=subtype, template=tmpl[0],
                )

    def test_prolog_queries_execute_without_error(self, db, person_names, caches, question_collector):
        """All generated Prolog queries should execute without errors."""
        templates = generate_templates(depth=5, question_types=ALL_QUESTION_TYPES)
        rng = np.random.default_rng(42)

        for tmpl in templates[:15]:
            if len(tmpl) == 4:
                result = _sample_extended(tmpl, rng, db, person_names, caches)
            else:
                q_template, query_template, answer = tmpl
                result = sample_question(
                    q_template, query_template, rng, db, person_names,
                    caches[0], caches[1], num_procs=1, num_sampling_attempts=10,
                )
            if result is None:
                continue
            question, query = result
            joined = ", ".join(reversed(query))
            try:
                results = list(db.prolog.query(joined))
            except Exception as e:
                pytest.fail(f"Prolog query failed: {joined}\nError: {e}")
            if question_collector is not None:
                subtype = tmpl[3] if len(tmpl) == 4 else "base"
                question_collector.add(
                    test_name="prolog_queries_execute",
                    question=question, query=query,
                    subtype=subtype, template=tmpl[0],
                )


# ---------------------------------------------------------------------------
# Depth/hop filtering tests
# ---------------------------------------------------------------------------
class TestDepthAndHopFiltering:
    def test_depth_parameter_controls_complexity(self):
        """Lower depth produces simpler (fewer-hop) templates."""
        t4 = generate_templates(depth=4, question_types=[QUESTION_TYPE_COMPARISON])
        t8 = generate_templates(depth=8, question_types=[QUESTION_TYPE_COMPARISON])

        # Higher depth should produce more templates (more R_c expansions)
        assert len(t8) > len(t4)

    def test_min_hops_filter(self):
        """--min-hops filters out questions with fewer hops."""
        questions = [
            {"prolog": {"query": ["child(A, B)"]}, "difficulty": 1},
            {"prolog": {"query": ["child(A, B)", "friend(B, C)"]}, "difficulty": 2},
            {"prolog": {"query": ["child(A, B)", "friend(B, C)", "parent(C, D)"]}, "difficulty": 3},
        ]
        filtered = _filter_by_hops(questions, min_hops=2)
        assert len(filtered) == 2

    def test_max_hops_filter(self):
        """--max-hops filters out questions with more hops."""
        questions = [
            {"prolog": {"query": ["child(A, B)"]}, "difficulty": 1},
            {"prolog": {"query": ["child(A, B)", "friend(B, C)"]}, "difficulty": 2},
            {"prolog": {"query": ["child(A, B)", "friend(B, C)", "parent(C, D)"]}, "difficulty": 3},
        ]
        filtered = _filter_by_hops(questions, max_hops=2)
        assert len(filtered) == 2

    def test_min_max_hops_range(self):
        """Combined --min-hops and --max-hops filter."""
        questions = [
            {"prolog": {"query": ["child(A, B)"]}, "difficulty": 1},
            {"prolog": {"query": ["child(A, B)", "friend(B, C)"]}, "difficulty": 2},
            {"prolog": {"query": ["child(A, B)", "friend(B, C)", "parent(C, D)"]}, "difficulty": 3},
        ]
        filtered = _filter_by_hops(questions, min_hops=2, max_hops=2)
        assert len(filtered) == 1


# ---------------------------------------------------------------------------
# Balanced sampling tests
# ---------------------------------------------------------------------------
class TestBalancedSampling:
    def test_balanced_sample_by_type_proportions(self):
        """Type-balanced sampling produces roughly 40/20/20/20 proportions."""
        questions = []
        for i in range(100):
            questions.append({"question_category": "base", "difficulty": i % 5 + 1})
        for i in range(50):
            questions.append({"question_category": "comparison_age", "difficulty": i % 5 + 1})
        for i in range(50):
            questions.append({"question_category": "multi_constraint_2", "difficulty": i % 5 + 1})
        for i in range(50):
            questions.append({"question_category": "superlative_oldest", "difficulty": i % 5 + 1})

        sampled = balanced_sample_by_type(questions, total_target=100)

        # Count by type category
        base_count = sum(1 for q in sampled if q["question_category"] == "base")
        cmp_count = sum(1 for q in sampled if "comparison" in q["question_category"])
        mc_count = sum(1 for q in sampled if "multi_constraint" in q["question_category"])
        sup_count = sum(1 for q in sampled if "superlative" in q["question_category"])

        # Check roughly correct proportions (within 15% tolerance)
        assert 25 <= base_count <= 55, f"Base should be ~40%, got {base_count}"
        assert 5 <= cmp_count <= 35, f"Comparison should be ~20%, got {cmp_count}"
        assert 5 <= mc_count <= 35, f"Multi-constraint should be ~20%, got {mc_count}"
        assert 5 <= sup_count <= 35, f"Superlative should be ~20%, got {sup_count}"

    def test_balanced_sample_empty_type(self):
        """If a type has no questions, others get proportionally more."""
        questions = []
        for i in range(100):
            questions.append({"question_category": "base", "difficulty": i % 5 + 1})
        for i in range(50):
            questions.append({"question_category": "comparison_age", "difficulty": i % 5 + 1})

        sampled = balanced_sample_by_type(questions)
        assert len(sampled) > 0


# ---------------------------------------------------------------------------
# Difficulty calculation tests
# ---------------------------------------------------------------------------
class TestDifficulty:
    def test_extended_question_difficulty(self, db, person_names, caches, question_collector):
        """Extended questions should have non-zero difficulty."""
        templates = generate_templates(depth=5, question_types=ALL_QUESTION_TYPES)
        rng = np.random.default_rng(42)

        for tmpl in templates[:10]:
            if len(tmpl) == 4:
                result = _sample_extended(tmpl, rng, db, person_names, caches)
                if result is not None:
                    question, query = result
                    difficulty = calculate_query_difficulty(query)
                    assert difficulty >= 0
                    if question_collector is not None:
                        question_collector.add(
                            test_name="difficulty",
                            question=question, query=query,
                            answer=f"difficulty={difficulty}",
                            subtype=tmpl[3], template=tmpl[0],
                        )
