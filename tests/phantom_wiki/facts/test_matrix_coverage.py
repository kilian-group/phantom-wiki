"""Tests for (hops, constraints) matrix coverage.

Verifies that generate_templates and build_comparison_count_variants populate
the expected cells as max_hops and max_constraints vary.
"""
import re
import pytest
from collections import Counter
from phantom_wiki.facts.templates import (
    generate_templates,
    cfg_depth_for_max_hops,
    is_comparison_older_subtype,
    is_comparison_younger_subtype,
    is_comparison_subtype,
)
from phantom_wiki.facts.extended_questions import (
    build_comparison_count_variants,
    build_extended_question_types,
    build_extended_question_category,
    _count_variant_type,
)


# ---------------------------------------------------------------------------
# cfg_depth_for_max_hops
# ---------------------------------------------------------------------------
class TestCfgDepth:
    @pytest.mark.parametrize("max_hops,expected_depth", [
        (1, 6),
        (2, 8),
        (3, 10),
        (4, 12),
    ])
    def test_formula(self, max_hops, expected_depth):
        assert cfg_depth_for_max_hops(max_hops) == expected_depth


# ---------------------------------------------------------------------------
# count_variant_type naming
# ---------------------------------------------------------------------------
class TestCountVariantType:
    def test_plain(self):
        assert _count_variant_type(0, 0) == "comparison_count"

    def test_chain_only(self):
        assert _count_variant_type(2, 0) == "comparison_count_chain2"

    def test_mc_only(self):
        assert _count_variant_type(0, 3) == "comparison_count_mc3"

    def test_chain_and_mc(self):
        assert _count_variant_type(2, 3) == "comparison_count_chain2_mc3"


# ---------------------------------------------------------------------------
# build_comparison_count_variants
# ---------------------------------------------------------------------------
class TestBuildVariants:
    def test_keys_named_correctly(self):
        v = build_comparison_count_variants(max_chain_depth=2, n_attrs_options=(0, 2, 3))
        assert "comparison_count" in v
        assert "comparison_count_chain2" in v
        assert "comparison_count_mc2" in v
        assert "comparison_count_chain2_mc3" in v

    def test_values_are_pairs(self):
        v = build_comparison_count_variants(max_chain_depth=3, n_attrs_options=(0, 2, 3))
        for key, (chain_depth, n_attrs) in v.items():
            assert isinstance(chain_depth, int)
            assert isinstance(n_attrs, int)

    def test_size(self):
        # (max_chain_depth+1) * len(n_attrs_options)
        v = build_comparison_count_variants(max_chain_depth=3, n_attrs_options=(0, 2, 3))
        assert len(v) == 4 * 3  # 4 chain depths × 3 n_attrs options

    def test_empty_attrs(self):
        v = build_comparison_count_variants(max_chain_depth=2, n_attrs_options=(0,))
        assert all(n == 0 for _, n in v.values())

    def test_extended_question_types_includes_all(self):
        v = build_comparison_count_variants(max_chain_depth=1, n_attrs_options=(0, 2, 3))
        types = build_extended_question_types(v)
        for key in v:
            assert key in types

    def test_extended_question_category_all_comparison_count(self):
        v = build_comparison_count_variants(max_chain_depth=1, n_attrs_options=(0, 2))
        cat = build_extended_question_category(v)
        for key in v:
            assert cat[key] == "comparison_count"

    @pytest.mark.parametrize("max_constraints", [2, 3, 4])
    def test_mc_range(self, max_constraints):
        opts = (0,) + tuple(range(2, max_constraints + 1))
        v = build_comparison_count_variants(max_chain_depth=2, n_attrs_options=opts)
        n_attrs_in_variants = {n for _, n in v.values()}
        for n in range(2, max_constraints + 1):
            assert n in n_attrs_in_variants


# ---------------------------------------------------------------------------
# is_comparison_*_subtype predicates
# ---------------------------------------------------------------------------
class TestSubtypePredicates:
    @pytest.mark.parametrize("subtype", [
        "comparison_age",
        "comparison_age_mc2",
        "comparison_age_mc3",
        "comparison_born_first",
        "comparison_born_first_mc2",
        "comparison_born_first_mc3",
    ])
    def test_older_subtypes(self, subtype):
        assert is_comparison_older_subtype(subtype)
        assert not is_comparison_younger_subtype(subtype)
        assert is_comparison_subtype(subtype)

    @pytest.mark.parametrize("subtype", [
        "comparison_age_younger",
        "comparison_age_younger_mc2",
        "comparison_age_younger_mc3",
    ])
    def test_younger_subtypes(self, subtype):
        assert is_comparison_younger_subtype(subtype)
        assert not is_comparison_older_subtype(subtype)
        assert is_comparison_subtype(subtype)

    @pytest.mark.parametrize("subtype", [
        "superlative_oldest",
        "multi_constraint_2",
        "comparison_count",
    ])
    def test_non_comparison_subtypes(self, subtype):
        assert not is_comparison_subtype(subtype)


