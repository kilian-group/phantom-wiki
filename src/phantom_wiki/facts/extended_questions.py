"""Extended question types: comparison, multi-constraint, and superlative questions.

These question types go beyond the base CFG (Who is / What is / How many) and support:

1. **Comparison**: "Who is older, <name_1> or <name_2>?"
   / "Who has more <relation_plural>, <name_1> or <name_2>?"

2. **Multi-constraint**: "Who is the person whose <attr_1> is <val_1> and whose <attr_2> is <val_2>?"

3. **Superlative**: "Who is the oldest <relation> of <name>?"
   / "Who has the most <relation_plural> among the <relation_plural> of <name>?"

Each function generates (question, prolog_query, answer_variable) tuples that can be
sampled and answered using the same pipeline as the base CFG questions.
"""

import re
from copy import copy

from numpy.random import Generator

from .attributes.constants import ATTRIBUTE_ALIASES, ATTRIBUTE_TYPES
from .database import Database
from .family.constants import FAMILY_RELATION_ALIAS, FAMILY_RELATION_DIFFICULTY, FAMILY_RELATION_PLURAL_ALIAS
from .friends.constants import (
    FRIENDSHIP_RELATION,
    FRIENDSHIP_RELATION_ALIAS,
    FRIENDSHIP_RELATION_PLURAL_ALIAS,
)
from .sample import RELATION_ALIAS, RELATION_PLURAL_ALIAS, get_relation_bank, get_vals_and_update_cache

# ---------------------------------------------------------------------------
# Question type identifiers
# ---------------------------------------------------------------------------
COMPARISON_AGE_TYPE = "comparison_age"
MULTI_CONSTRAINT_TYPE = "multi_constraint"
SUPERLATIVE_OLDEST_TYPE = "superlative_oldest"
SUPERLATIVE_YOUNGEST_TYPE = "superlative_youngest"
SUPERLATIVE_MOST_TYPE = "superlative_most"


def _count_variant_type(chain_depth: int, n_attrs: int) -> str:
    """Canonical name for a comparison_count variant.

    Examples:
        (0, 0) -> 'comparison_count'                       targets (1, 0)
        (1, 0) -> 'comparison_count_chain1'                targets (2, 0)
        (0, 2) -> 'comparison_count_mc2'                   targets (1, 2)
        (2, 3) -> 'comparison_count_chain2_mc3'            targets (3, 3)

    The +1 in the target hops comes from the aggregate_all that the
    count-comparison adds on top of the relation chain.
    """
    chain = f"_chain{chain_depth}" if chain_depth else ""
    mc = f"_mc{n_attrs}" if n_attrs else ""
    return f"comparison_count{chain}{mc}"


def build_comparison_count_variants(
    max_chain_depth: int,
    n_attrs_options: tuple[int, ...],
) -> dict[str, tuple[int, int]]:
    """Build the (variant name -> (chain_depth, n_attrs)) table.

    ``max_chain_depth`` is the largest chain length we'll emit (0..max_chain_depth
    inclusive). ``n_attrs_options`` lists the attribute-anchor sizes; 0 means a
    named anchor, >=2 means a multi-constraint anchor with that many attributes.
    """
    return {
        _count_variant_type(c, n): (c, n)
        for c in range(max_chain_depth + 1)
        for n in n_attrs_options
    }


def build_extended_question_types(
    count_variants: dict[str, tuple[int, int]],
) -> list[str]:
    return [
        COMPARISON_AGE_TYPE,
        *count_variants.keys(),
        MULTI_CONSTRAINT_TYPE,
        SUPERLATIVE_OLDEST_TYPE,
        SUPERLATIVE_YOUNGEST_TYPE,
        SUPERLATIVE_MOST_TYPE,
    ]


def build_extended_question_category(
    count_variants: dict[str, tuple[int, int]],
) -> dict[str, str]:
    """Map each extended-question type to its top-level category, used by the
    ``--question-types`` filter in the dataset generator."""
    return {
        COMPARISON_AGE_TYPE: "comparison_age",
        **{t: "comparison_count" for t in count_variants},
        MULTI_CONSTRAINT_TYPE: "multi_constraint",
        SUPERLATIVE_OLDEST_TYPE: "superlative",
        SUPERLATIVE_YOUNGEST_TYPE: "superlative",
        SUPERLATIVE_MOST_TYPE: "superlative",
    }


