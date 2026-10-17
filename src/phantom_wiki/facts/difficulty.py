"""Structured difficulty computation for Prolog query templates.

Decomposes difficulty into two independent axes:

- **hops**: number of base-level Prolog predicate evaluations needed to
  traverse the relation chain.  Derived relations (e.g. ``nephew``) are
  recursively expanded into base predicates and counted.
- **constraints**: number of attribute-filter predicates (``hobby``, ``job``,
  ``dob``) that appear in the query.

A scalar **composite** (hops + constraints) is provided for simple sorting.
"""

from __future__ import annotations

import functools
import re

from .attributes.constants import ATTRIBUTE_TYPES
from .family.constants import FAMILY_RELATION_DIFFICULTY
from .friends.constants import FRIENDSHIP_RELATION

# Predicates that are gender filters, not relational hops
GENDER_FILTERS = frozenset(["male", "female", "nonbinary", "gender"])


@functools.lru_cache(maxsize=1)
def derive_relation_hop_counts() -> dict[str, int]:
    """Return {relation_name: hop_count} sourced from FAMILY_RELATION_DIFFICULTY
    plus friendship relations (1 hop each).
    """
    hops = dict(FAMILY_RELATION_DIFFICULTY)
    for rel in FRIENDSHIP_RELATION:
        hops[rel] = 1
    return hops


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

# Attribute predicates that count as constraints (not hops)
_ATTRIBUTE_SET = frozenset(ATTRIBUTE_TYPES) | {"dob", "date_of_birth"}
_AGGREGATE_RE = re.compile(r"aggregate_all\(")
_COMPARISON_RE = re.compile(r"@[<>]|\\+|\\=|==|>|<")


def _parse_predicate(query_atom: str) -> tuple[str | None, list[str]]:
    """Extract predicate name and arguments from a Prolog query atom.

    Returns (name, args) or (None, []) for non-predicate atoms.
    """
    query_atom = query_atom.strip()
    if not query_atom:
        return None, []
    if query_atom.startswith("\\+"):
        return None, []
    if _COMPARISON_RE.match(query_atom):
        return None, []
    m = re.match(r"(\w+)\(", query_atom)
    if not m:
        return None, []

    name = m.group(1)
    # Extract the argument string (everything between the outermost parens)
    start = m.end()  # position right after "name("
    depth = 1
    i = start
    while i < len(query_atom) and depth > 0:
        ch = query_atom[i]
        if ch == '"':
            i += 1
            while i < len(query_atom) and query_atom[i] != '"':
                i += 1
        elif ch == "'":
            i += 1
            while i < len(query_atom) and query_atom[i] != "'":
                i += 1
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                break
        i += 1

    arg_str = query_atom[start:i]

    # Split args on commas, respecting quotes and nested parens
    args: list[str] = []
    current: list[str] = []
    depth = 0
    in_quote = False
    quote_char = ""
    for ch in arg_str:
        if in_quote:
            current.append(ch)
            if ch == quote_char:
                in_quote = False
        elif ch in ('"', "'"):
            in_quote = True
            quote_char = ch
            current.append(ch)
        elif ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            args.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        args.append("".join(current).strip())

    return name, args


def _parse_predicate_name(query_atom: str) -> str | None:
    """Extract the predicate name from a Prolog query atom."""
    name, _ = _parse_predicate(query_atom)
    return name


def _is_quoted_literal(s: str) -> bool:
    """True if the string is a quoted literal value (double or single quotes)."""
    s = s.strip()
    return (len(s) >= 2 and s[0] == '"' and s[-1] == '"') or \
           (len(s) >= 2 and s[0] == "'" and s[-1] == "'")


_VARIABLE_RE = re.compile(r"\b([A-Z][A-Za-z0-9_]*)\b")
_QUOTED_STR_RE = re.compile(r'"[^"]*"')


def _extract_variables(atom: str) -> set[str]:
    """Extract all Prolog variable names from an atom (uppercase-starting identifiers).

    Quoted string literals (e.g. person names like "Deane Smock") are stripped
    first so their words are not mistaken for Prolog variables.
    """
    atom_no_strings = _QUOTED_STR_RE.sub("", atom)
    return set(_VARIABLE_RE.findall(atom_no_strings)) - GENDER_FILTERS


_BARE_CMP_RE = re.compile(r"@[<>]|>=|<=|=:=|==|>|<")