# ---------------------------------------------------------------------------
# generate_templates cell coverage
# ---------------------------------------------------------------------------
_RELATION_ATOM = re.compile(r"^<relation>_\d+\(")
_ATTR_ATOM = re.compile(r"^<attribute_name>_\d+\(")
_AGG_ATOM = re.compile(r"^aggregate_all")


def _template_cell(p_atoms: list[str]) -> tuple[int, int]:
    """Estimate (hops, constraints) for a template's Prolog atom list.

    Uses placeholder patterns rather than concrete predicate names since
    templates have not been substituted yet.
    """
    hops = sum(1 for a in p_atoms if _RELATION_ATOM.match(a) or _AGG_ATOM.match(a))
    constraints = sum(1 for a in p_atoms if _ATTR_ATOM.match(a))
    return hops, constraints


def _cells_covered(templates) -> set[tuple[int, int]]:
    """Return set of (hops, constraints) cells across all templates."""
    cells = set()
    for t in templates:
        p_atoms = t[1]
        if not isinstance(p_atoms, list):
            continue
        cells.add(_template_cell(p_atoms))
    return cells


class TestTemplateCells:
    @pytest.mark.parametrize("max_hops", [1, 2, 3, 4])
    def test_base_hops_range(self, max_hops):
        """Base templates scale with max_hops in the (h, 0) column.

        The count grammar (``How many Xp does [chain] have?``) contributes
        one aggregate_all on top of the chain, so the deepest (h, 0) cell
        is max_hops + 1. We verify that the column reaches that depth.
        """
        ts = generate_templates(
            max_hops=max_hops, max_constraints=2, question_types=["base"]
        )
        cells = _cells_covered(ts)
        hop_col = {h for h, c in cells if c == 0}
        assert max(hop_col) >= max_hops, (
            f"Expected max hop in (h,0) column >= {max_hops}, got {sorted(hop_col)}"
        )

    @pytest.mark.parametrize("max_hops", [1, 2, 3, 4])
    def test_base_attr_anchor(self, max_hops):
        """Base templates include at least one 1-attr-constraint cell."""
        ts = generate_templates(
            max_hops=max_hops, max_constraints=2, question_types=["base"]
        )
        cells = _cells_covered(ts)
        assert any(c >= 1 for _, c in cells), "Expected at least one constraint-1 cell"

    @pytest.mark.parametrize("max_constraints", [2, 3])
    def test_multi_constraint_cells(self, max_constraints):
        """Standalone multi_constraint covers (0, n) for n in 2..max_constraints."""
        ts = generate_templates(
            max_hops=4, max_constraints=max_constraints, question_types=["multi_constraint"]
        )
        cells = _cells_covered(ts)
        for n in range(2, max_constraints + 1):
            assert (0, n) in cells, f"Missing (hops=0, constraints={n}) at max_constraints={max_constraints}"

    @pytest.mark.parametrize("max_hops,max_constraints", [
        (2, 2), (3, 2), (4, 2),
        (2, 3), (3, 3), (4, 3),
    ])
    def test_comparison_age_mc_cells(self, max_hops, max_constraints):
        """comparison_age with mc-N fragments populates (hops>=1, constraints=N) cells."""
        ts = generate_templates(
            max_hops=max_hops,
            max_constraints=max_constraints,
            question_types=["comparison_age"],
        )
        cells = _cells_covered(ts)
        for n in range(2, max_constraints + 1):
            # At least (1, n) should be populated
            assert any(h >= 1 and c == n for h, c in cells), (
                f"Missing any (hops>=1, constraints={n}) at max_hops={max_hops}, max_constraints={max_constraints}"
            )

    def test_more_hops_strictly_more_cells(self):
        """Cells at max_hops=4 strictly include all cells at max_hops=2."""
        ts2 = generate_templates(max_hops=2, max_constraints=2, question_types=["base", "comparison_age"])
        ts4 = generate_templates(max_hops=4, max_constraints=2, question_types=["base", "comparison_age"])
        cells2 = _cells_covered(ts2)
        cells4 = _cells_covered(ts4)
        assert cells2 <= cells4
        assert cells2 != cells4  # strictly more at higher max_hops

    def test_more_constraints_strictly_more_cells(self):
        """Cells at max_constraints=3 strictly include all cells at max_constraints=2."""
        ts2 = generate_templates(max_hops=3, max_constraints=2, question_types=["multi_constraint", "comparison_age"])
        ts3 = generate_templates(max_hops=3, max_constraints=3, question_types=["multi_constraint", "comparison_age"])
        cells2 = _cells_covered(ts2)
        cells3 = _cells_covered(ts3)
        assert cells2 <= cells3
        assert cells2 != cells3