def is_extended_question(question: str) -> bool:
    """Returns True if the question matches an extended question pattern."""
    patterns = [
        r"^Who is older,",
        r"^Who is younger,",
        r"^Who has more ",
        r"^Who is the person whose .+ and whose ",
        r"^Who is the oldest ",
        r"^Who is the youngest ",
        r"^Who has the most ",
    ]
    return any(re.match(p, question.strip()) for p in patterns)


# ---------------------------------------------------------------------------
# Comparison: age
# ---------------------------------------------------------------------------
def sample_comparison_age_question(
    rng: Generator,
    db: Database,
    person_name_bank: list[str],
    person_name2attr_name_and_val: dict[str, list[tuple[str, str]]],
    num_sampling_attempts: int = 100,
) -> tuple[str, list[str]] | None:
    """Sample: 'Who is older, <name_1> or <name_2>?'

    Prolog query:
        dob("<name_1>", D1), dob("<name_2>", D2), D1 @< D2
    Answer variable: Result (the name of the older person)

    We resolve the answer directly: compare DOBs, whoever has the earlier DOB is older.
    The Prolog query is structured so that the answer is deterministic.
    """
    for _ in range(num_sampling_attempts):
        if len(person_name_bank) < 2:
            return None
        idxs = rng.choice(len(person_name_bank), size=2, replace=False)
        name1 = person_name_bank[idxs[0]]
        name2 = person_name_bank[idxs[1]]

        # Check both have DOBs
        dob1_results = db.query(f'dob("{name1}", D)')
        dob2_results = db.query(f'dob("{name2}", D)')
        if not dob1_results or not dob2_results:
            continue

        question = f"Who is older, {name1} or {name2}?"
        # Prolog: earlier DOB = older person
        # We use @< for string comparison (dates are in YYYY-MM-DD format)
        query = [
            f'dob("{name1}", D1)',
            f'dob("{name2}", D2)',
            "D1 @< D2",  # name1 is older if their DOB is earlier
        ]
        # The "answer" here needs special handling - it's a computed result
        # We'll store the answer as a sentinel and compute it during answer extraction
        return question, query

    return None


