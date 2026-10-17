"""Generates formal question templates and corresponding Prolog queries using a context-free grammar (CFG).


*Question templates* are based on the QA_GRAMMAR_STRING and can be generated at varying recursion depths.
The templates are not complete questions or valid queries, as they contain the <placeholder> tokens intended
to be replaced with their instantiations that depend on their type and the Prolog database.

For example, at a low recursion depth the grammar string may generate two questions:

    > Question: Who is the person whose hobby is reading?
    > Template: Who is the person whose <attribute_name>_1 is <attribute_value>_1 ?

    > Question: How many children does John have?
    > Template: How many <relation_plural>_2 does <name>_1 have?

Therefore a template of a question is an abstraction of many possible questions of the same type.

Note the exact numbering of the <placeholder> tokens may differ based on the chosen recursion depth, and is
there to distinguish tokens potentially generated at the same recursion depth but representing different
tokens.

Each question template has a corresponding template for Prolog query used to obtain the ground truth answer.
For example:

    > Template: Who is the person whose <attribute_name>_1 is <attribute_value>_1 ?
    > Query: <attribute_name>_1(Y_2, <attribute_value>_1).
    > Answer: Y_2

    > Template: How many <relation_plural>_2 does <name>_1 have?
    > Query: aggregate_all(count, distinct(<relation_plural>_2(<name>_1, Y_3)), Count_3).
    > Answer: Count_3

`phantom_wiki.facts.templates.generate_templates` generates tuples of all possible question and Prolog query
templates at a particular recursion depth from the context-free grammar as defined by QA_GRAMMAR_STRING.

This template generation is based on the `nltk.parse.generate` function from the NLTK project, see:
    Source: https://github.com/nltk/nltk/blob/develop/nltk/parse/generate.py
    Natural Language Toolkit: Generating from a CFG

    Copyright (C) 2001-2024 NLTK Project
    Author: Steven Bird <stevenbird1@gmail.com>
            Peter Ljunglöf <peter.ljunglof@heatherleaf.se>
            Eric Kafe <kafe.eric@gmail.com>
    URL: https://www.nltk.org/
    For license information, see https://github.com/nltk/nltk/blob/develop/LICENSE.txt
"""

import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from nltk import CFG, Nonterminal

QA_GRAMMAR_STRING = """
    S -> 'Who is' R '?' | 'What is' A '?' | 'How many' RN_p 'does' R_c 'have' '?'
    R -> 'the' RN 'of' R_c | 'the person whose' AN 'is' AV
    R_c -> R | N
    A -> 'the' AN 'of' R
    RN -> '<relation>'
    RN_p -> '<relation_plural>'
    AN -> '<attribute_name>'
    AV -> '<attribute_value>'
    N -> '<name>'
    """

# Question type categories for filtering
QUESTION_TYPE_BASE = "base"
QUESTION_TYPE_COMPARISON_AGE = "comparison_age"
QUESTION_TYPE_COMPARISON_COUNT = "comparison_count"
QUESTION_TYPE_MULTI_CONSTRAINT = "multi_constraint"
QUESTION_TYPE_SUPERLATIVE = "superlative"
ALL_QUESTION_TYPES = [
    QUESTION_TYPE_BASE,
    QUESTION_TYPE_COMPARISON_AGE,
    QUESTION_TYPE_COMPARISON_COUNT,
    QUESTION_TYPE_MULTI_CONSTRAINT,
    QUESTION_TYPE_SUPERLATIVE,
]

# Extended question subtypes for the non-mc-N (plain) builders.
# mc-N variant subtypes are generated dynamically as f"<base>_mc{n}".
COMPARISON_AGE_SUBTYPE = "comparison_age"
COMPARISON_AGE_YOUNGER_SUBTYPE = "comparison_age_younger"
COMPARISON_BORN_FIRST_SUBTYPE = "comparison_born_first"
SUPERLATIVE_OLDEST_SUBTYPE = "superlative_oldest"
SUPERLATIVE_YOUNGEST_SUBTYPE = "superlative_youngest"


def is_comparison_older_subtype(subtype: str) -> bool:
    """True for comparison subtypes whose Prolog success means LEFT is older.

    Covers both the plain forms ("comparison_age", "comparison_born_first") and
    the dynamically-named multi-constraint variants ("comparison_age_mc3", etc.),
    while excluding the "_younger" variants.
    """
    if subtype.startswith("comparison_age_younger"):
        return False
    return subtype.startswith("comparison_age") or subtype.startswith("comparison_born_first")


def is_comparison_younger_subtype(subtype: str) -> bool:
    return subtype.startswith("comparison_age_younger")


def is_comparison_subtype(subtype: str) -> bool:
    return is_comparison_older_subtype(subtype) or is_comparison_younger_subtype(subtype)


