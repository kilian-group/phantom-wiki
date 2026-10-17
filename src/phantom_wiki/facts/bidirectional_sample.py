"""Bidirectional anchor sampling for question generation.

Eliminates positional bias by placing the sampling anchor at a random position
in the relation chain, then walking outward in both directions:
- Toward the head (answer): forward queries R("known", A)
- Toward the tail (start): inverse queries R(A, "known")
"""

import re
from copy import copy

from numpy.random import Generator

from ..utils import decode
from .attributes.constants import ATTRIBUTE_ALIASES, ATTRIBUTE_TYPES
from .database import Database
from .family.constants import FAMILY_RELATION_ALIAS, FAMILY_RELATION_DIFFICULTY, FAMILY_RELATION_PLURAL_ALIAS
from .friends.constants import (
    FRIENDSHIP_RELATION,
    FRIENDSHIP_RELATION_ALIAS,
    FRIENDSHIP_RELATION_PLURAL_ALIAS,
)
from .sample import (
    RELATION_ALIAS,
    RELATION_PLURAL_ALIAS,
    add_to_atom_assignments,
    get_inverse_vals_and_update_cache,
    get_relation_bank,
    get_vals_and_update_cache,
)

# Regex patterns for parsing query template items (same as sample.py)
RE_ATTR_NAME_Y_ATTR_VAL = re.compile(
    r"(<attribute_name>_\d+)\((Y_\d+), (<attribute_value>_\d+)\)"
)
RE_RELATION_NAME_Y = re.compile(
    r"(<relation>_\d+)\((<name>_\d+), (Y_\d+)\)"
)
RE_RELATION_Y_Y = re.compile(
    r"(<relation>_\d+)\((Y_\d+), (Y_\d+)\)"
)
RE_ATTR_NAME_Y_Y = re.compile(
    r"(<attribute_name>_\d+)\((Y_\d+), (Y_\d+)\)"
)
RE_AGG_RELATION_NAME_Y = re.compile(
    r"aggregate_all\(count, distinct\((<relation_plural>_\d+)\((<name>_\d+), (Y_\d+)\)\), (Count_\d+)\)"
)
RE_AGG_RELATION_Y_Y = re.compile(
    r"aggregate_all\(count, distinct\((<relation_plural>_\d+)\((Y_\d+), (Y_\d+)\)\), (Count_\d+)\)"
)
RE_ANY_PLACEHOLDER = re.compile(r"<\w+>_\d+")


def _parse_step(template_item: str) -> dict | None:
    """Parse a single query template item into a structured step dict.

    Returns a dict with keys:
        - 'type': one of 'attr_val', 'relation_name', 'relation_yy', 'attr_yy',
                  'agg_name', 'agg_yy', 'static'
        - 'raw': the original template string
        - 'first_var': the first Y variable (or <name> placeholder)
        - 'second_var': the second Y variable (or <attribute_value> placeholder)
        - 'match': the regex match object
    """
    if m := RE_ATTR_NAME_Y_ATTR_VAL.search(template_item):
        return {
            "type": "attr_val",
            "raw": template_item,
            "first_var": m.group(2),   # Y_\d+
            "second_var": None,        # attribute value, not a chain var
            "match": m,
        }
    elif m := RE_RELATION_NAME_Y.search(template_item):
        return {
            "type": "relation_name",
            "raw": template_item,
            "first_var": m.group(2),   # <name>_\d+
            "second_var": m.group(3),  # Y_\d+
            "match": m,
            "is_name_start": True,
        }
    elif m := RE_RELATION_Y_Y.search(template_item):
        return {
            "type": "relation_yy",
            "raw": template_item,
            "first_var": m.group(2),   # Y_\d+ (input, closer to tail)
            "second_var": m.group(3),  # Y_\d+ (output, closer to head)
            "match": m,
        }
    elif m := RE_ATTR_NAME_Y_Y.search(template_item):
        return {
            "type": "attr_yy",
            "raw": template_item,
            "first_var": m.group(2),   # Y_\d+ (input)
            "second_var": m.group(3),  # Y_\d+ (output, the answer var)
            "match": m,
        }
    elif m := RE_AGG_RELATION_NAME_Y.search(template_item):
        return {
            "type": "agg_name",
            "raw": template_item,
            "first_var": m.group(2),   # <name>_\d+
            "second_var": m.group(3),  # Y_\d+
            "match": m,
            "is_name_start": True,
        }
    elif m := RE_AGG_RELATION_Y_Y.search(template_item):
        return {
            "type": "agg_yy",
            "raw": template_item,
            "first_var": m.group(2),   # Y_\d+ (input)
            "second_var": m.group(3),  # Y_\d+ (output)
            "match": m,
        }
    else:
        return {
            "type": "static",
            "raw": template_item,
            "first_var": None,
            "second_var": None,
            "match": None,
        }