# ---------------------------------------------------------------------------
# Comparison: count of relations (chained + mc2 unified sampler)
# ---------------------------------------------------------------------------
def _build_count_branch(
    rng: Generator,
    db: Database,
    person_name_bank: list[str],
    person_name2attr_name_and_val: dict[str, list[tuple[str, str]]],
    person_name2relation_and_related: dict[str, list[tuple[str, str]]],
    num_procs: int,
    chain_depth: int,
    n_attrs: int,
    var_prefix: str,
    easy_mode: bool,
    num_sampling_attempts: int = 50,
) -> dict | None:
    """Build one branch of a count-comparison question.

    Walks ``chain_depth`` random relation hops from an anchor. The anchor is
    either a named person (``n_attrs=0``) or a person uniquely identified by
    ``n_attrs`` attribute constraints (``n_attrs >= 2``; 1 is unsupported here
    because it overlaps the base CFG path).

    Returns a dict with:
      - ``text``: natural-language description of the branch ("the sister of Alice")
      - ``atoms``: prolog atoms (anchor + chain)
      - ``endpoint_name``: name of the person at the end of the chain
      - ``endpoint_var``: prolog term that resolves to the endpoint
        (a quoted literal for chain_depth=0 named, otherwise a variable)
    Returns ``None`` if no valid branch can be sampled.
    """
    if n_attrs == 1:
        raise ValueError("n_attrs=1 is not supported in comparison_count branches")
    relation_bank = get_relation_bank(easy_mode)

    for _ in range(num_sampling_attempts):
        # Step 1: pick the anchor
        if n_attrs >= 2:
            person = person_name_bank[rng.integers(0, len(person_name_bank))]
            attrs = get_vals_and_update_cache(
                cache=person_name2attr_name_and_val,
                key=person,
                db=db,
                query_bank=ATTRIBUTE_TYPES,
                num_procs=num_procs,
            )
            if len(attrs) < n_attrs:
                continue
            idxs = rng.choice(len(attrs), size=n_attrs, replace=False)
            picked = [attrs[i] for i in idxs]  # list of (name, val)

            # Require uniqueness so the branch resolves to exactly one person
            uniqueness_q = ", ".join(
                f'{name}(X, "{val}")' for name, val in picked
            )
            if len(list(db.prolog.query(uniqueness_q))) != 1:
                continue

            anchor_var = f"{var_prefix}0"
            anchor_text = "the person " + " and ".join(
                f"whose {ATTRIBUTE_ALIASES[name]} is {val}" for name, val in picked
            )
            anchor_atoms = [
                f'{name}({anchor_var}, "{val}")' for name, val in picked
            ]
            current_var = anchor_var
            current_person = person
        else:
            person = person_name_bank[rng.integers(0, len(person_name_bank))]
            anchor_text = person
            anchor_atoms = []
            current_var = f'"{person}"'
            current_person = person

        # Step 2: walk chain_depth relation hops
        chain_atoms: list[str] = []
        chain_words: list[str] = []
        success = True
        for hop in range(chain_depth):
            relations = get_vals_and_update_cache(
                cache=person_name2relation_and_related,
                key=current_person,
                db=db,
                query_bank=relation_bank,
                num_procs=num_procs,
            )
            if not relations:
                success = False
                break
            rel, related = relations[rng.integers(0, len(relations))]
            rel_alias = RELATION_ALIAS.get(rel, rel)
            next_var = f"{var_prefix}{hop + 1}"
            chain_atoms.append(f"{rel}({current_var}, {next_var})")
            chain_words.append(f"the {rel_alias} of")
            current_var = next_var
            current_person = related

        if not success:
            continue

        # Step 3: assemble — outermost relation comes first in the question text
        if chain_words:
            text = " ".join(list(reversed(chain_words)) + [anchor_text])
        else:
            text = anchor_text

        return {
            "text": text,
            "atoms": anchor_atoms + chain_atoms,
            "endpoint_name": current_person,
            "endpoint_var": current_var,
        }

    return None


def sample_comparison_count_extended_question(
    rng: Generator,
    db: Database,
    person_name_bank: list[str],
    person_name2attr_name_and_val: dict[str, list[tuple[str, str]]],
    person_name2relation_and_related: dict[str, list[tuple[str, str]]],
    num_procs: int,
    chain_depth: int,
    n_attrs: int,
    easy_mode: bool = False,
    num_sampling_attempts: int = 100,
) -> tuple[str, list[str]] | None:
    """Sample: 'Who has more <relation_plural>, <left_branch> or <right_branch>?'

    Each branch walks ``chain_depth`` random relation hops from an anchor; the
    left branch's anchor may be a multi-constraint with ``n_attrs`` attributes
    (``n_attrs=0`` for a named anchor) so the constraint-axis cells get filled.
    The right branch is always named-anchored. The branch with more of
    ``<relation>`` at the endpoint wins.

    Prolog query format (the trailing ``LeftAns``/``RightAns`` unifications and
    bare ``CL > CR`` are read by ``get_extended_answer`` to extract the winner):

        <left anchor + chain atoms>,
        <right anchor + chain atoms>,
        aggregate_all(count, distinct(<rel>(<left_endpoint>, _)), CL),
        aggregate_all(count, distinct(<rel>(<right_endpoint>, _)), CR),
        LeftAns = <left_endpoint>,
        RightAns = <right_endpoint>,
        CL > CR
    """
    relation_bank = get_relation_bank(easy_mode)

    for _ in range(num_sampling_attempts):
        count_rel = relation_bank[rng.integers(0, len(relation_bank))]
        count_rel_plural = RELATION_PLURAL_ALIAS.get(count_rel, count_rel + "s")

        left = _build_count_branch(
            rng, db, person_name_bank, person_name2attr_name_and_val,
            person_name2relation_and_related, num_procs,
            chain_depth=chain_depth, n_attrs=n_attrs, var_prefix="LP", easy_mode=easy_mode,
        )
        if left is None:
            continue
        right = _build_count_branch(
            rng, db, person_name_bank, person_name2attr_name_and_val,
            person_name2relation_and_related, num_procs,
            chain_depth=chain_depth, n_attrs=0, var_prefix="RP", easy_mode=easy_mode,
        )
        if right is None:
            continue
        if left["endpoint_name"] == right["endpoint_name"]:
            continue

        cl = len(db.query(f'distinct({count_rel}("{left["endpoint_name"]}", X))'))
        cr = len(db.query(f'distinct({count_rel}("{right["endpoint_name"]}", X))'))
        if cl == 0 or cr == 0 or cl == cr:
            continue

        query = (
            left["atoms"]
            + right["atoms"]
            + [
                f'aggregate_all(count, distinct({count_rel}({left["endpoint_var"]}, _LX)), CL)',
                f'aggregate_all(count, distinct({count_rel}({right["endpoint_var"]}, _RX)), CR)',
                f'LeftAns = {left["endpoint_var"]}',
                f'RightAns = {right["endpoint_var"]}',
                "CL > CR",
            ]
        )
        question = (
            f"Who has more {count_rel_plural}, "
            f"{left['text']} or {right['text']}?"
        )
        return question, query

    return None