def classify_question_type(question_template: list[str]) -> str:
    """Classify a question template into one of the extended types based on its structure."""
    joined = " ".join(question_template)
    if any(kw in joined for kw in ["older,", "younger,", "born first,"]):
        return QUESTION_TYPE_COMPARISON_AGE
    if any(kw in joined for kw in ["has more ", "has fewer "]):
        return QUESTION_TYPE_COMPARISON_COUNT
    if "and whose" in joined:
        return QUESTION_TYPE_MULTI_CONSTRAINT
    if any(kw in joined for kw in ["oldest", "youngest"]):
        return QUESTION_TYPE_SUPERLATIVE
    return QUESTION_TYPE_BASE


def is_aggregation_question(question: str) -> bool:
    """
    Returns True if the question is an aggregation question.

    Definition of aggregation question:
    -----------------------------------
    1. Starts with `"How many"`
    -----------------------------------
    For example, "How many children does John have?" is an aggregation question.
    """
    return question.strip().startswith("How many")


def cfg_depth_for_max_hops(max_hops: int) -> int:
    """CFG recursion-depth cap that reaches every cell up to ``max_hops``.

    Each chain step (``R -> 'the X of' R_c``) costs 2 grammar levels, and the
    attribute-anchor branch (``R_c -> R -> 'the person whose AN is AV'``) costs
    another 2. So to reach the ``(max_hops, attr-anchor)`` cell of the base CFG
    we need ``2 * max_hops + 4`` levels.
    """
    return 2 * max_hops + 4


def generate_templates(
    max_hops: int,
    max_constraints: int,
    question_types: list[str] | None = None,
    grammar: CFG = None,
) -> list[tuple]:
    """Generate question + Prolog query templates for the (hops, constraints) matrix.

    Args:
        max_hops: The largest number of relation hops any generated question may
            contain. Drives both the base CFG depth (2*max_hops + 4) and the
            chain-builders' extra hops.
        max_constraints: The largest number of attribute constraints any generated
            question may contain. Determines which mc-N anchors get built (n in
            2..max_constraints) and the standalone multi-constraint sizes.
        question_types: List of high-level types to include. If None, only base
            types. Use ALL_QUESTION_TYPES or a subset.
        grammar: Optional CFG override. Defaults to QA_GRAMMAR_STRING.

    Returns:
        List of tuples. Base templates are 3-tuples (q, p, answer). Extended
        templates are 4-tuples (q, p, answer_info, subtype).
    """
    if grammar is None:
        grammar = CFG.fromstring(QA_GRAMMAR_STRING)
    if question_types is None:
        question_types = [QUESTION_TYPE_BASE]

    depth = cfg_depth_for_max_hops(max_hops)
    start = grammar.start()
    templates: list[tuple] = []

    if QUESTION_TYPE_BASE in question_types:
        fragments = _generate_tail_template_fragments(grammar, [start], depth, depth)
        for fragment in fragments:
            templates.append((fragment.q_fragment, fragment.p_fragment, fragment.p_answer))
        # Add chain templates the base CFG cannot generate: mc-c anchors and
        # mid-chain single-position constraints.
        templates += _build_chain_rc_base_templates(max_hops, max_constraints)

    extended_types = set(question_types) - {QUESTION_TYPE_BASE}
    if extended_types:
        rc_nonterminal = Nonterminal("R_c")
        templates += _generate_extended_templates(
            grammar, rc_nonterminal, depth, extended_types, max_hops, max_constraints,
        )

    return templates


def _generate_extended_templates(
    grammar: CFG,
    rc_nonterminal: Nonterminal,
    depth: int,
    extended_types: set[str],
    max_hops: int,
    max_constraints: int,
) -> list[tuple]:
    """Generate extended question templates by composing R_c fragments from the base grammar.

    For each ``n`` in ``2..max_constraints``, builds mc-N fragments and feeds them
    into the comparison and superlative composers. Deep R_c fragments (built up to
    ``max_hops`` hops) bypass the CFG depth cap so the composers can reach the
    high-hops cells.

    Returns 4-tuples: (question_template, query_template, answer_info, question_subtype).
    """
    templates = []

    rc_fragments = _generate_head_template_fragments(grammar, rc_nonterminal, depth, depth)
    deep_rc_fragments = _build_deep_rc_fragments(max_hops)
    all_rc_fragments = rc_fragments + deep_rc_fragments

    # mc-N fragments for n in [2, max_constraints]
    mc_fragments_by_n: dict[int, list[Fragment]] = {
        n: _build_mc_n_fragments(n, depth) for n in range(2, max_constraints + 1)
    }

    if QUESTION_TYPE_COMPARISON_AGE in extended_types:
        templates += _build_comparison_templates(grammar, rc_fragments, depth)
        for n, mc_frags in mc_fragments_by_n.items():
            templates += _build_comparison_mc_n_templates(all_rc_fragments, mc_frags, n, depth)

    # Count-comparison templates are emitted by extended_questions.py via the
    # comparison_count_variants table — not from the CFG composer.

    if QUESTION_TYPE_MULTI_CONSTRAINT in extended_types:
        templates += _build_multi_constraint_templates(depth, max_constraints)

    if QUESTION_TYPE_SUPERLATIVE in extended_types:
        templates += _build_superlative_templates(grammar, all_rc_fragments, depth)
        sup_chain_depths = tuple(range(1, max_hops + 1))
        for n, mc_frags in mc_fragments_by_n.items():
            templates += _build_superlative_mc_n_templates(mc_frags, n, depth, sup_chain_depths)

    return templates