def _is_bare_comparison_atom(atom: str) -> bool:
    """True for top-level comparison-operator atoms like ``D1 @< D2`` or ``C1 > C2``.

    Excludes atoms with parens (predicates, negations) so comparison operators
    nested inside ``\\+ (... @< ...)`` aggregation plumbing are not mistaken
    for top-level comparisons.
    """
    a = atom.strip()
    if a.startswith("\\+"):
        return False
    if "(" in a:
        return False
    return bool(_BARE_CMP_RE.search(a))


def _split_comparison_branches(query_template: list[str]) -> list[list[str]] | None:
    """Split a comparison query into K parallel branches.

    Detects two binder shapes:

    - ``dob(Entity, V)`` where ``V`` flows into a top-level ``@<``/``@>``
      comparison.  This is *plumbing* — the atom is excluded from branch
      content; the branch's chain is whatever connects to ``Entity``.
    - ``aggregate_all(count, distinct(P(Entity, _)), V)`` where ``V`` flows
      into a top-level numeric comparison.  This is *content* — the atom is
      retained in the branch and contributes ``hop_counts[P]`` hops.

    Returns a list of branch atom lists (one per binder), or ``None`` if no
    two-branch comparison pattern is present.  Comparison-operator atoms are
    excluded from all branches.
    """
    cmp_atom_idx: set[int] = set()
    cmp_vars: set[str] = set()
    for i, atom in enumerate(query_template):
        if _is_bare_comparison_atom(atom):
            cmp_atom_idx.add(i)
            cmp_vars.update(_extract_variables(atom))
    if not cmp_vars:
        return None

    # binder_info: (atom_idx, kind, entity_token).  entity_token may be a
    # variable name (e.g. ``Y_2``) or a quoted literal (e.g. ``"Alice"``).
    binder_info: list[tuple[int, str, str]] = []
    for i, atom in enumerate(query_template):
        if i in cmp_atom_idx:
            continue
        pred, args = _parse_predicate(atom)
        if pred == "dob" and len(args) >= 2 and args[1].strip() in cmp_vars:
            binder_info.append((i, "dob_plumbing", args[0].strip()))
        elif pred == "aggregate_all" and len(args) >= 3 and args[-1].strip() in cmp_vars:
            distinct_pred, distinct_args = _parse_predicate(args[1])
            if distinct_pred == "distinct" and distinct_args:
                inner_pred, inner_args = _parse_predicate(distinct_args[0])
                if inner_pred and inner_args:
                    binder_info.append((i, "aggregate_content", inner_args[0].strip()))

    if len(binder_info) < 2:
        return None

    branch_count = len(binder_info)
    sentinels = [f"_BRANCH_{k}" for k in range(branch_count)]
    parent: dict[str, str] = {s: s for s in sentinels}

    def find(x: str) -> str:
        while parent.get(x, x) != x:
            parent[x] = parent.get(parent[x], parent[x])
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            if rb in sentinels:
                parent[ra] = rb
            else:
                parent[rb] = ra

    # Seed each branch sentinel with its binder's entity (when it's a variable).
    branches: list[list[str]] = [[] for _ in range(branch_count)]
    binder_skip_idx: set[int] = set()
    for k, (idx, kind, entity) in enumerate(binder_info):
        binder_skip_idx.add(idx)
        if not _is_quoted_literal(entity):
            parent.setdefault(entity, sentinels[k])
            union(entity, sentinels[k])
        if kind == "aggregate_content":
            branches[k].append(query_template[idx])

    # Collect content atoms (excluding comparison plumbing and binders).
    content_atoms: list[tuple[str, set[str]]] = []
    for i, atom in enumerate(query_template):
        if i in cmp_atom_idx or i in binder_skip_idx:
            continue
        atom_vars = _extract_variables(atom) - cmp_vars
        content_atoms.append((atom, atom_vars))

    for _, atom_vars in content_atoms:
        vlist = [v for v in atom_vars if not v.startswith("Cmp")]
        for i in range(1, len(vlist)):
            union(vlist[0], vlist[i])

    for atom, atom_vars in content_atoms:
        vlist = [v for v in atom_vars if not v.startswith("Cmp")]
        if not vlist:
            continue
        root = find(vlist[0])
        if root in sentinels:
            branches[sentinels.index(root)].append(atom)

    return branches