# ---------------------------------------------------------------------------
# Multi-constraint
# ---------------------------------------------------------------------------
def sample_multi_constraint_question(
    rng: Generator,
    db: Database,
    person_name_bank: list[str],
    person_name2attr_name_and_val: dict[str, list[tuple[str, str]]],
    num_procs: int,
    n_attrs: int,
    num_sampling_attempts: int = 100,
) -> tuple[str, list[str]] | None:
    """Sample: 'Who is the person whose <attr_1> is <val_1> and ... and whose <attr_N> is <val_N>?'

    ``n_attrs`` must be >= 2.
    Prolog query: <attr_1>(X, "<val_1>"), ..., <attr_N>(X, "<val_N>")
    Answer variable: X
    """
    if n_attrs < 2:
        raise ValueError(f"n_attrs must be >= 2 for multi_constraint, got {n_attrs}")

    for _ in range(num_sampling_attempts):
        person_name = person_name_bank[rng.integers(0, len(person_name_bank))]

        attr_name_and_vals: list[tuple[str, str]] = get_vals_and_update_cache(
            cache=person_name2attr_name_and_val,
            key=person_name,
            db=db,
            query_bank=ATTRIBUTE_TYPES,
            num_procs=num_procs,
        )

        if len(attr_name_and_vals) < n_attrs:
            continue

        idxs = rng.choice(len(attr_name_and_vals), size=n_attrs, replace=False)
        picked = [attr_name_and_vals[i] for i in idxs]

        question = (
            "Who is the person "
            + " and ".join(f"whose {ATTRIBUTE_ALIASES[name]} is {val}" for name, val in picked)
            + "?"
        )
        query = [f'{name}(X, "{val}")' for name, val in picked]
        return question, query

    return None


# ---------------------------------------------------------------------------
# Superlative: oldest / youngest relation
# ---------------------------------------------------------------------------
def sample_superlative_age_question(
    rng: Generator,
    db: Database,
    person_name_bank: list[str],
    person_name2relation_and_related: dict[str, list[tuple[str, str]]],
    easy_mode: bool = False,
    oldest: bool = True,
    num_sampling_attempts: int = 100,
) -> tuple[str, list[str]] | None:
    """Sample: 'Who is the oldest/youngest <relation> of <name>?'

    Prolog query (oldest):
        <relation>("<name>", X), dob(X, D),
        \\+ (<relation>("<name>", Y), dob(Y, D2), Y \\= X, D2 @< D)
    The negation ensures no other relative has an earlier DOB (i.e., X has the earliest = oldest).
    """
    relation_bank = get_relation_bank(easy_mode)

    for _ in range(num_sampling_attempts):
        person_name = person_name_bank[rng.integers(0, len(person_name_bank))]
        relation = relation_bank[rng.integers(0, len(relation_bank))]
        relation_alias = RELATION_ALIAS.get(relation, relation)

        # Check this person has at least 2 of this relation (otherwise superlative is trivial)
        results = db.query(f'distinct({relation}("{person_name}", X))')
        if len(results) < 2:
            continue

        adj = "oldest" if oldest else "youngest"
        op = "@<" if oldest else "@>"  # oldest = earliest DOB = @<, youngest = latest DOB = @>

        question = f"Who is the {adj} {relation_alias} of {person_name}?"
        # Prolog: find X such that no Y has a DOB that is earlier (oldest) / later (youngest)
        query = [
            f'{relation}("{person_name}", X)',
            "dob(X, D)",
            f'\\+ ({relation}("{person_name}", Y), dob(Y, D2), Y \\= X, D2 {op} D)',
        ]
        return question, query

    return None