def _build_mc_n_fragments(n: int, depth: int) -> list["Fragment"]:
    """Build Fragment objects representing an N-attribute multi-constraint person lookup.

    Each fragment represents: 'the person whose AN1 is AV1 and whose AN2 is AV2 ... and whose ANN is AVN'
    with query atoms [AN1(Y_person, AV1), ..., ANN(Y_person, AVN)] and answer Y_person.

    These are used as R_c substitutes in comparison/superlative builders so that one
    branch can carry N constraints, enabling (hops>=1, constraints=N) questions.

    ``n`` must be >= 2 (n=1 is already covered by the base CFG attribute anchor).
    """
    if n < 2:
        raise ValueError(f"_build_mc_n_fragments requires n >= 2, got {n}")

    # Use a high offset (n * depth * 10) so different (n, depth) combos don't
    # collide with each other or with base R_c fragments.
    offset = n * depth * 10
    person_var = f"Y_{offset}"

    q: list[str] = ["the person"]
    p: list[str] = []
    for i in range(n):
        an = f"<attribute_name>_{offset + i}"
        av = f"<attribute_value>_{offset + i}"
        prefix = "whose" if i == 0 else "and whose"
        q.extend([prefix, an, "is", av])
        p.append(f"{an}({person_var}, {av})")

    return [Fragment(q_fragment=q, p_fragment=p, p_answer=person_var)]


def _renumber_fragment(fragment: "Fragment", offset: int) -> "Fragment":
    """Add offset to all numeric subscripts (_N) in a fragment to avoid variable collisions."""
    pattern = re.compile(r"_(\d+)")

    def add_offset(s):
        return pattern.sub(lambda m: f"_{int(m.group(1)) + offset}", s)

    return Fragment(
        q_fragment=[add_offset(t) for t in fragment.q_fragment],
        p_fragment=[add_offset(t) for t in fragment.p_fragment],
        p_answer=add_offset(fragment.p_answer) if fragment.p_answer else None,
    )


def _get_person_var(fragment: "Fragment") -> str:
    """Get the variable/placeholder that resolves to a person from an R_c fragment.

    For N (terminal name): the placeholder like '<name>_1'
    For R (chain): the answer variable like 'Y_3'
    """
    if fragment.p_answer:
        return fragment.p_answer
    return fragment.p_fragment[0]


def _count_hops(fragment: "Fragment") -> int:
    """Count the number of relation hops in an R_c fragment.

    N (name) -> 0 hops
    R (attr only) -> 0 hops (attribute constraint, no relation traversal)
    R (chain) -> number of relation predicates in p_fragment
    """
    return sum(
        1 for atom in fragment.p_fragment
        if re.match(r"<relation>_\d+", atom)
    )


# Sequential subscript-window allocation for chain fragments.
# Each fragment owns a disjoint window [offset, offset + STRIDE).
# STRIDE is chosen large enough that fragment renumbering (adds <100) cannot
# cause any two fragments' windows to overlap.
CHAIN_FRAGMENT_OFFSET_BASE = 1000
CHAIN_FRAGMENT_OFFSET_STRIDE = 1000


