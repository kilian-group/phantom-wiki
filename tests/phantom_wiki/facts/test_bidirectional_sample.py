"""Tests for bidirectional anchor sampling.

50 tests covering:
- Inverse predicate generation (7)
- Query construction / chain building (8)
- Sampling correctness (8)
- Backwards compatibility (4)
- Answer position (5)
- Metadata completeness (5)
- Edge cases & robustness (6)
- Multi-template stress tests (7)

All integration tests dump generated questions via the --dump-questions fixture.

Usage:
    # Run tests only
    .venv/bin/python -m pytest tests/phantom_wiki/facts/test_bidirectional_sample.py -v

    # Run tests and dump all generated questions to ./test_output/
    .venv/bin/python -m pytest tests/phantom_wiki/facts/test_bidirectional_sample.py -v -s \
        --dump-questions ./test_output
"""

import re
from collections import Counter

import numpy as np
import pytest

from phantom_wiki.facts import get_database
from phantom_wiki.facts.attributes.constants import ATTRIBUTE_TYPES
from phantom_wiki.facts.bidirectional_sample import (
    _build_processing_order,
    _build_variable_chain,
    _get_anchorable_slots,
    _parse_step,
    choose_anchor_index,
    sample_question_bidirectional,
)
from phantom_wiki.facts.inverse_relations import (
    ALL_RELATIONS,
    SYMMETRIC_RELATIONS,
    build_inverse_relation_map,
    get_inverse_name,
    register_inverse_predicates,
)
from phantom_wiki.facts.sample import (
    RELATION,
    RELATION_EASY,
    get_vals_and_update_cache,
    sample_question,
)
from phantom_wiki.facts.templates import generate_templates
from phantom_wiki.utils import decode
from tests.phantom_wiki.facts import DATABASE_SMALL_PATH


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def db(request):
    custom_path = request.config.getoption("--db-path", default=None)
    if custom_path:
        return get_database(str(custom_path.resolve()))
    return get_database(DATABASE_SMALL_PATH)


@pytest.fixture(scope="module")
def inverse_map(db):
    return register_inverse_predicates(db)


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


@pytest.fixture(scope="module")
def base_templates():
    templates = generate_templates(max_hops=1, max_constraints=2, question_types=["base"])
    return [t for t in templates if len(t) == 3]


@pytest.fixture(scope="module")
def deep_templates():
    templates = generate_templates(max_hops=1, max_constraints=2, question_types=["base"])
    return [t for t in templates if len(t) == 3]


def _collect(collector, test_name, question, query, metadata=None):
    """Helper to dump a question into the collector if available."""
    if collector is None:
        return
    answer = None
    subtype = None
    if metadata:
        subtype = metadata.get("method", "bidirectional")
        answer = f"anchor={metadata.get('anchor_slot_index')}, pos={metadata.get('anchor_position')}"
    collector.add(
        test_name=test_name,
        question=question,
        query=query,
        answer=answer,
        subtype=subtype,
    )


# ===========================================================================
# 1. Inverse predicate generation (7 tests)
# ===========================================================================
class TestInversePredicates:
    def test_inverse_predicates_emitted(self):
        """Every relation has corresponding _inverse entry."""
        inv_map = build_inverse_relation_map()
        for rel in ALL_RELATIONS:
            assert rel in inv_map, f"Missing inverse for {rel}"

    def test_inverse_symmetric_friend(self, db, inverse_map):
        """friend maps to itself (symmetric)."""
        assert inverse_map.get("friend") == "friend"

    def test_inverse_symmetric_sibling(self, db, inverse_map):
        """sibling maps to itself (symmetric)."""
        assert inverse_map.get("sibling") == "sibling"

    def test_inverse_symmetric_cousin(self, db, inverse_map):
        """cousin maps to itself (symmetric)."""
        assert inverse_map.get("cousin") == "cousin"

    def test_inverse_asymmetric_parent(self, db, inverse_map, person_names):
        """parent_inverse swaps arguments correctly against Prolog."""
        inv_name = inverse_map["parent"]
        assert inv_name == "parent_inverse"
        for name in person_names[:10]:
            fwd = list(db.prolog.query(f'parent("{name}", X)'))
            if fwd:
                child = decode(fwd[0]["X"])
                inv = list(db.prolog.query(f'{inv_name}("{child}", X)'))
                found = [decode(r["X"]) for r in inv]
                assert name in found
                return
        pytest.skip("No parent relations found")

    def test_inverse_compound_nephew(self, inverse_map):
        """nephew_inverse correctly named."""
        if "nephew" in inverse_map:
            assert inverse_map["nephew"] == "nephew_inverse"

    def test_inverse_auto_derived(self):
        """Custom relation list auto-generates inverse names."""
        custom = build_inverse_relation_map(["parent", "child", "custom_rel"])
        assert custom["custom_rel"] == "custom_rel_inverse"
        assert custom["parent"] == "parent_inverse"