def _build_variable_chain(steps: list[dict]) -> list[str]:
    """Extract the ordered chain of Y variables from parsed steps.

    The chain runs from tail (starting person) to head (answer).
    Returns the ordered variable names, e.g. ['<name>_1', 'Y_2', 'Y_4', 'Y_6'].

    The chain is built by following the variable links in the template,
    starting from the tail (highest template index in the backward walk).
    """
    # Build adjacency: for each step, first_var → second_var
    # Template indices go: 0 = head side, n-1 = tail side
    # Steps are ordered: index 0 has vars near the head, index n-1 has vars near the tail
    #
    # Chain order (tail to head): step[n-1].first_var → step[n-1].second_var
    #                              = step[n-2].first_var → step[n-2].second_var ...
    chain = []
    # Process from tail to head (high index to low index)
    for step in reversed(steps):
        if step["type"] == "static":
            continue
        if step["first_var"] is not None and step["first_var"] not in chain:
            chain.append(step["first_var"])
        if step["second_var"] is not None and step["second_var"] not in chain:
            chain.append(step["second_var"])
    return chain


def _get_anchorable_slots(chain: list[str], steps: list[dict]) -> list[int]:
    """Return indices into the chain that are valid anchor positions.

    An anchorable slot is a Y_\\d+ variable from which all non-static steps
    in the template can be reached via dependency expansion.
    """
    num_non_static = sum(1 for s in steps if s["type"] != "static")
    anchorable = []
    for i, var in enumerate(chain):
        if not var.startswith("Y_"):
            continue
        # Check if anchoring here allows processing all steps
        order = _build_processing_order(steps, chain, i)
        if len(order) >= num_non_static:
            anchorable.append(i)
    return anchorable