def _build_chain_rc_fragment(
    n_hops: int,
    c_count: int,
    c_position: int,
    offset: int,
) -> "Fragment":
    """Build an R_c chain fragment with c_count attribute filters at one position.

    A chain "Who is the <rel_0> of the <rel_1> of ... <anchor>?" with at most one
    decorated person along the chain. The structural knobs are:

      n_hops:     number of relations in the chain (>= 1)
      c_count:    number of attribute filters on a single person (0 = none)
      c_position: which person carries the filters; 1..n_hops where n_hops is
                  the anchor and k in 1..n_hops-1 is intermediate Y_k. Ignored
                  when c_count == 0.

    The chain produces persons Y_0..Y_n where the question phrase "the <rel_k>"
    refers to Y_k (the result of relation k). So a relative clause constraining
    Y_k must follow "the <rel_k>" in the surface form. Y_0 is the answer and
    not directly constrainable here.

    Three cases:
      c_count == 0:                       pure-name chain (anchor = <name>)
      c_count >= 1 and c_position == n_hops: anchor carries the filters (mc-c
        anchor; subsumes the legacy single-attr anchor at c=1)
      c_count >= 1 and c_position <  n_hops: an intermediate Y_{c_position}
        carries the filters; the anchor is a <name>

    Subscript layout (all variables/placeholders live in [offset, offset + STRIDE)):
      answer  = Y_{offset}
      Y_i     = Y_{offset + i}    for i in 1..n_hops-1   (intermediates)
      anchor  = Y_{offset + n_hops}                      (only when anchor is a
                                                          person variable)
      relation_i, name, attribute_*  use disjoint subscripts in the same window.
    """
    assert n_hops >= 0, f"n_hops must be >= 0, got {n_hops}"
    assert c_count >= 0, f"c_count must be >= 0, got {c_count}"
    if c_count > 0:
        assert 0 <= c_position <= n_hops, (
            f"c_position must be in 0..{n_hops}, got {c_position}"
        )
    if n_hops == 0:
        # Pure anchor (no chain): only meaningful with attribute filters.
        assert c_count > 0 and c_position == 0, (
            "n_hops=0 requires c_count >= 1 and c_position = 0 (the anchor)"
        )

    q: list[str] = []
    p: list[str] = []

    def _attr_clause(target_var: str) -> str:
        """Build "<an>_1 is <av>_1 and <an>_2 is <av>_2 ..." and append the
        corresponding Prolog atoms to ``p``."""
        parts = []
        for k in range(c_count):
            an = f"<attribute_name>_{offset + n_hops + 1 + k}"
            av = f"<attribute_value>_{offset + n_hops + 1 + k}"
            parts.append(f"{an} is {av}")
            p.append(f"{an}({target_var}, {av})")
        return " and ".join(parts)

    for i in range(n_hops):
        rel_token = f"<relation>_{offset + i}"
        # Mid-chain clause goes after the noun referring to Y_i, i.e. when
        # i == c_position. The clause + commas is glued into one token so
        # " ".join does not insert spaces before the commas.
        if c_count > 0 and c_position == i and 1 <= c_position < n_hops:
            q.append(f"the {rel_token}, whose {_attr_clause(f'Y_{offset + i}')}, of")
        else:
            q.extend(["the", rel_token, "of"])

    # Anchor: <name>, or mc-c anchor when c_count >= 1 at the end of the chain.
    if c_count > 0 and c_position == n_hops:
        anchor_var = f"Y_{offset + n_hops}"
        q.append(f"the person whose {_attr_clause(anchor_var)}")
    else:
        anchor_var = f"<name>_{offset + n_hops}"
        q.append(anchor_var)

    for i in range(n_hops):
        outer = f"Y_{offset + i}"
        if i == n_hops - 1:
            inner = anchor_var
        else:
            inner = f"Y_{offset + i + 1}"
        p.append(f"<relation>_{offset + i}({inner}, {outer})")

    return Fragment(q_fragment=q, p_fragment=p, p_answer=f"Y_{offset}")


def _build_deep_rc_fragments(max_hops: int) -> list["Fragment"]:
    """Plain-anchor R_c chains (name or single-attr) for extended composers.

    Used by ``_build_comparison_mc_n_templates`` and ``_build_superlative_*``
    composers, which pair these chains with mc-N branches to add constraints.
    Produces only the configurations these composers need: 2..max_hops hops,
    name- or single-attr-anchored. Sequential offset windows.
    """
    fragments: list[Fragment] = []
    for idx, (n_hops, c_count, c_position) in enumerate(
        (n_hops, c, p)
        for n_hops in range(2, max_hops + 1)
        for (c, p) in [(0, 0), (1, n_hops)]
    ):
        offset = CHAIN_FRAGMENT_OFFSET_BASE + idx * CHAIN_FRAGMENT_OFFSET_STRIDE
        fragments.append(_build_chain_rc_fragment(n_hops, c_count, c_position, offset))
    return fragments


def _build_chain_rc_base_templates(
    max_hops: int, max_constraints: int
) -> list[tuple]:
    """Base templates with single-position constraints on the chain.

    Enumerates ``(n_hops, c, p)`` with ``1 <= n_hops <= max_hops``,
    ``1 <= c <= max_constraints``, ``1 <= p <= n_hops``. Skips ``(c=1, p=n_hops)``
    because the base CFG already produces "Who is the <rel> of ... of the person
    whose AN is AV?" via natural recursion, and we want a single source of truth
    per (hops, constraints, position) cell.

    Each chain is wrapped into the three top-level question forms the CFG
    supports, so the new (h, c) cells are filled across question categories:

      * "Who is <chain>?"               — answer is the chain's terminal person
      * "What is the AN of <chain>?"    — answer is an attribute of that person
      * "How many RN_p does <chain> have?" — answer is a count

    Each emitted chain fills one of:
      * (h>=1, c>=2, p=h):   mc-c anchor — "...of the person whose A1 is V1 and whose A2 is V2?"
      * (h>=1, c>=1, p<h):   mid-chain — "...the friend, whose A1 is V1, of <name>?"

    Offsets sit above the deep_rc range so the two builders cannot collide.
    """
    templates: list[tuple] = []
    base_offset = CHAIN_FRAGMENT_OFFSET_BASE + 1_000_000  # well above _build_deep_rc_fragments
    idx = 0
    for n_hops in range(0, max_hops + 1):
        for c in range(1, max_constraints + 1):
            # n_hops=0: only one position (the anchor itself); no mid-chain.
            positions = [0] if n_hops == 0 else range(1, n_hops + 1)
            for p in positions:
                # CFG already produces single-attr anchored "the person whose
                # AN is AV" chains, so skip (c=1, p=n_hops) to avoid duplicates.
                # TODO: open question — drop the "person whose AN is AV" branch
                # from QA_GRAMMAR_STRING and let this builder be the single
                # source of truth for all "whose"-clause constraints (c >= 1
                # at any position). Would unify mid-chain, mc-anchor, and
                # single-attr anchor into one code path; currently deferred
                # because the CFG path is exercised by golden-file fixtures
                # (templates_depth_*.json) that would need refreshing.
                if c == 1 and p == n_hops:
                    continue
                offset = base_offset + idx * CHAIN_FRAGMENT_OFFSET_STRIDE
                idx += 1
                frag = _build_chain_rc_fragment(n_hops, c, p, offset)
                templates += _wrap_chain_in_top_level_forms(frag, offset)
    return templates