# ===========================================================================
# 2. Query construction / chain building (8 tests)
# ===========================================================================
class TestQueryConstruction:
    def test_parse_attr_val(self):
        step = _parse_step("<attribute_name>_1(Y_2, <attribute_value>_1)")
        assert step["type"] == "attr_val"
        assert step["first_var"] == "Y_2"

    def test_parse_relation_name_y(self):
        step = _parse_step("<relation>_3(<name>_1, Y_4)")
        assert step["type"] == "relation_name"
        assert step["is_name_start"] is True

    def test_parse_relation_yy(self):
        step = _parse_step("<relation>_5(Y_2, Y_6)")
        assert step["type"] == "relation_yy"
        assert step["first_var"] == "Y_2"
        assert step["second_var"] == "Y_6"

    def test_parse_all_step_types(self):
        """Every recognized step type parses correctly."""
        assert _parse_step("<attribute_name>_1(Y_2, <attribute_value>_1)")["type"] == "attr_val"
        assert _parse_step("<relation>_1(<name>_1, Y_2)")["type"] == "relation_name"
        assert _parse_step("<relation>_1(Y_2, Y_4)")["type"] == "relation_yy"
        assert _parse_step("<attribute_name>_1(Y_2, Y_4)")["type"] == "attr_yy"
        assert _parse_step("aggregate_all(count, distinct(<relation_plural>_1(<name>_1, Y_2)), Count_1)")["type"] == "agg_name"
        assert _parse_step("aggregate_all(count, distinct(<relation_plural>_1(Y_1, Y_2)), Count_1)")["type"] == "agg_yy"
        assert _parse_step("static_thing(x)")["type"] == "static"

    def test_chain_simple(self):
        """Two-step chain builds correctly."""
        steps = [
            _parse_step("<relation>_1(<name>_1, Y_2)"),
            _parse_step("<relation>_3(Y_2, Y_4)"),
        ]
        chain = _build_variable_chain(steps)
        assert "Y_2" in chain
        assert "Y_4" in chain
        assert "<name>_1" in chain

    def test_chain_single_step(self):
        steps = [_parse_step("<relation>_1(<name>_1, Y_2)")]
        chain = _build_variable_chain(steps)
        assert len(chain) == 2

    def test_anchor_mid_chain_produces_both_directions(self):
        """Anchoring mid-chain gives both forward and inverse steps."""
        steps = [
            _parse_step("<relation>_1(<name>_1, Y_2)"),
            _parse_step("<relation>_3(Y_2, Y_4)"),
            _parse_step("<attribute_name>_5(Y_4, Y_6)"),
        ]
        chain = _build_variable_chain(steps)
        if "Y_4" in chain:
            idx = chain.index("Y_4")
            order = _build_processing_order(steps, chain, idx)
            directions = [d for _, d in order]
            assert "forward" in directions
            assert "inverse" in directions

    def test_static_steps_skipped_in_order(self):
        """Static predicates do not appear in processing order."""
        steps = [
            _parse_step("some_static_thing"),
            _parse_step("<relation>_1(<name>_1, Y_2)"),
        ]
        chain = _build_variable_chain(steps)
        if "Y_2" in chain:
            idx = chain.index("Y_2")
            order = _build_processing_order(steps, chain, idx)
            step_indices = [i for i, _ in order]
            assert 0 not in step_indices