# ---------------------------------------------------------------------------
# Superlative: most relations
# ---------------------------------------------------------------------------
def sample_superlative_most_question(
    rng: Generator,
    db: Database,
    person_name_bank: list[str],
    person_name2relation_and_related: dict[str, list[tuple[str, str]]],
    easy_mode: bool = False,
    num_sampling_attempts: int = 100,
) -> tuple[str, list[str]] | None:
    """Sample: 'Who has the most <relation_plural> among the <relation_plural_2> of <name>?'

    E.g., "Who has the most children among the siblings of Alice?"

    Prolog query:
        <relation_2>("<name>", X),
        aggregate_all(count, distinct(<relation_1>(X, Z)), C),
        \\+ (<relation_2>("<name>", Y), Y \\= X,
             aggregate_all(count, distinct(<relation_1>(Y, W)), C2), C2 > C)
    """
    relation_bank = get_relation_bank(easy_mode)

    for _ in range(num_sampling_attempts):
        person_name = person_name_bank[rng.integers(0, len(person_name_bank))]
        # relation_2 is the group relation (e.g., "siblings of name")
        relation_2 = relation_bank[rng.integers(0, len(relation_bank))]
        # relation_1 is what we count (e.g., "children")
        relation_1 = relation_bank[rng.integers(0, len(relation_bank))]

        relation_1_plural = RELATION_PLURAL_ALIAS.get(relation_1, relation_1 + "s")
        relation_2_plural = RELATION_PLURAL_ALIAS.get(relation_2, relation_2 + "s")

        # Check person has >= 2 of relation_2
        group = db.query(f'distinct({relation_2}("{person_name}", X))')
        if len(group) < 2:
            continue

        # Check at least one member has relation_1 and counts vary
        from ..utils import decode

        counts = {}
        for r in group:
            member = decode(r["X"])
            c = len(db.query(f'distinct({relation_1}("{member}", Z))'))
            counts[member] = c

        if max(counts.values()) == 0:
            continue
        # Ensure there's a unique maximum
        max_count = max(counts.values())
        if list(counts.values()).count(max_count) > 1:
            continue

        question = f"Who has the most {relation_1_plural} among the {relation_2_plural} of {person_name}?"
        query = [
            f'{relation_2}("{person_name}", X)',
            f"aggregate_all(count, distinct({relation_1}(X, Z)), C)",
            f'\\+ ({relation_2}("{person_name}", Y), Y \\= X, '
            f"aggregate_all(count, distinct({relation_1}(Y, W)), C2), C2 > C)",
        ]
        return question, query

    return None