def _wrap_chain_in_top_level_forms(frag: "Fragment", offset: int) -> list[tuple]:
    """Wrap a chain fragment in the three S-productions of QA_GRAMMAR_STRING.

    Uses subscripts well above the chain's own window (offset + 500..) so the
    wrapper placeholders cannot collide with the chain's variables.
    """
    chain_person = frag.p_answer
    wrap_sub = offset + 500
    out: list[tuple] = []

    # 1. "Who is <chain> ?"
    q_who = ["Who is"] + frag.q_fragment + ["?"]
    out.append((q_who, frag.p_fragment, frag.p_answer))

    # 2. "What is the <attribute_name> of <chain> ?"
    attr_n = f"<attribute_name>_{wrap_sub}"
    attr_y = f"Y_{wrap_sub}"
    q_what = ["What is", "the", attr_n, "of"] + frag.q_fragment + ["?"]
    p_what = [f"{attr_n}({chain_person}, {attr_y})"] + frag.p_fragment
    out.append((q_what, p_what, attr_y))

    # 3. "How many <relation_plural> does <chain> have ?"
    rel_p = f"<relation_plural>_{wrap_sub + 1}"
    count_y = f"Y_{wrap_sub + 1}"
    count_v = f"Count_{wrap_sub + 1}"
    q_many = ["How many", rel_p, "does"] + frag.q_fragment + ["have", "?"]
    p_many = [
        f"aggregate_all(count, distinct({rel_p}({chain_person}, {count_y})), {count_v})"
    ] + frag.p_fragment
    out.append((q_many, p_many, count_v))

    return out


def _build_comparison_mc_n_templates(
    rc_fragments: list["Fragment"],
    mc_n_fragments: list["Fragment"],
    n: int,
    depth: int,
) -> list[tuple]:
    """Build comparison templates where one branch is an N-attribute multi-constraint fragment.

    Pairs each R_c fragment (which contributes hops) with an mc-N fragment (which contributes
    N constraints), producing questions like:
      'Who is older, the wife of the person whose hobby is X
       or the person whose job is Y and whose hobby is Z?'

    Unlocks (hops>=1, constraints=N) cells.
    """
    templates = []
    dob_l_var = f"CmpDL_{depth}_{n}"
    dob_r_var = f"CmpDR_{depth}_{n}"

    phrasings = [
        (f"comparison_age_mc{n}", ["Who is older,"]),
        (f"comparison_age_younger_mc{n}", ["Who is younger,"]),
        (f"comparison_born_first_mc{n}", ["Who was born first,"]),
    ]
    pair_idx = 0

    for rc_frag in rc_fragments:
        if _count_hops(rc_frag) == 0:
            continue  # skip name/attribute-only frags — no hops to pair with

        for mc_frag in mc_n_fragments:
            mc_var = _get_person_var(mc_frag)
            rc_var = _get_person_var(rc_frag)

            # rc on the left, mc on the right
            age_query = (
                [f"{dob_l_var} @< {dob_r_var}",
                 f"dob({rc_var}, {dob_l_var})",
                 f"dob({mc_var}, {dob_r_var})"]
                + rc_frag.p_fragment
                + mc_frag.p_fragment
            )
            subtype, prefix = phrasings[pair_idx % len(phrasings)]
            pair_idx += 1
            q = prefix + rc_frag.q_fragment + ["or"] + mc_frag.q_fragment + ["?"]
            templates.append((q, age_query, (rc_var, mc_var), subtype))

            # Also mc on the left, rc on the right (reversed)
            age_query_rev = (
                [f"{dob_l_var} @< {dob_r_var}",
                 f"dob({mc_var}, {dob_l_var})",
                 f"dob({rc_var}, {dob_r_var})"]
                + mc_frag.p_fragment
                + rc_frag.p_fragment
            )
            subtype, prefix = phrasings[pair_idx % len(phrasings)]
            pair_idx += 1
            q = prefix + mc_frag.q_fragment + ["or"] + rc_frag.q_fragment + ["?"]
            templates.append((q, age_query_rev, (mc_var, rc_var), subtype))

    return templates