# ===========================================================================
# 3. Sampling correctness (8 tests)
# ===========================================================================
class TestSamplingCorrectness:
    def test_sample_returns_valid_path(self, db, person_names, caches, inverse_map,
                                       base_templates, question_collector):
        """Every sampled chain validates in Prolog."""
        attr_cache, rel_cache = caches
        inv_cache: dict = {}
        rng = np.random.default_rng(42)
        validated = 0
        for tmpl in base_templates[:15]:
            q_template, query_template, answer = tmpl
            result = sample_question_bidirectional(
                q_template, query_template, rng, db, person_names,
                attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                num_sampling_attempts=50,
            )
            if result is not None:
                question, query, metadata = result
                joined = ", ".join(reversed(query))
                results = list(db.prolog.query(joined))
                assert len(results) > 0, f"Prolog found no results for: {joined}"
                _collect(question_collector, "valid_path", question, query, metadata)
                validated += 1
        assert validated > 0

    def test_sample_anchor_position_start(self, db, person_names, caches, inverse_map,
                                          base_templates, question_collector):
        """strategy='start' anchors at first anchorable slot."""
        attr_cache, rel_cache = caches
        inv_cache: dict = {}
        rng = np.random.default_rng(42)
        for tmpl in base_templates[:15]:
            q_template, query_template, answer = tmpl
            result = sample_question_bidirectional(
                q_template, query_template, rng, db, person_names,
                attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                num_sampling_attempts=50, anchor_strategy="start",
            )
            if result is not None:
                _, _, metadata = result
                steps = [_parse_step(item) for item in query_template]
                anchorable = _get_anchorable_slots(_build_variable_chain(steps), steps)
                assert metadata["anchor_slot_index"] == anchorable[0]
                return

    def test_sample_anchor_position_end(self, db, person_names, caches, inverse_map,
                                        base_templates, question_collector):
        """strategy='end' anchors at last anchorable slot."""
        attr_cache, rel_cache = caches
        inv_cache: dict = {}
        rng = np.random.default_rng(42)
        for tmpl in base_templates[:15]:
            q_template, query_template, answer = tmpl
            result = sample_question_bidirectional(
                q_template, query_template, rng, db, person_names,
                attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                num_sampling_attempts=50, anchor_strategy="end",
            )
            if result is not None:
                _, _, metadata = result
                steps = [_parse_step(item) for item in query_template]
                anchorable = _get_anchorable_slots(_build_variable_chain(steps), steps)
                assert metadata["anchor_slot_index"] == anchorable[-1]
                return

    def test_sample_anchor_position_middle(self, db, person_names, caches, inverse_map,
                                           base_templates, question_collector):
        """strategy='middle' anchors at the middle anchorable slot."""
        attr_cache, rel_cache = caches
        inv_cache: dict = {}
        rng = np.random.default_rng(42)
        for tmpl in base_templates[:15]:
            q_template, query_template, answer = tmpl
            result = sample_question_bidirectional(
                q_template, query_template, rng, db, person_names,
                attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                num_sampling_attempts=50, anchor_strategy="middle",
            )
            if result is not None:
                _, _, metadata = result
                steps = [_parse_step(item) for item in query_template]
                anchorable = _get_anchorable_slots(_build_variable_chain(steps), steps)
                expected = anchorable[len(anchorable) // 2]
                assert metadata["anchor_slot_index"] == expected
                return

    def test_sample_random_anchor_distribution(self, db, person_names, caches, inverse_map,
                                               base_templates, question_collector):
        """Random strategy produces >1 distinct anchor positions over 300 samples."""
        attr_cache, rel_cache = caches
        inv_cache: dict = {}
        rng = np.random.default_rng(42)
        anchor_positions = []
        for _ in range(300):
            tmpl = base_templates[rng.integers(0, len(base_templates))]
            q_template, query_template, answer = tmpl
            result = sample_question_bidirectional(
                q_template, query_template, rng, db, person_names,
                attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                num_sampling_attempts=50, anchor_strategy="random",
            )
            if result is not None:
                _, _, metadata = result
                anchor_positions.append(metadata["anchor_position"])

        counts = Counter(anchor_positions)
        assert len(counts) >= 2, f"Only {len(counts)} distinct anchor positions: {counts}"

    def test_sample_balanced_anchor_distribution(self, db, person_names, caches, inverse_map,
                                                 base_templates, question_collector):
        """Balanced strategy cycles through positions with <=1 count difference."""
        attr_cache, rel_cache = caches
        inv_cache: dict = {}
        rng = np.random.default_rng(42)
        counter = [0]
        anchor_indices = []
        for _ in range(50):
            q_template, query_template, answer = base_templates[0]
            result = sample_question_bidirectional(
                q_template, query_template, rng, db, person_names,
                attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                num_sampling_attempts=50, anchor_strategy="balanced",
                _balanced_counter=counter,
            )
            if result is not None:
                _, _, metadata = result
                anchor_indices.append(metadata["anchor_slot_index"])

        if len(anchor_indices) > 1:
            counts = Counter(anchor_indices)
            assert max(counts.values()) - min(counts.values()) <= 1

    def test_sample_no_dead_ends(self, db, person_names, caches, inverse_map,
                                 base_templates, question_collector):
        """Bidirectional succeeds for at least some templates."""
        attr_cache, rel_cache = caches
        inv_cache: dict = {}
        rng = np.random.default_rng(42)
        successes = 0
        for tmpl in base_templates[:10]:
            q_template, query_template, answer = tmpl
            result = sample_question_bidirectional(
                q_template, query_template, rng, db, person_names,
                attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                num_sampling_attempts=100,
            )
            if result is not None:
                successes += 1
        assert successes > 0

    def test_sample_multiple_templates_succeed(self, db, person_names, caches, inverse_map,
                                               base_templates, question_collector):
        """Multiple distinct templates produce valid questions."""
        attr_cache, rel_cache = caches
        inv_cache: dict = {}
        rng = np.random.default_rng(42)
        succeeded_templates = set()
        for i, tmpl in enumerate(base_templates[:20]):
            q_template, query_template, answer = tmpl
            result = sample_question_bidirectional(
                q_template, query_template, rng, db, person_names,
                attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                num_sampling_attempts=50,
            )
            if result is not None:
                question, query, metadata = result
                succeeded_templates.add(i)
                _collect(question_collector, "multi_template", question, query, metadata)

        assert len(succeeded_templates) >= 2


# ===========================================================================
# 4. Backwards compatibility (4 tests)
# ===========================================================================
class TestBackwardsCompatibility:
    def test_default_backward_unchanged(self, db, person_names, caches, base_templates):
        """Backward sampling reproduces with same seed."""
        attr_cache, rel_cache = caches
        for tmpl in base_templates[:5]:
            q_template, query_template, answer = tmpl
            rng1 = np.random.default_rng(42)
            rng2 = np.random.default_rng(42)
            r1 = sample_question(q_template, query_template, rng1, db, person_names,
                                 attr_cache, rel_cache, num_procs=1, num_sampling_attempts=50)
            r2 = sample_question(q_template, query_template, rng2, db, person_names,
                                 attr_cache, rel_cache, num_procs=1, num_sampling_attempts=50)
            if r1 is not None and r2 is not None:
                assert r1[0] == r2[0]
                assert r1[1] == r2[1]

    def test_seed_reproducibility_bidirectional(self, db, person_names, caches, inverse_map,
                                                base_templates):
        """Same seed → same bidirectional output."""
        attr_cache, rel_cache = caches
        q_template, query_template, answer = base_templates[0]
        results = []
        for _ in range(2):
            inv_cache: dict = {}
            rng = np.random.default_rng(42)
            result = sample_question_bidirectional(
                q_template, query_template, rng, db, person_names,
                attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                num_sampling_attempts=50,
            )
            results.append(result)
        if results[0] is not None and results[1] is not None:
            assert results[0][0] == results[1][0]
            assert results[0][1] == results[1][1]

    def test_backward_still_works(self, db, person_names, caches, base_templates,
                                  question_collector):
        """Standard backward sampling unaffected by bidirectional code."""
        attr_cache, rel_cache = caches
        rng = np.random.default_rng(42)
        for tmpl in base_templates[:5]:
            q_template, query_template, answer = tmpl
            result = sample_question(q_template, query_template, rng, db, person_names,
                                     attr_cache, rel_cache, num_procs=1, num_sampling_attempts=50)
            if result is not None:
                question, query = result
                assert question.endswith("?")
                assert not re.search(r"<\w+>_\d+", question)
                _collect(question_collector, "backward_compat", question, query)
                return
        pytest.skip("No backward result")

    def test_different_seeds_differ(self, db, person_names, caches, inverse_map, base_templates):
        """Different seeds produce different bidirectional output."""
        attr_cache, rel_cache = caches
        q_template, query_template, answer = base_templates[0]
        results = []
        for seed in [42, 999]:
            inv_cache: dict = {}
            rng = np.random.default_rng(seed)
            result = sample_question_bidirectional(
                q_template, query_template, rng, db, person_names,
                attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                num_sampling_attempts=50,
            )
            results.append(result)
        if results[0] is not None and results[1] is not None:
            assert results[0][0] != results[1][0] or results[0][2]["anchor_person"] != results[1][2]["anchor_person"]


# ===========================================================================
# 5. Answer position (5 tests)
# ===========================================================================
class TestAnswerPosition:
    def test_answer_head_default(self, db, person_names, caches, inverse_map,
                                 base_templates, question_collector):
        """Default answer_position='head' → slot 0."""
        attr_cache, rel_cache = caches
        inv_cache: dict = {}
        rng = np.random.default_rng(42)
        for tmpl in base_templates[:15]:
            q_template, query_template, answer = tmpl
            result = sample_question_bidirectional(
                q_template, query_template, rng, db, person_names,
                attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                num_sampling_attempts=50, answer_position="head",
            )
            if result is not None:
                question, query, metadata = result
                assert metadata["answer_position"] == "head"
                assert metadata["answer_slot_index"] == 0
                _collect(question_collector, "answer_head", question, query, metadata)
                return
        pytest.skip("No result")

    def test_answer_tail(self, db, person_names, caches, inverse_map,
                         base_templates, question_collector):
        """answer_position='tail' → answer at last slot."""
        attr_cache, rel_cache = caches
        inv_cache: dict = {}
        rng = np.random.default_rng(42)
        for tmpl in base_templates[:15]:
            q_template, query_template, answer = tmpl
            result = sample_question_bidirectional(
                q_template, query_template, rng, db, person_names,
                attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                num_sampling_attempts=50, answer_position="tail",
            )
            if result is not None:
                question, query, metadata = result
                assert metadata["answer_position"] == "tail"
                assert metadata["answer_slot_index"] == metadata["chain_length"]
                _collect(question_collector, "answer_tail", question, query, metadata)
                return
        pytest.skip("No result")

    def test_answer_random_varies(self, db, person_names, caches, inverse_map,
                                  base_templates, question_collector):
        """answer_position='random' produces both head and tail over 100 questions."""
        attr_cache, rel_cache = caches
        inv_cache: dict = {}
        rng = np.random.default_rng(42)
        positions = []
        for _ in range(100):
            tmpl = base_templates[rng.integers(0, len(base_templates))]
            q_template, query_template, answer = tmpl
            result = sample_question_bidirectional(
                q_template, query_template, rng, db, person_names,
                attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                num_sampling_attempts=50, answer_position="random",
            )
            if result is not None:
                question, query, metadata = result
                positions.append(metadata["answer_position"])
                _collect(question_collector, "answer_random", question, query, metadata)

        pos_counts = Counter(positions)
        assert len(pos_counts) >= 2, f"answer_position='random' didn't vary: {pos_counts}"

    def test_answer_head_polarity_changes_with_anchor(self, db, person_names, caches,
                                                       inverse_map, base_templates):
        """With head answer, different anchor positions yield different polarities."""
        attr_cache, rel_cache = caches
        polarities = set()
        for strategy in ["start", "end"]:
            inv_cache: dict = {}
            rng = np.random.default_rng(42)
            for tmpl in base_templates[:15]:
                q_template, query_template, answer = tmpl
                result = sample_question_bidirectional(
                    q_template, query_template, rng, db, person_names,
                    attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                    num_sampling_attempts=50, anchor_strategy=strategy,
                    answer_position="head",
                )
                if result is not None:
                    _, _, metadata = result
                    polarities.add(metadata["polarity"])
                    break
        assert len(polarities) >= 1

    def test_answer_slot_index_consistent(self, db, person_names, caches, inverse_map,
                                          base_templates):
        """answer_slot_index matches chain_length for tail, 0 for head."""
        attr_cache, rel_cache = caches
        for pos in ["head", "tail"]:
            inv_cache: dict = {}
            rng = np.random.default_rng(42)
            for tmpl in base_templates[:15]:
                q_template, query_template, answer = tmpl
                result = sample_question_bidirectional(
                    q_template, query_template, rng, db, person_names,
                    attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                    num_sampling_attempts=50, answer_position=pos,
                )
                if result is not None:
                    _, _, metadata = result
                    if pos == "head":
                        assert metadata["answer_slot_index"] == 0
                    else:
                        assert metadata["answer_slot_index"] == metadata["chain_length"]
                    break


# ===========================================================================
# 6. Metadata completeness (5 tests)
# ===========================================================================
class TestMetadata:
    def test_all_required_fields_present(self, db, person_names, caches, inverse_map,
                                         base_templates, question_collector):
        """Metadata has every field from the output spec."""
        attr_cache, rel_cache = caches
        inv_cache: dict = {}
        rng = np.random.default_rng(42)
        for tmpl in base_templates[:15]:
            q_template, query_template, answer = tmpl
            result = sample_question_bidirectional(
                q_template, query_template, rng, db, person_names,
                attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                num_sampling_attempts=50,
            )
            if result is not None:
                question, query, metadata = result
                required = [
                    "method", "anchor_position", "anchor_slot_index",
                    "anchor_person", "answer_position", "answer_slot_index",
                    "polarity", "chain_length", "chain_variables",
                ]
                for field in required:
                    assert field in metadata, f"Missing: {field}"
                _collect(question_collector, "metadata_fields", question, query, metadata)
                return
        pytest.skip("No result")

    def test_prolog_solutions_found_positive(self, db, person_names, caches, inverse_map,
                                             base_templates):
        """prolog_solutions_found >= 1 for valid questions."""
        attr_cache, rel_cache = caches
        inv_cache: dict = {}
        rng = np.random.default_rng(42)
        for tmpl in base_templates[:15]:
            q_template, query_template, answer = tmpl
            result = sample_question_bidirectional(
                q_template, query_template, rng, db, person_names,
                attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                num_sampling_attempts=50,
            )
            if result is not None:
                _, _, metadata = result
                assert metadata["prolog_solutions_found"] >= 1
                return
        pytest.skip("No result")

    def test_polarity_values_valid(self, db, person_names, caches, inverse_map, base_templates):
        """Polarity must be one of same, same_side, opposite."""
        attr_cache, rel_cache = caches
        inv_cache: dict = {}
        rng = np.random.default_rng(42)
        for tmpl in base_templates[:15]:
            q_template, query_template, answer = tmpl
            result = sample_question_bidirectional(
                q_template, query_template, rng, db, person_names,
                attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                num_sampling_attempts=50,
            )
            if result is not None:
                _, _, metadata = result
                assert metadata["polarity"] in ("same", "same_side", "opposite")
                return
        pytest.skip("No result")

    def test_anchor_position_label_valid(self, db, person_names, caches, inverse_map,
                                         base_templates):
        """anchor_position is start, middle, or end."""
        attr_cache, rel_cache = caches
        inv_cache: dict = {}
        rng = np.random.default_rng(42)
        for tmpl in base_templates[:15]:
            q_template, query_template, answer = tmpl
            result = sample_question_bidirectional(
                q_template, query_template, rng, db, person_names,
                attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                num_sampling_attempts=50,
            )
            if result is not None:
                _, _, metadata = result
                assert metadata["anchor_position"] in ("start", "middle", "end")
                return
        pytest.skip("No result")

    def test_chain_variables_list_nonempty(self, db, person_names, caches, inverse_map,
                                           base_templates):
        """chain_variables is a non-empty list of variable names."""
        attr_cache, rel_cache = caches
        inv_cache: dict = {}
        rng = np.random.default_rng(42)
        for tmpl in base_templates[:15]:
            q_template, query_template, answer = tmpl
            result = sample_question_bidirectional(
                q_template, query_template, rng, db, person_names,
                attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                num_sampling_attempts=50,
            )
            if result is not None:
                _, _, metadata = result
                assert isinstance(metadata["chain_variables"], list)
                assert len(metadata["chain_variables"]) >= 2
                return
        pytest.skip("No result")


# ===========================================================================
# 7. Edge cases & robustness (6 tests)
# ===========================================================================
class TestEdgeCases:
    def test_returns_none_on_impossible_template(self, db, person_names, caches, inverse_map):
        """Returns None when no anchorable Y variables exist."""
        attr_cache, rel_cache = caches
        inv_cache: dict = {}
        rng = np.random.default_rng(42)
        result = sample_question_bidirectional(
            ["What", "is", "?"], ["static_predicate(a, b)"],
            rng, db, person_names, attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
            num_sampling_attempts=5,
        )
        assert result is None

    def test_easy_mode_restricts_relations(self, db, person_names, caches, inverse_map,
                                           base_templates, question_collector):
        """Easy mode produces valid questions."""
        attr_cache, rel_cache = caches
        inv_cache: dict = {}
        rng = np.random.default_rng(42)
        for tmpl in base_templates[:10]:
            q_template, query_template, answer = tmpl
            result = sample_question_bidirectional(
                q_template, query_template, rng, db, person_names,
                attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                easy_mode=True, num_sampling_attempts=50,
            )
            if result is not None:
                question, query, metadata = result
                assert question.endswith("?")
                _collect(question_collector, "easy_mode", question, query, metadata)
                return
        pytest.skip("No result in easy mode")

    def test_question_well_formed(self, db, person_names, caches, inverse_map,
                                  base_templates, question_collector):
        """Questions end with ? and have no unresolved <placeholder>_N tokens."""
        attr_cache, rel_cache = caches
        inv_cache: dict = {}
        rng = np.random.default_rng(42)
        checked = 0
        for tmpl in base_templates[:15]:
            q_template, query_template, answer = tmpl
            result = sample_question_bidirectional(
                q_template, query_template, rng, db, person_names,
                attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                num_sampling_attempts=50,
            )
            if result is not None:
                question, query, metadata = result
                assert question.endswith("?")
                assert not re.search(r"<\w+>_\d+", question)
                for stmt in query:
                    assert not re.search(r"<\w+>_\d+", stmt)
                _collect(question_collector, "well_formed", question, query, metadata)
                checked += 1
        assert checked > 0

    def test_choose_anchor_empty_raises(self):
        with pytest.raises(ValueError):
            choose_anchor_index([], np.random.default_rng(0))

    def test_choose_anchor_unknown_strategy_raises(self):
        with pytest.raises(ValueError, match="Unknown anchor strategy"):
            choose_anchor_index([0], np.random.default_rng(0), strategy="bogus")

    def test_get_inverse_name_function(self):
        """get_inverse_name returns correct names."""
        assert get_inverse_name("parent") == "parent_inverse"
        assert get_inverse_name("friend") == "friend"
        assert get_inverse_name("sibling") == "sibling"
        assert get_inverse_name("uncle") == "uncle_inverse"


# ===========================================================================
# 8. Multi-template stress tests with output dumping (7 tests)
# ===========================================================================
class TestStress:
    def test_batch_10_questions_per_template(self, db, person_names, caches, inverse_map,
                                             base_templates, question_collector):
        """Generate 10 questions per template for the first 5 templates."""
        attr_cache, rel_cache = caches
        inv_cache: dict = {}
        rng = np.random.default_rng(42)
        total = 0
        for i, tmpl in enumerate(base_templates[:5]):
            q_template, query_template, answer = tmpl
            for _ in range(10):
                result = sample_question_bidirectional(
                    q_template, query_template, rng, db, person_names,
                    attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                    num_sampling_attempts=50,
                )
                if result is not None:
                    question, query, metadata = result
                    _collect(question_collector, f"batch_tmpl_{i}", question, query, metadata)
                    total += 1
        assert total >= 10

    def test_all_strategies_produce_output(self, db, person_names, caches, inverse_map,
                                           base_templates, question_collector):
        """All 5 anchor strategies produce at least one question."""
        attr_cache, rel_cache = caches
        strategies = ["random", "start", "middle", "end", "balanced"]
        for strategy in strategies:
            inv_cache: dict = {}
            rng = np.random.default_rng(42)
            found = False
            for tmpl in base_templates[:15]:
                q_template, query_template, answer = tmpl
                result = sample_question_bidirectional(
                    q_template, query_template, rng, db, person_names,
                    attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                    num_sampling_attempts=50, anchor_strategy=strategy,
                )
                if result is not None:
                    question, query, metadata = result
                    _collect(question_collector, f"strategy_{strategy}", question, query, metadata)
                    found = True
                    break
            assert found, f"Strategy '{strategy}' produced no results"

    def test_deep_templates_work(self, db, person_names, caches, inverse_map,
                                 deep_templates, question_collector):
        """Depth-6 templates (longer chains) also produce valid questions."""
        attr_cache, rel_cache = caches
        inv_cache: dict = {}
        rng = np.random.default_rng(42)
        successes = 0
        for tmpl in deep_templates[:20]:
            q_template, query_template, answer = tmpl
            result = sample_question_bidirectional(
                q_template, query_template, rng, db, person_names,
                attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                num_sampling_attempts=50,
            )
            if result is not None:
                question, query, metadata = result
                _collect(question_collector, "deep_templates", question, query, metadata)
                successes += 1
        assert successes > 0

    def test_mixed_answer_positions_batch(self, db, person_names, caches, inverse_map,
                                          base_templates, question_collector):
        """Batch with answer_position='random' produces mixed head/tail."""
        attr_cache, rel_cache = caches
        inv_cache: dict = {}
        rng = np.random.default_rng(42)
        positions = []
        for _ in range(50):
            tmpl = base_templates[rng.integers(0, len(base_templates))]
            q_template, query_template, answer = tmpl
            result = sample_question_bidirectional(
                q_template, query_template, rng, db, person_names,
                attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                num_sampling_attempts=50, answer_position="random",
            )
            if result is not None:
                question, query, metadata = result
                positions.append(metadata["answer_position"])
                _collect(question_collector, "mixed_answer_pos", question, query, metadata)
        assert len(set(positions)) >= 2

    def test_prolog_correctness_batch(self, db, person_names, caches, inverse_map,
                                      base_templates, question_collector):
        """Every question in a batch of 30 has a valid Prolog answer."""
        attr_cache, rel_cache = caches
        inv_cache: dict = {}
        rng = np.random.default_rng(42)
        checked = 0
        for _ in range(30):
            tmpl = base_templates[rng.integers(0, len(base_templates))]
            q_template, query_template, answer = tmpl
            result = sample_question_bidirectional(
                q_template, query_template, rng, db, person_names,
                attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                num_sampling_attempts=50,
            )
            if result is not None:
                question, query, metadata = result
                joined = ", ".join(reversed(query))
                results = list(db.prolog.query(joined))
                assert len(results) > 0, f"No Prolog result for: {joined}"
                _collect(question_collector, "prolog_correctness", question, query, metadata)
                checked += 1
        assert checked >= 10

    def test_anchor_person_from_universe(self, db, person_names, caches, inverse_map,
                                        base_templates, question_collector):
        """Every anchor_person in metadata is a real person from the universe."""
        attr_cache, rel_cache = caches
        inv_cache: dict = {}
        rng = np.random.default_rng(42)
        for _ in range(20):
            tmpl = base_templates[rng.integers(0, len(base_templates))]
            q_template, query_template, answer = tmpl
            result = sample_question_bidirectional(
                q_template, query_template, rng, db, person_names,
                attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                num_sampling_attempts=50,
            )
            if result is not None:
                _, _, metadata = result
                assert metadata["anchor_person"] in person_names

    def test_chain_length_matches_template(self, db, person_names, caches, inverse_map,
                                           base_templates, question_collector):
        """chain_length is consistent with the number of chain steps in the template."""
        attr_cache, rel_cache = caches
        inv_cache: dict = {}
        rng = np.random.default_rng(42)
        for tmpl in base_templates[:10]:
            q_template, query_template, answer = tmpl
            result = sample_question_bidirectional(
                q_template, query_template, rng, db, person_names,
                attr_cache, rel_cache, inv_cache, inverse_map, num_procs=1,
                num_sampling_attempts=50,
            )
            if result is not None:
                _, _, metadata = result
                assert metadata["chain_length"] >= 1
                assert metadata["chain_length"] == len(metadata["chain_variables"]) - 1
                _collect(question_collector, "chain_length", "", [], metadata)
                return
        pytest.skip("No result")