# ---------------------------------------------------------------------------
# Master sampling function
# ---------------------------------------------------------------------------
def sample_extended_question(
    question_type: str,
    rng: Generator,
    db: Database,
    person_name_bank: list[str],
    person_name2attr_name_and_val: dict[str, list[tuple[str, str]]],
    person_name2relation_and_related: dict[str, list[tuple[str, str]]],
    num_procs: int,
    count_variants: dict[str, tuple[int, int]],
    multi_constraint_n_attrs: int,
    easy_mode: bool = False,
    num_sampling_attempts: int = 100,
) -> tuple[str, list[str]] | None:
    """Sample an extended question of the given type.

    ``count_variants`` is the build_comparison_count_variants() table; ``multi_constraint_n_attrs``
    is the N for the standalone "Who is the person whose A1 is V1 and ..." question.

    Returns (question_string, prolog_query_list) or None if sampling fails.
    """
    if question_type == COMPARISON_AGE_TYPE:
        return sample_comparison_age_question(
            rng, db, person_name_bank, person_name2attr_name_and_val, num_sampling_attempts
        )
    elif question_type in count_variants:
        chain_depth, n_attrs = count_variants[question_type]
        return sample_comparison_count_extended_question(
            rng, db, person_name_bank,
            person_name2attr_name_and_val, person_name2relation_and_related,
            num_procs,
            chain_depth=chain_depth, n_attrs=n_attrs,
            easy_mode=easy_mode, num_sampling_attempts=num_sampling_attempts,
        )
    elif question_type == MULTI_CONSTRAINT_TYPE:
        return sample_multi_constraint_question(
            rng, db, person_name_bank, person_name2attr_name_and_val, num_procs,
            n_attrs=multi_constraint_n_attrs,
            num_sampling_attempts=num_sampling_attempts,
        )
    elif question_type == SUPERLATIVE_OLDEST_TYPE:
        return sample_superlative_age_question(
            rng, db, person_name_bank, person_name2relation_and_related,
            easy_mode, True, num_sampling_attempts,
        )
    elif question_type == SUPERLATIVE_YOUNGEST_TYPE:
        return sample_superlative_age_question(
            rng, db, person_name_bank, person_name2relation_and_related,
            easy_mode, False, num_sampling_attempts,
        )
    elif question_type == SUPERLATIVE_MOST_TYPE:
        return sample_superlative_most_question(
            rng, db, person_name_bank, person_name2relation_and_related,
            easy_mode, num_sampling_attempts,
        )
    else:
        raise ValueError(f"Unknown extended question type: {question_type}")


def get_extended_answer(
    question: str,
    query: list[str],
    question_type: str,
    db: Database,
    count_variants: dict[str, tuple[int, int]],
) -> list[str]:
    """Execute an extended question's Prolog query and return the answer.

    For comparison questions, the answer is one of the two names.
    For multi-constraint, the answer is the person(s) matching all constraints.
    For superlative, the answer is the person with the extreme value.
    """
    from ..utils import decode

    if question_type == COMPARISON_AGE_TYPE:
        # Query: dob("name1", D1), dob("name2", D2), D1 @< D2
        # If this succeeds, name1 is older; otherwise name2 is older
        joined = ", ".join(query)
        results = list(db.prolog.query(joined))
        # Extract names from the question
        import re

        m = re.match(r"Who is older, (.+?) or (.+?)\?", question)
        if not m:
            return []
        name1, name2 = m.group(1), m.group(2)
        if results:
            return [name1]  # D1 @< D2 succeeded, name1 is older
        else:
            return [name2]

    elif question_type in count_variants:
        # Query ends with `LeftAns = ..., RightAns = ..., CL > CR`.
        # Forward run: extract LeftAns when left wins.
        # Reverse run (swap CL > CR for CR > CL): extract RightAns when right wins.
        forward = list(db.prolog.query(", ".join(query)))
        if forward:
            return sorted({decode(r["LeftAns"]) for r in forward if "LeftAns" in r})
        reverse_query = [
            "CR > CL" if a.strip() == "CL > CR" else a for a in query
        ]
        reverse = list(db.prolog.query(", ".join(reverse_query)))
        if reverse:
            return sorted({decode(r["RightAns"]) for r in reverse if "RightAns" in r})
        return []

    elif question_type == MULTI_CONSTRAINT_TYPE:
        joined = ", ".join(query)
        results = list(db.prolog.query(joined))
        return sorted({decode(r["X"]) for r in results})

    elif question_type in (SUPERLATIVE_OLDEST_TYPE, SUPERLATIVE_YOUNGEST_TYPE):
        joined = ", ".join(query)
        results = list(db.prolog.query(joined))
        return sorted({decode(r["X"]) for r in results})

    elif question_type == SUPERLATIVE_MOST_TYPE:
        joined = ", ".join(query)
        results = list(db.prolog.query(joined))
        return sorted({decode(r["X"]) for r in results})

    return []