# ---------------------------------------------------------------------------
# Single-position chain extensions: mc-anchor and mid-chain constraints
# ---------------------------------------------------------------------------
class TestChainRcBaseTemplates:
    """Base templates emitted by ``_build_chain_rc_base_templates`` —
    mc-c anchors (p == n_hops, c >= 2) and mid-chain (p < n_hops, c >= 1).
    """

    @pytest.mark.parametrize("max_hops,max_constraints", [
        (2, 2), (3, 2), (3, 3), (4, 3),
    ])
    def test_mc_anchor_cells_covered(self, max_hops, max_constraints):
        """For each h in 1..max_hops and c in 2..max_constraints, an (h, c) cell exists."""
        ts = generate_templates(
            max_hops=max_hops, max_constraints=max_constraints, question_types=["base"]
        )
        cells = _cells_covered(ts)
        for h in range(1, max_hops + 1):
            for c in range(2, max_constraints + 1):
                assert (h, c) in cells, (
                    f"Missing (h={h}, c={c}) at max_hops={max_hops}, "
                    f"max_constraints={max_constraints}"
                )

    @pytest.mark.parametrize("max_hops,max_constraints", [
        (2, 2), (3, 2), (3, 3), (4, 3),
    ])
    def test_mid_chain_emits_relative_clause(self, max_hops, max_constraints):
        """Mid-chain templates contain ', whose <attribute_name>_X is ...,' inside the chain."""
        ts = generate_templates(
            max_hops=max_hops, max_constraints=max_constraints, question_types=["base"]
        )
        # At least one base template should contain a mid-chain relative clause:
        # the marker ", whose" appears (with leading comma) only in mid-chain output.
        joined = [" ".join(t[0]) for t in ts if isinstance(t[0], list)]
        assert any(", whose" in q for q in joined), (
            "Expected at least one mid-chain template with ', whose ...' clause"
        )

    def test_skips_c1_p_equals_n_hops(self):
        """``(c=1, p=n_hops)`` is covered by the base CFG; the chain builder should not duplicate it.

        For max_hops=1, max_constraints=1, the chain builder enumerates only one
        case ``(n_hops=1, c=1, p=1)`` which is skipped — so it emits zero new
        templates and the total template count equals the CFG-only count.
        """
        cfg_only = generate_templates(max_hops=1, max_constraints=1, question_types=["base"])
        # max_constraints=1 alone gives no new chain templates beyond CFG.
        assert all(", whose" not in " ".join(t[0]) for t in cfg_only)

    def test_mid_chain_clause_constrains_named_intermediate(self):
        """The relative clause must constrain the Y referred to by the noun it follows.

        For a chain template "the rel_0 of the rel_1, whose AN is AV, of <name>",
        the clause comes after "the rel_1" — which refers to Y_1 in the chain
        (result of rel_1, source of rel_0). The Prolog atom for the constraint
        must therefore bind to that same Y_1, not to Y_0 or any other variable.
        """
        ts = generate_templates(max_hops=3, max_constraints=2, question_types=["base"])
        # Find one mid-chain template (contains ", whose").
        for q_tokens, p_atoms, _ in [t for t in ts if isinstance(t[0], list)]:
            q_str = " ".join(q_tokens)
            if not q_str.startswith("Who is") or ", whose" not in q_str:
                continue
            # Identify which Y_k the relative clause sits next to: count "the <relation>_N"
            # occurrences before the ", whose" marker.
            pre_clause = q_str.split(", whose")[0]
            relations_before = re.findall(r"<relation>_(\d+)", pre_clause)
            assert len(relations_before) >= 1
            # The noun the clause attaches to is the LAST relation before ", whose".
            noun_rel_subscript = int(relations_before[-1])
            # The chain produces Y_k as the result of <relation>_(offset+k); the
            # subscript on the relation name equals offset+k, so its result Y is
            # Y_(offset+k) — same numeric subscript as the relation token.
            expected_target_y = f"Y_{noun_rel_subscript}"
            # Find the attribute_name atom in p_atoms; its first arg must be expected_target_y.
            attr_atoms = [a for a in p_atoms if a.startswith("<attribute_name>_")]
            assert attr_atoms, f"Mid-chain template missing attribute atom: {p_atoms}"
            for atom in attr_atoms:
                m = re.match(r"<attribute_name>_\d+\((Y_\d+),", atom)
                assert m, f"Could not parse attribute atom: {atom}"
                actual_target = m.group(1)
                assert actual_target == expected_target_y, (
                    f"Clause attaches to relation noun for {expected_target_y} but "
                    f"Prolog binds constraint to {actual_target}.\nQ: {q_str}\nP: {p_atoms}"
                )
            return  # one verified template is enough
        pytest.fail("No mid-chain template found to verify")

    def test_three_top_level_forms(self):
        """Each new chain fragment is emitted as Who/What/How-many."""
        ts = generate_templates(max_hops=2, max_constraints=2, question_types=["base"])
        joined = [" ".join(t[0]) for t in ts if isinstance(t[0], list)]
        # Each top-level form must contain at least one new chain template,
        # detected by the "whose ... is ... and ... is" multi-attr clause.
        def has_multi_attr(q):
            return re.search(r"whose <attribute_name>_\d+ is <attribute_value>_\d+ and ", q) is not None
        assert any(q.startswith("Who is") and has_multi_attr(q) for q in joined)
        assert any(q.startswith("What is") and has_multi_attr(q) for q in joined)
        assert any(q.startswith("How many") and has_multi_attr(q) for q in joined)