def _build_superlative_mc_n_templates(
    mc_n_fragments: list["Fragment"],
    n: int,
    depth: int,
    chain_depths: tuple[int, ...],
) -> list[tuple]:
    """Build superlative templates where the anchor chain is an mc-N fragment.

    'Who is the oldest [relation] of the person whose [attr1] is X and ... and whose [attrN] is Z?'

    The mc-N fragment (0 hops, N constraints) provides the innermost anchor person; one or
    more fresh relation placeholders (chain depth K) are stacked on top to add hops,
    producing (hops=K, constraints=N) questions.
    """
    templates = []
    sup_d1 = f"SupD_{depth}_{n}"
    sup_d2 = f"SupD2_{depth}_{n}"
    sup_z = f"SupZ_{depth}_{n}"

    oldest_subtype = f"superlative_oldest_mc{n}"
    youngest_subtype = f"superlative_youngest_mc{n}"

    for chain_depth in chain_depths:
        assert chain_depth >= 1
        # Subscript base for this chain's relation/answer variables.
        # Layout: 300 + n*200 + chain_depth*10 — keeps (n, chain_depth) slots
        # disjoint and clear of CFG (<=20), mc-N (n*depth*10), deep-rc (200-...).
        base = 300 + n * 200 + chain_depth * 10
        answer_var = f"Y_{base}"

        for mc_frag in mc_n_fragments:
            mc_person = _get_person_var(mc_frag)

            # Build chain atoms (in query order: innermost first so reversal executes outermost first)
            chain_q: list[str] = []
            chain_p: list[str] = []
            for i in range(chain_depth):
                chain_q.extend(["the", f"<relation>_{base + i}", "of"])
                outer = f"Y_{base + i}"
                inner = mc_person if i == chain_depth - 1 else f"Y_{base + i + 1}"
                chain_p.append(f"<relation>_{base + i}({inner}, {outer})")

            # Outer superlative's negation-as-failure target.
            if chain_depth == 1:
                nf_inner = mc_person
            else:
                nf_inner = f"Y_{base + 1}"
            rel_outer = f"<relation>_{base}"

            for subtype, adj, op in [
                (oldest_subtype, "oldest", "@<"),
                (youngest_subtype, "youngest", "@>"),
            ]:
                q_chain = chain_q.copy()
                q_chain[0] = f"the {adj}"

                q = ["Who is"] + q_chain + mc_frag.q_fragment + ["?"]
                query = [
                    f"\\+ ({rel_outer}({nf_inner}, {sup_z}), dob({sup_z}, {sup_d2}), "
                    f"{sup_z} \\= {answer_var}, {sup_d2} {op} {sup_d1})",
                    f"dob({answer_var}, {sup_d1})",
                ] + chain_p + mc_frag.p_fragment
                templates.append((q, query, answer_var, subtype))

    return templates


_COMPARISON_AGE_PHRASINGS = [
    (COMPARISON_AGE_SUBTYPE, ["Who is older,"]),
    (COMPARISON_AGE_YOUNGER_SUBTYPE, ["Who is younger,"]),
    (COMPARISON_BORN_FIRST_SUBTYPE, ["Who was born first,"]),
]


def _build_comparison_templates(
    grammar: CFG, rc_fragments: list["Fragment"], depth: int
) -> list[tuple]:
    """Build comparison question templates from pairs of R_c fragments.

    For each ``(left, right)`` R_c pair, emits ONE phrasing chosen round-robin
    from older / younger / born-first. The three phrasings encode the same
    DOB-comparison question with different surface forms; emitting all three
    per pair triples template volume without adding logical diversity.

    The round-robin assignment is deterministic (counter mod 3), so each
    phrasing receives ~1/3 of pairs.
    """
    templates = []
    pair_idx = 0

    for left_frag in rc_fragments:
        # Renumber right operand to avoid variable collisions with left
        for right_frag_orig in rc_fragments:
            right_frag = _renumber_fragment(right_frag_orig, depth)
            left_var = _get_person_var(left_frag)
            right_var = _get_person_var(right_frag)

            # Query: chain queries + dob lookups + comparison
            # After reversal in get_answer, execution order is:
            # chains -> dob lookups -> comparison
            dob_l_var = f"CmpDL_{depth}"
            dob_r_var = f"CmpDR_{depth}"

            age_query = (
                [f"{dob_l_var} @< {dob_r_var}", f"dob({left_var}, {dob_l_var})", f"dob({right_var}, {dob_r_var})"]
                + left_frag.p_fragment
                + right_frag.p_fragment
            )

            subtype, prefix = _COMPARISON_AGE_PHRASINGS[pair_idx % len(_COMPARISON_AGE_PHRASINGS)]
            pair_idx += 1
            q = prefix + left_frag.q_fragment + ["or"] + right_frag.q_fragment + ["?"]
            answer_info = (left_var, right_var)
            templates.append((q, age_query, answer_info, subtype))

    return templates