def _score_atoms(atoms: list[str], hop_counts: dict[str, int]) -> tuple[int, int]:
    """Compute (hops, constraints) for a list of Prolog query atoms."""
    hops = 0
    constraints = 0

    for atom in atoms:
        pred, args = _parse_predicate(atom)
        if pred is None:
            continue

        if pred == "aggregate_all":
            inner = re.search(r"distinct\((\w+)\(", atom)
            if inner:
                inner_pred = inner.group(1)
                if inner_pred in _ATTRIBUTE_SET:
                    constraints += 1
                elif inner_pred in hop_counts:
                    hops += hop_counts[inner_pred]
                else:
                    hops += 1
            else:
                hops += 1
            continue

        if pred in _ATTRIBUTE_SET:
            if len(args) >= 2 and _is_quoted_literal(args[1]):
                constraints += 1
        elif pred in hop_counts:
            hops += hop_counts[pred]
        elif pred in GENDER_FILTERS:
            pass
        else:
            hops += 1

    return hops, constraints


def _compute_constraint_position(
    query_template: list[str],
    answer_var: str,
    hop_counts: dict[str, int],
) -> int | None:
    """Hop-weighted shortest-path distance from ``answer_var`` to a
    literal-bound (constrained) attribute var. ``hop_counts[rel]`` weights
    each relation edge — so ``grandfather`` contributes 2. ``aggregate_all``
    edges use the inner relation's hop count. Attribute *extraction* atoms
    (var second arg) contribute 0. Returns ``None`` if no constraint or no
    path. Anchor-end constraints in linear chains yield position == hops.
    """
    if answer_var is None:
        return None

    constrained: set[str] = set()
    for atom in query_template:
        pred, args = _parse_predicate(atom)
        if pred in _ATTRIBUTE_SET and len(args) >= 2 and _is_quoted_literal(args[1]):
            constrained.add(args[0].strip())
    if not constrained:
        return None
    if answer_var in constrained:
        return 0

    import heapq
    from collections import defaultdict

    adj: dict[str, list[tuple[str, int]]] = defaultdict(list)

    def _add_edge(a: str, b: str, cost: int) -> None:
        if _is_quoted_literal(a) or _is_quoted_literal(b):
            return
        adj[a].append((b, cost))
        adj[b].append((a, cost))

    for atom in query_template:
        pred, args = _parse_predicate(atom)
        if pred in hop_counts and len(args) == 2:
            _add_edge(args[0].strip(), args[1].strip(), hop_counts[pred])
        elif pred in _ATTRIBUTE_SET and len(args) >= 2 and not _is_quoted_literal(args[1]):
            _add_edge(args[0].strip(), args[1].strip(), 0)
        elif pred == "aggregate_all" and len(args) >= 3:
            inner = re.search(r"distinct\((\w+)\(([^,]+),\s*([^)]+)\)\)", atom)
            if inner and inner.group(1) in hop_counts:
                _add_edge(inner.group(2).strip(), args[-1].strip(), hop_counts[inner.group(1)])

    dist: dict[str, int] = {answer_var: 0}
    heap: list[tuple[int, str]] = [(0, answer_var)]
    while heap:
        d, node = heapq.heappop(heap)
        if d > dist.get(node, float("inf")):
            continue
        if node in constrained:
            return d
        for nb, cost in adj[node]:
            nd = d + cost
            if nd < dist.get(nb, float("inf")):
                dist[nb] = nd
                heapq.heappush(heap, (nd, nb))
    return None


def compute_difficulty(query_template: list[str], *, answer_var: str | None = None) -> dict:
    """Compute structured difficulty from a Prolog query template.

    For two-branch comparison queries (CmpDL/CmpDR pattern), hops and
    constraints are computed per-branch and the **max** of each axis is
    used — an agent can resolve both branches in parallel, so difficulty
    is determined by the harder branch, not the sum.

    When ``answer_var`` is provided, ``constraint_position`` is added: the
    hop-weighted distance from the answer to the constrained var (see
    :func:`_compute_constraint_position`).

    Returns dict with keys ``hops``, ``constraints``, ``composite``, and
    (when ``answer_var`` is provided) ``constraint_position``.
    """
    hop_counts = derive_relation_hop_counts()

    branches = _split_comparison_branches(query_template)
    if branches is not None:
        scores = [_score_atoms(b, hop_counts) for b in branches]
        hops = max((s[0] for s in scores), default=0)
        constraints = max((s[1] for s in scores), default=0)
    else:
        hops, constraints = _score_atoms(query_template, hop_counts)

    result = {
        "hops": hops,
        "constraints": constraints,
        "composite": hops + constraints,
    }
    if answer_var is not None:
        result["constraint_position"] = _compute_constraint_position(
            query_template, answer_var, hop_counts
        )
    return result