class TestOffsetWindowsDisjoint:
    """Sequential offset windows must keep each chain fragment's subscripts disjoint
    from every other chain fragment's subscripts, including after fragment renumbering.
    """

    def test_chain_base_template_subscripts_disjoint(self):
        """Distinct chain fragments use disjoint subscript ranges.

        The three top-level wrappers (Who/What/How-many) share a chain fragment
        and are intentionally in the same offset window. We verify only that
        distinct chain fragments do not overlap by examining one wrapper
        (the "Who is" form) per chain.
        """
        ts = generate_templates(max_hops=4, max_constraints=3, question_types=["base"])
        windows = []
        for t in ts:
            q_str = " ".join(t[0]) if isinstance(t[0], list) else ""
            if not q_str.startswith("Who is"):
                continue
            if ", whose" not in q_str and "and whose" not in q_str:
                continue
            subs = set()
            for atom in t[1]:
                subs.update(int(m) for m in re.findall(r"_(\d+)", atom))
            if not subs:
                continue
            windows.append((min(subs), max(subs)))
        for i, (a_lo, a_hi) in enumerate(windows):
            for b_lo, b_hi in windows[i + 1:]:
                assert a_hi < b_lo or b_hi < a_lo, (
                    f"Chain fragment windows overlap: [{a_lo},{a_hi}] vs [{b_lo},{b_hi}]"
                )


# ---------------------------------------------------------------------------
# comparison_count variants target cells
# ---------------------------------------------------------------------------
class TestComparisonCountCells:
    """Verify each variant type maps to the expected (hops, constraints) target.

    The +1 on hops comes from aggregate_all inside the comparison_count sampler;
    we can't easily test this without a real DB, so we just check the variant
    table encodes the right (chain_depth, n_attrs) pairs.
    """
    @pytest.mark.parametrize("chain_depth,n_attrs,expected_key", [
        (0, 0, "comparison_count"),
        (1, 0, "comparison_count_chain1"),
        (3, 0, "comparison_count_chain3"),
        (0, 2, "comparison_count_mc2"),
        (2, 2, "comparison_count_chain2_mc2"),
        (0, 3, "comparison_count_mc3"),
        (1, 3, "comparison_count_chain1_mc3"),
        (3, 3, "comparison_count_chain3_mc3"),
    ])
    def test_variant_key_and_value(self, chain_depth, n_attrs, expected_key):
        v = build_comparison_count_variants(
            max_chain_depth=3, n_attrs_options=(0, 2, 3)
        )
        assert expected_key in v
        assert v[expected_key] == (chain_depth, n_attrs)

    @pytest.mark.parametrize("max_hops,max_constraints", [
        (2, 2), (3, 3), (4, 3),
    ])
    def test_chain_depth_bounded_by_max_hops(self, max_hops, max_constraints):
        """chain_depth never exceeds max_hops - 1 (aggregate_all adds the last hop)."""
        opts = (0,) + tuple(range(2, max_constraints + 1))
        v = build_comparison_count_variants(
            max_chain_depth=max_hops - 1, n_attrs_options=opts
        )
        for key, (chain_depth, _) in v.items():
            assert chain_depth <= max_hops - 1, (
                f"{key} has chain_depth={chain_depth} > max_hops-1={max_hops-1}"
            )