def _build_multi_constraint_templates(depth: int, max_constraints: int) -> list[tuple]:
    """Build multi-constraint question templates for n=2..max_constraints.

    Multi-constraint: "Who is the person whose AN1 is AV1 and ... and whose ANn is AVn?"
    Resolves to a person matching n attributes (a leaf production).
    """
    if max_constraints < 2:
        return []

    templates = []
    person_var = f"Y_{depth}"

    for n in range(2, max_constraints + 1):
        ans = [f"<attribute_name>_{depth + i}" for i in range(n)]
        avs = [f"<attribute_value>_{depth + i}" for i in range(n)]

        q = ["Who is", "the person"]
        for i in range(n):
            prefix = "whose" if i == 0 else "and whose"
            q.extend([prefix, ans[i], "is", avs[i]])
        q.append("?")

        query = [f"{ans[i]}({person_var}, {avs[i]})" for i in range(n)]
        subtype = f"multi_constraint_{n}"
        templates.append((q, query, person_var, subtype))

    return templates


def _build_superlative_templates(
    grammar: CFG, rc_fragments: list["Fragment"], depth: int
) -> list[tuple]:
    """Build superlative question templates from R_c fragments.

    Superlative types:
    - "Who is the oldest/youngest RN of R_c?" (age-based)
    - "Who is the RN of R_c with the most/fewest RN_p?" (count-based)

    The superlative itself is an R production that resolves to a person,
    and it composes with R_c via R_c -> R.
    """
    templates = []

    for rc_frag in rc_fragments:
        rc_person = _get_person_var(rc_frag)

        # Age-based superlatives: oldest/youngest
        # R -> 'the oldest/youngest' RN 'of' R_c
        rel_d = f"<relation>_{depth + 1}"
        answer_var = f"Y_{depth + 1}"
        sup_z = f"SupZ_{depth}"
        sup_d1 = f"SupD_{depth}"
        sup_d2 = f"SupD2_{depth}"

        for subtype, adj, op in [
            (SUPERLATIVE_OLDEST_SUBTYPE, "oldest", "@<"),
            (SUPERLATIVE_YOUNGEST_SUBTYPE, "youngest", "@>"),
        ]:
            q = ["Who is", f"the {adj}", rel_d, "of"] + rc_frag.q_fragment + ["?"]
            # Query order: negation, dob, relation, then chain queries
            # After reversal in get_answer: chain -> relation -> dob -> negation
            query = [
                f"\\+ ({rel_d}({rc_person}, {sup_z}), dob({sup_z}, {sup_d2}), "
                f"{sup_z} \\= {answer_var}, {sup_d2} {op} {sup_d1})",
                f"dob({answer_var}, {sup_d1})",
                f"{rel_d}({rc_person}, {answer_var})",
            ] + rc_frag.p_fragment
            templates.append((q, query, answer_var, subtype))

    return templates


@dataclass
class Fragment:
    """Fragment of the question and Prolog query template.

    Represents a subsequence of the CFG.
    If the subsequence is empty, it will be of the form ([], [], None).
    If the subsequence is a single terminal, it will be of the form (['terminal'], [], None).
    If the subsequence is a single <placeholder> terminal, it will be of the form
        (['<placeholder>_*'], ['<placeholder>_*'], None).
    Otherwise, a general subsequence is of the form
        (['Who is', 'the', '<relation>_*', ...], ['<relation>_*(...)', ...], Y_*)

    Attributes:
        q_fragment: Question template of the current fragment
        p_fragment: Prolog query template of the current fragment
        p_answer: The variable in the Prolog query template corresponding to the answer
    """

    q_fragment: list[str] = field(default_factory=list)
    p_fragment: list[str] = field(default_factory=list)
    p_answer: str = None

    def is_empty(self):
        """End-of-production fragment."""
        return not self.q_fragment

    def is_terminal(self):
        """Regular non<placeholder> terminal."""
        return not self.p_fragment

    def is_placeholder(self):
        """Test for <placeholder> terminal."""
        return len(self.p_fragment) == 1 and not self.p_answer

    def get_question_template(self) -> str:
        # TODO remove space before question mark
        return " ".join(self.q_fragment)

    def get_query_template(self) -> str:
        return ", ".join(self.p_fragment)

    def get_query_answer(self) -> str:
        return self.p_answer


def _generate_tail_template_fragments(
    grammar: CFG, items: list[Nonterminal | Any], depth: int, total_depth: int
) -> list[Fragment]:
    """Generates fragments for a list of symbols (`items`) in the grammar.

    Calls `_generate_head_template_fragments` to process the first symbol in `items` and then makes a
    recursive call to process the "remaining symbols" (tail) of the list.
    Then combines all valid subsequences (fragments) resulting from the tail call with all the valid
    subsequences produced from the first symbol.
    """
    if items:
        try:
            fragments = []
            for frag1 in _generate_head_template_fragments(grammar, items[0], depth, total_depth):
                for frag2 in _generate_tail_template_fragments(grammar, items[1:], depth, total_depth):
                    fragments.append(_combine_fragments(frag1, frag2, depth, total_depth))
        except RecursionError as error:
            # Helpful error message while still showing the recursion stack.
            raise RuntimeError(
                "The grammar has rule(s) that yield infinite recursion!\n\
                    Eventually use a lower 'depth', or a higher 'sys.setrecursionlimit()'."
            ) from error
        return fragments
    else:
        # End of production
        return [Fragment()]