def choose_anchor_index(
    anchorable_slots: list[int],
    rng: Generator,
    strategy: str = "random",
    _balanced_counter: list[int] | None = None,
) -> int:
    """Pick an anchor slot index from the anchorable positions.

    Args:
        anchorable_slots: Valid slot indices in the variable chain.
        rng: Random number generator.
        strategy: One of "random", "balanced", "start", "middle", "end".
        _balanced_counter: Mutable list [counter] for balanced strategy state.

    Returns:
        The chosen slot index (an element of anchorable_slots).
    """
    if not anchorable_slots:
        raise ValueError("No anchorable slots available")

    if strategy == "random":
        return anchorable_slots[rng.integers(0, len(anchorable_slots))]
    elif strategy == "balanced":
        if _balanced_counter is None:
            _balanced_counter = [0]
        idx = _balanced_counter[0] % len(anchorable_slots)
        _balanced_counter[0] += 1
        return anchorable_slots[idx]
    elif strategy == "start":
        return anchorable_slots[0]
    elif strategy == "middle":
        return anchorable_slots[len(anchorable_slots) // 2]
    elif strategy == "end":
        return anchorable_slots[-1]
    else:
        raise ValueError(f"Unknown anchor strategy: {strategy}")


def _process_step_forward(
    step: dict,
    known_var: str,
    target_var: str,
    query_assignments: dict[str, str],
    question_assignments: dict[str, str],
    atom_assignments: dict[str, str],
    rng: Generator,
    db: Database,
    person_name_bank: list[str],
    person_name2attr_name_and_val: dict[str, list[tuple[str, str]]],
    person_name2relation_and_related: dict[str, list[tuple[str, str]]],
    relation_bank: list[str],
    used_attrs_per_person: dict[str, set[tuple[str, str]]],
    num_procs: int,
) -> bool:
    """Process a chain step in the FORWARD direction (first arg known, find second).

    This is the same direction as the existing backward walk in sample.py.
    """
    m = step["match"]
    step_type = step["type"]

    if step_type == "relation_yy":
        relation, y1, y2 = m.group(1, 2, 3)
        person_name = atom_assignments[query_assignments[y1]]

        relation_and_related = get_vals_and_update_cache(
            cache=person_name2relation_and_related,
            key=person_name,
            db=db,
            query_bank=relation_bank,
            num_procs=num_procs,
        )
        if not relation_and_related:
            return False

        relation_choice, related_person = relation_and_related[rng.integers(0, len(relation_and_related))]
        query_assignments[relation] = relation_choice
        query_assignments[y2] = add_to_atom_assignments(atom_assignments, related_person)
        question_assignments[relation] = RELATION_ALIAS[relation_choice]
        return True

    elif step_type == "relation_name":
        relation, name, y = m.group(1, 2, 3)
        # In forward direction from a known person, the <name> is the first arg
        # and is already known. Find the second arg Y.
        person_name = atom_assignments[query_assignments[name]] if name in query_assignments else None
        if person_name is None:
            # <name> not yet bound — pick a random person
            person_name = person_name_bank[rng.integers(0, len(person_name_bank))]
            query_assignments[name] = f'"{person_name}"'

        relation_and_related = get_vals_and_update_cache(
            cache=person_name2relation_and_related,
            key=person_name,
            db=db,
            query_bank=relation_bank,
            num_procs=num_procs,
        )
        if not relation_and_related:
            return False

        relation_choice, related_person = relation_and_related[rng.integers(0, len(relation_and_related))]
        query_assignments[relation] = relation_choice
        query_assignments[y] = add_to_atom_assignments(atom_assignments, related_person)
        question_assignments[relation] = RELATION_ALIAS[relation_choice]
        question_assignments[name] = person_name
        return True

    elif step_type == "attr_yy":
        attribute_name, y1, y2 = m.group(1, 2, 3)
        person_name = atom_assignments[query_assignments[y1]]

        attr_name_and_vals = get_vals_and_update_cache(
            cache=person_name2attr_name_and_val,
            key=person_name,
            db=db,
            query_bank=ATTRIBUTE_TYPES,
            num_procs=num_procs,
        )
        if not attr_name_and_vals:
            return False

        attr_choice, attr_val = attr_name_and_vals[rng.integers(0, len(attr_name_and_vals))]
        query_assignments[attribute_name] = attr_choice
        question_assignments[attribute_name] = ATTRIBUTE_ALIASES[attr_choice]
        return True

    elif step_type == "attr_val":
        attribute_name, y, attribute_value = m.group(1, 2, 3)
        if y in query_assignments:
            person_name = atom_assignments[query_assignments[y]]
        else:
            person_name = person_name_bank[rng.integers(0, len(person_name_bank))]
            query_assignments[y] = add_to_atom_assignments(atom_assignments, person_name)

        attr_name_and_vals = get_vals_and_update_cache(
            cache=person_name2attr_name_and_val,
            key=person_name,
            db=db,
            query_bank=ATTRIBUTE_TYPES,
            num_procs=num_procs,
        )
        if not attr_name_and_vals:
            return False

        if used_attrs_per_person is not None:
            used = used_attrs_per_person.get(y, set())
            available = [(n, v) for n, v in attr_name_and_vals if (n, v) not in used]
            if not available:
                return False
            attr_name_and_vals = available

        attr_choice, attr_val = attr_name_and_vals[rng.integers(0, len(attr_name_and_vals))]
        query_assignments[attribute_name] = attr_choice
        query_assignments[attribute_value] = f'"{attr_val}"'

        if used_attrs_per_person is not None:
            used_attrs_per_person.setdefault(y, set()).add((attr_choice, attr_val))

        question_assignments[attribute_name] = ATTRIBUTE_ALIASES[attr_choice]
        question_assignments[attribute_value] = attr_val
        return True

    elif step_type in ("agg_name", "agg_yy"):
        # Aggregation steps — handle similarly to forward relation
        if step_type == "agg_name":
            relation_plural, name, y, count = m.group(1, 2, 3, 4)
            if name not in query_assignments:
                person_name = person_name_bank[rng.integers(0, len(person_name_bank))]
                query_assignments[name] = f'"{person_name}"'
            else:
                person_name = atom_assignments.get(
                    query_assignments[name],
                    query_assignments[name].strip('"'),
                )
        else:
            relation_plural, y1, y2, count = m.group(1, 2, 3, 4)
            person_name = atom_assignments[query_assignments[y1]]

        relation_and_related = get_vals_and_update_cache(
            cache=person_name2relation_and_related,
            key=person_name,
            db=db,
            query_bank=relation_bank,
            num_procs=num_procs,
        )
        if not relation_and_related:
            return False

        relation_choice, related_person = relation_and_related[rng.integers(0, len(relation_and_related))]
        query_assignments[relation_plural] = relation_choice
        question_assignments[relation_plural] = RELATION_PLURAL_ALIAS[relation_choice]
        if step_type == "agg_name":
            question_assignments[name] = person_name
        else:
            query_assignments[y2] = add_to_atom_assignments(atom_assignments, related_person)
        return True

    return False


def _process_step_inverse(
    step: dict,
    known_var: str,
    target_var: str,
    query_assignments: dict[str, str],
    question_assignments: dict[str, str],
    atom_assignments: dict[str, str],
    rng: Generator,
    db: Database,
    person_name_bank: list[str],
    person_name2attr_name_and_val: dict[str, list[tuple[str, str]]],
    person_name2inverse_relation: dict[str, list[tuple[str, str]]],
    relation_bank: list[str],
    used_attrs_per_person: dict[str, set[tuple[str, str]]],
    num_procs: int,
    inverse_map: dict[str, str] | None = None,
) -> bool:
    """Process a chain step in the INVERSE direction (second arg known, find first).

    Used when walking from the anchor toward the tail of the chain.
    Queries R(A, "known_person") to find the first argument.
    """
    m = step["match"]
    step_type = step["type"]

    if step_type == "relation_yy":
        relation, y1, y2 = m.group(1, 2, 3)
        # y2 (second arg) is known, we need to find y1 (first arg)
        person_name = atom_assignments[query_assignments[y2]]

        # Inverse lookup: find people X where R(X, person_name).
        # The cache may have been prewarmed with the full relation bank, so filter
        # results to only relations in relation_bank after the lookup.
        inverse_relations = [
            (r, p) for r, p in get_inverse_vals_and_update_cache(
                cache=person_name2inverse_relation,
                key=person_name,
                db=db,
                query_bank=relation_bank,
                num_procs=num_procs,
                inverse_map=inverse_map,
            )
            if r in relation_bank
        ]
        if not inverse_relations:
            return False

        relation_choice, found_person = inverse_relations[rng.integers(0, len(inverse_relations))]
        query_assignments[relation] = relation_choice
        query_assignments[y1] = add_to_atom_assignments(atom_assignments, found_person)
        question_assignments[relation] = RELATION_ALIAS[relation_choice]
        return True

    elif step_type == "relation_name":
        relation, name, y = m.group(1, 2, 3)
        # y (second arg) is known, we need to find <name> (first arg)
        person_name = atom_assignments[query_assignments[y]]

        inverse_relations = [
            (r, p) for r, p in get_inverse_vals_and_update_cache(
                cache=person_name2inverse_relation,
                key=person_name,
                db=db,
                query_bank=relation_bank,
                num_procs=num_procs,
                inverse_map=inverse_map,
            )
            if r in relation_bank
        ]
        if not inverse_relations:
            return False

        relation_choice, found_person = inverse_relations[rng.integers(0, len(inverse_relations))]
        query_assignments[relation] = relation_choice
        query_assignments[name] = f'"{found_person}"'
        question_assignments[relation] = RELATION_ALIAS[relation_choice]
        question_assignments[name] = found_person
        return True

    elif step_type == "attr_val":
        attribute_name, y, attribute_value = m.group(1, 2, 3)
        # The Y variable should already be bound (by the chain walk)
        if y not in query_assignments:
            return False
        person_name = atom_assignments[query_assignments[y]]

        attr_name_and_vals = get_vals_and_update_cache(
            cache=person_name2attr_name_and_val,
            key=person_name,
            db=db,
            query_bank=ATTRIBUTE_TYPES,
            num_procs=num_procs,
        )
        if not attr_name_and_vals:
            return False

        if used_attrs_per_person is not None:
            used = used_attrs_per_person.get(y, set())
            available = [(n, v) for n, v in attr_name_and_vals if (n, v) not in used]
            if not available:
                return False
            attr_name_and_vals = available

        attr_choice, attr_val = attr_name_and_vals[rng.integers(0, len(attr_name_and_vals))]
        query_assignments[attribute_name] = attr_choice
        query_assignments[attribute_value] = f'"{attr_val}"'

        if used_attrs_per_person is not None:
            used_attrs_per_person.setdefault(y, set()).add((attr_choice, attr_val))

        question_assignments[attribute_name] = ATTRIBUTE_ALIASES[attr_choice]
        question_assignments[attribute_value] = attr_val
        return True

    elif step_type == "attr_yy":
        attribute_name, y1, y2 = m.group(1, 2, 3)
        # In inverse direction, y2 is known. y1 needs to be discovered.
        # But attr_yy is a terminal query — it just reads an attribute.
        # If y1 is already bound, process normally.
        if y1 in query_assignments:
            person_name = atom_assignments[query_assignments[y1]]
        else:
            return False

        attr_name_and_vals = get_vals_and_update_cache(
            cache=person_name2attr_name_and_val,
            key=person_name,
            db=db,
            query_bank=ATTRIBUTE_TYPES,
            num_procs=num_procs,
        )
        if not attr_name_and_vals:
            return False

        attr_choice, attr_val = attr_name_and_vals[rng.integers(0, len(attr_name_and_vals))]
        query_assignments[attribute_name] = attr_choice
        question_assignments[attribute_name] = ATTRIBUTE_ALIASES[attr_choice]
        return True

    elif step_type in ("agg_name", "agg_yy"):
        if step_type == "agg_name":
            relation_plural, name, y, count = m.group(1, 2, 3, 4)
            # y is known, find <name>
            person_name = atom_assignments[query_assignments[y]]

            inverse_relations = [
                (r, p) for r, p in get_inverse_vals_and_update_cache(
                    cache=person_name2inverse_relation,
                    key=person_name,
                    db=db,
                    query_bank=relation_bank,
                    num_procs=num_procs,
                )
                if r in relation_bank
            ]
            if not inverse_relations:
                return False

            relation_choice, found_person = inverse_relations[rng.integers(0, len(inverse_relations))]
            query_assignments[relation_plural] = relation_choice
            query_assignments[name] = f'"{found_person}"'
            question_assignments[relation_plural] = RELATION_PLURAL_ALIAS[relation_choice]
            question_assignments[name] = found_person
            return True
        else:
            relation_plural, y1, y2, count = m.group(1, 2, 3, 4)
            # y2 is known, find y1
            person_name = atom_assignments[query_assignments[y2]]

            inverse_relations = [
                (r, p) for r, p in get_inverse_vals_and_update_cache(
                    cache=person_name2inverse_relation,
                    key=person_name,
                    db=db,
                    query_bank=relation_bank,
                    num_procs=num_procs,
                )
                if r in relation_bank
            ]
            if not inverse_relations:
                return False

            relation_choice, found_person = inverse_relations[rng.integers(0, len(inverse_relations))]
            query_assignments[relation_plural] = relation_choice
            query_assignments[y1] = add_to_atom_assignments(atom_assignments, found_person)
            question_assignments[relation_plural] = RELATION_PLURAL_ALIAS[relation_choice]
            return True

    return False


def _all_placeholders_assigned(query_item: str, query_assignments: dict[str, str]) -> bool:
    """Check if all <placeholder>_N tokens in a query item are already in query_assignments."""
    placeholders = RE_ANY_PLACEHOLDER.findall(query_item)
    return all(p in query_assignments for p in placeholders)


def _build_processing_order(
    steps: list[dict],
    chain: list[str],
    anchor_slot: int,
) -> list[tuple[int, str]]:
    """Build dependency-ordered processing sequence from the anchor outward.

    Uses BFS expansion: start from the anchor variable, find steps that have
    exactly one known variable (the anchor or a previously discovered variable),
    process those to discover new variables, repeat.

    Returns list of (template_index, direction) where direction is "forward"
    or "inverse".
    """
    anchor_var = chain[anchor_slot]
    known_vars = {anchor_var}
    processed = set()
    order = []

    # Keep expanding until no more steps can be processed
    changed = True
    while changed:
        changed = False
        for idx, step in enumerate(steps):
            if idx in processed:
                continue
            if step["type"] == "static":
                processed.add(idx)
                continue

            fv = step["first_var"]
            sv = step["second_var"]
            fv_known = fv is not None and fv in known_vars
            sv_known = sv is not None and sv in known_vars

            if step["type"] == "attr_val":
                # attr_val(Y, <attr_val>): needs Y to be known
                if fv_known:
                    order.append((idx, "forward"))
                    processed.add(idx)
                    changed = True
                continue

            if step["type"] == "attr_yy":
                # attr_yy(Y_in, Y_out): needs Y_in to be known
                if fv_known:
                    order.append((idx, "forward"))
                    if sv is not None:
                        known_vars.add(sv)
                    processed.add(idx)
                    changed = True
                continue

            if step["type"] in ("relation_yy", "relation_name"):
                if fv_known and not sv_known:
                    # Forward: first arg known, discover second
                    order.append((idx, "forward"))
                    if sv is not None:
                        known_vars.add(sv)
                    if fv is not None and not fv.startswith("Y_"):
                        known_vars.add(fv)
                    processed.add(idx)
                    changed = True
                elif sv_known and not fv_known:
                    # Inverse: second arg known, discover first
                    order.append((idx, "inverse"))
                    if fv is not None:
                        known_vars.add(fv)
                    processed.add(idx)
                    changed = True
                elif fv_known and sv_known:
                    # Both known — skip (or process as validation)
                    processed.add(idx)
                    changed = True
                continue

            if step["type"] in ("agg_name", "agg_yy"):
                if step["type"] == "agg_name":
                    # agg_name(<name>, Y): if <name> known → forward; if Y known → inverse
                    name_var = fv
                    y_var = sv
                    if name_var in known_vars or (name_var is not None and name_var in known_vars):
                        order.append((idx, "forward"))
                        if y_var:
                            known_vars.add(y_var)
                        processed.add(idx)
                        changed = True
                    elif y_var in known_vars:
                        order.append((idx, "inverse"))
                        if name_var:
                            known_vars.add(name_var)
                        processed.add(idx)
                        changed = True
                else:
                    # agg_yy(Y_in, Y_out)
                    if fv_known and not sv_known:
                        order.append((idx, "forward"))
                        if sv:
                            known_vars.add(sv)
                        processed.add(idx)
                        changed = True
                    elif sv_known and not fv_known:
                        order.append((idx, "inverse"))
                        if fv:
                            known_vars.add(fv)
                        processed.add(idx)
                        changed = True
                    elif fv_known and sv_known:
                        processed.add(idx)
                        changed = True
                continue

    return order


def sample_question_bidirectional(
    question_template: list[str],
    query_template: list[str],
    rng: Generator,
    db: Database,
    person_name_bank: list[str],
    person_name2attr_name_and_val: dict[str, list[tuple[str, str]]],
    person_name2relation_and_related: dict[str, list[tuple[str, str]]],
    person_name2inverse_relation: dict[str, list[tuple[str, str]]],
    inverse_map: dict[str, str],
    num_procs: int,
    easy_mode: bool = False,
    num_sampling_attempts: int = 100,
    anchor_strategy: str = "random",
    answer_position: str = "head",
    _balanced_counter: list[int] | None = None,
) -> tuple[str, list[str], dict] | None:
    """Sample a question using bidirectional anchor placement.

    Instead of always starting from the tail of the relation chain (backward walk),
    this picks a random anchor position and walks outward in both directions:
    - Toward the head (answer): uses forward relation queries
    - Toward the tail (start): uses inverse relation queries

    Args:
        question_template: Question template as list of CFG terminals.
        query_template: Query template as list of Prolog statements.
        rng: Random number generator.
        db: The Prolog database.
        person_name_bank: List of all person names in the database.
        person_name2attr_name_and_val: Forward attribute cache.
        person_name2relation_and_related: Forward relation cache.
        person_name2inverse_relation: Inverse relation cache.
        inverse_map: Dict mapping relation to its inverse predicate name.
        easy_mode: Whether to use only easy relations.
        num_sampling_attempts: Max attempts to sample a valid question.
        anchor_strategy: How to choose the anchor position.
        answer_position: Which end of the chain is the answer ("head", "tail", "random").
        _balanced_counter: Mutable state for "balanced" strategy.

    Returns:
        Tuple of (question_string, query_list, sampling_metadata) or None if
        all attempts fail.
    """
    relation_bank = get_relation_bank(easy_mode)

    # 1. Parse all template steps
    steps = [_parse_step(item) for item in query_template]

    # 2. Build the variable chain (tail to head)
    chain = _build_variable_chain(steps)

    # 3. Find anchorable slots
    anchorable = _get_anchorable_slots(chain, steps)
    if not anchorable:
        return None

    # 4. Choose anchor slot
    anchor_slot = choose_anchor_index(anchorable, rng, anchor_strategy, _balanced_counter)
    anchor_var = chain[anchor_slot]

    # 5. Build dependency-ordered processing sequence
    processing_order = _build_processing_order(steps, chain, anchor_slot)

    # 6. Try sampling
    for attempt in range(num_sampling_attempts):
        atom_assignments: dict[str, str] = {}
        query_assignments: dict[str, str] = {}
        question_assignments: dict[str, str] = {}
        used_attrs_per_person: dict[str, set[tuple[str, str]]] = {}

        # Bind the anchor variable to a random person
        anchor_person = person_name_bank[rng.integers(0, len(person_name_bank))]
        query_assignments[anchor_var] = add_to_atom_assignments(
            atom_assignments, anchor_person
        )

        success = True

        for idx, direction in processing_order:
            step = steps[idx]
            if direction == "forward":
                ok = _process_step_forward(
                    step, None, None,
                    query_assignments, question_assignments, atom_assignments,
                    rng, db, person_name_bank,
                    person_name2attr_name_and_val, person_name2relation_and_related,
                    relation_bank, used_attrs_per_person,
                    num_procs,
                )
            else:  # inverse
                ok = _process_step_inverse(
                    step, None, None,
                    query_assignments, question_assignments, atom_assignments,
                    rng, db, person_name_bank,
                    person_name2attr_name_and_val, person_name2inverse_relation,
                    relation_bank, used_attrs_per_person,
                    num_procs,
                    inverse_map=inverse_map,
                )
            if not ok:
                success = False
                break

        if not success:
            continue

        # 7. Assemble the final query and question
        joined_query = ",,".join(query_template)
        for placeholder, sampled_value in query_assignments.items():
            if sampled_value not in atom_assignments:
                joined_query = joined_query.replace(placeholder, sampled_value)
        query = joined_query.split(",,")

        question = " ".join(question_template[:-1]) + question_template[-1]
        for placeholder, sampled_value in question_assignments.items():
            question = question.replace(placeholder, sampled_value)

        # Determine answer position
        actual_answer_position = answer_position
        if answer_position == "random":
            actual_answer_position = rng.choice(["head", "tail"])

        # Determine answer slot index and polarity
        answer_slot_index = 0 if actual_answer_position == "head" else len(chain) - 1
        if anchor_slot == answer_slot_index:
            polarity = "same"
        elif anchor_slot < answer_slot_index:
            polarity = "same_side"
        else:
            polarity = "opposite"

        # Determine anchor position label
        if anchor_slot == 0:
            anchor_position_label = "start"
        elif anchor_slot == len(chain) - 1:
            anchor_position_label = "end"
        else:
            anchor_position_label = "middle"

        # Build sampling metadata
        metadata = {
            "method": "bidirectional",
            "anchor_position": anchor_position_label,
            "anchor_slot_index": int(anchor_slot),
            "anchor_person": anchor_person,
            "answer_position": actual_answer_position,
            "answer_slot_index": answer_slot_index,
            "polarity": polarity,
            "chain_length": len(chain) - 1,
            "chain_variables": chain,
        }

        return question, query, metadata

    return None