def _generate_head_template_fragments(
    grammar: CFG, item: Nonterminal | Any, depth: int, total_depth: int
) -> list[Fragment]:
    """Generates fragments for the current `item` symbol of the grammar.

    Called as a subroutine to process the first symbol (head) of the current production (`item`).
    Recursively calls `_generate_tail_template_fragments` if `item` is a nonterminal in the CFG, for all its
    possible productions.
    If `item` is a <placeholder> or terminal, generates its Fragment.
    """
    if depth > 0:
        if isinstance(item, Nonterminal):
            fragments = []
            for prod in grammar.productions(lhs=item):
                fragments += _generate_tail_template_fragments(grammar, prod.rhs(), depth - 1, total_depth)
            return fragments

        elif re.match(r"<.*?>", item):
            # <placeholder> terminal
            d = total_depth - depth
            return [Fragment([f"{item}_{d}"], [f"{item}_{d}"], None)]
        else:
            # non<placeholder> terminal
            return [Fragment([item], [], None)]

    return []


def _combine_fragments(f1: Fragment, f2: Fragment, depth, total_depth) -> Fragment:
    """Combines two Fragments.

    This merges two CFG subsequences, e.g. 'Who is' and 'the <relation> of ...'.
    The question fragments are combined straightforwardly by concatenating the symbols.
    The Prolog query fragments are combined based on the <placeholder> and query type.

    Examples:
    > (['Who is'], [], None) + (['<name>'], ['<name>'], None) -> (['Who is', '<name>'], ['<name>'], None)
    > (['<attribute_name>_3'], ['<attribute_name>_3'], None)
        + (['of the', '<relation>_2', 'of', '<name>_1', '?'], ['<relation>_2(<name>_1, Y_3)'], 'Y_3')
        -> (['<attribute_name>_3', 'of the', ...],
            ['<attribute_name>_3(Y_3, Y_4)', '<relation>_2(<name>_1, Y_3)'],
            'Y_4')
    """

    q_fragment = f1.q_fragment + f2.q_fragment

    if f1.is_empty():
        return Fragment(q_fragment, f2.p_fragment, f2.p_answer)

    elif f1.is_terminal():
        if f2.is_empty():
            return Fragment(q_fragment, f1.p_fragment, f1.p_answer)
        else:
            return Fragment(q_fragment, f2.p_fragment, f2.p_answer)

    # <placeholder> f1 case (e.g. '<relation>', '<name>',...)
    #   Note: the grammar currently does not allow f1 to be a subquery,
    #   but f2 can be either a subquery, <placeholder>, terminal, or empty
    else:
        if f2.is_empty() or f2.is_terminal():
            return Fragment(q_fragment, f1.p_fragment, f1.p_answer)

        assert f1.is_placeholder()
        placeholder = f1.p_fragment[0]
        subquery = None
        answer = None

        d = total_depth - depth

        if re.match(r"<relation_plural>_(\d+)", placeholder):
            if f2.is_placeholder():
                # ... how many brothers does Alice have ...
                subquery = [
                    (f"aggregate_all(count, distinct({placeholder}({f2.p_fragment[0]}, Y_{d})), Count_{d})")
                ]
            else:
                # ... how many brothers does the sister of Alice have ...
                subquery = [
                    f"aggregate_all(count, distinct({placeholder}({f2.p_answer}, Y_{d})), Count_{d})"
                ] + f2.p_fragment
            answer = f"Count_{d}"

        elif re.match(r"<relation>_(\d+)", placeholder):
            if f2.is_placeholder():
                # ... who is the mother of Alice ...
                subquery = [f"{placeholder}({f2.p_fragment[0]}, Y_{d})"]
            else:
                # ... who is the mother of the mother of Alice ...
                subquery = [f"{placeholder}({f2.p_answer}, Y_{d})"] + f2.p_fragment
            answer = f"Y_{d}"

        elif re.match(r"<attribute_name>_(\d+)", placeholder):
            if placeholder.replace("name", "value") in f2.p_fragment[0]:
                # ... whose hobby is running ...
                assert f2.is_placeholder()
                subquery = [f"{placeholder}(Y_{d}, {f2.p_fragment[0]})"]
            else:
                # ...the hobby of the mother of Alice ...
                subquery = [f"{placeholder}({f2.p_answer}, Y_{d})"] + f2.p_fragment
            answer = f"Y_{d}"

        return Fragment(q_fragment, subquery, answer)
