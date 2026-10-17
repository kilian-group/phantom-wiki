"""Tests for the structured difficulty computation module."""

import json
import os

import pytest

from phantom_wiki.facts.difficulty import (
    compute_difficulty,
    derive_relation_hop_counts,
)


# ---------------------------------------------------------------------------
# Hop-count auto-derivation
# ---------------------------------------------------------------------------


class TestDeriveRelationHopCounts:
    """Verify hop counts are derived from Prolog rules, not hardcoded."""

    @pytest.fixture(autouse=True)
    def _hop_counts(self):
        derive_relation_hop_counts.cache_clear()
        self.hops = derive_relation_hop_counts()

    def test_base_predicate_parent(self):
        assert self.hops["parent"] == 1

    def test_base_predicate_child(self):
        assert self.hops["child"] == 1

    def test_base_predicate_friend(self):
        assert self.hops["friend"] == 1

    def test_sibling_is_semantic_base_fact(self):
        # sibling is a semantic base fact → 1 hop
        assert self.hops["sibling"] == 1

    def test_brother_sibling_plus_gender(self):
        # brother(X,Y) :- sibling(X,Y), male(Y) → 1 hop (gender filter excluded)
        assert self.hops["brother"] == 1

    def test_sister_sibling_plus_gender(self):
        assert self.hops["sister"] == 1

    def test_mother_parent_plus_gender(self):
        # mother(X,Y) :- parent(X,Y), female(Y) → 1 hop
        assert self.hops["mother"] == 1

    def test_father_parent_plus_gender(self):
        assert self.hops["father"] == 1

    def test_nephew(self):
        assert self.hops["nephew"] == 2

    def test_niece(self):
        assert self.hops["niece"] == 2

    def test_grandparent(self):
        assert self.hops["grandparent"] == 2

    def test_cousin(self):
        assert self.hops["cousin"] == 3

    def test_aunt(self):
        assert self.hops["aunt"] == 2

    def test_uncle(self):
        assert self.hops["uncle"] == 2

    def test_great_grandparent(self):
        assert self.hops["great_grandparent"] == 3

    def test_second_cousin(self):
        assert self.hops["female_second_cousin"] == 5

    def test_wife(self):
        assert self.hops["wife"] == 1

    def test_husband(self):
        assert self.hops["husband"] == 1

    def test_all_relations_present(self):
        from phantom_wiki.facts.family.constants import FAMILY_RELATION_DIFFICULTY
        from phantom_wiki.facts.friends.constants import FRIENDSHIP_RELATION

        expected = set(FAMILY_RELATION_DIFFICULTY.keys()) | set(FRIENDSHIP_RELATION)
        assert expected.issubset(set(self.hops.keys()))


# ---------------------------------------------------------------------------
# compute_difficulty()
# ---------------------------------------------------------------------------


class TestComputeDifficulty:
    def test_simple_one_hop_friend(self):
        query = ['friend("David", Y_2)']
        d = compute_difficulty(query)
        assert d["hops"] == 1
        assert d["constraints"] == 0
        assert d["composite"] == 1

    def test_compound_relation_nephew(self):
        # nephew decomposes to sibling + son → 2 hops
        query = ['nephew("David", Y_2)']
        d = compute_difficulty(query)
        assert d["hops"] == 2
        assert d["constraints"] == 0

    def test_chain_nephew_of_friend(self):
        # nephew(Y_2, Y_3), friend("David", Y_2) → nephew(2) + friend(1) = 3
        query = ['nephew(Y_2, Y_3)', 'friend("David", Y_2)']
        d = compute_difficulty(query)
        assert d["hops"] == 3
        assert d["constraints"] == 0

    def test_single_constraint_hobby(self):
        query = ['hobby(Y_2, "reading")']
        d = compute_difficulty(query)
        assert d["hops"] == 0
        assert d["constraints"] == 1
        assert d["composite"] == 1

    def test_multi_constraint(self):
        query = ['hobby(Y_2, "reading")', 'job(Y_2, "teacher")']
        d = compute_difficulty(query)
        assert d["hops"] == 0
        assert d["constraints"] == 2
        assert d["composite"] == 2

    def test_chain_with_constraint(self):
        # friend(1 hop) + hobby(1 constraint)
        query = ['friend(Y_2, Y_3)', 'hobby(Y_2, "reading")']
        d = compute_difficulty(query)
        assert d["hops"] == 1
        assert d["constraints"] == 1
        assert d["composite"] == 2

    def test_complex_nephew_friend_hobby_job(self):
        # nephew(2) + friend(1) = 3 hops; hobby + job = 2 constraints; composite = 5
        query = [
            'nephew(Y_3, Y_4)',
            'friend(Y_2, Y_3)',
            'hobby(Y_2, "reading")',
            'job(Y_2, "teacher")',
        ]
        d = compute_difficulty(query)
        assert d["hops"] == 3
        assert d["constraints"] == 2
        assert d["composite"] == 5

    def test_aggregation_query(self):
        query = ['aggregate_all(count, distinct(child("Alice", Y_2)), Count_3)']
        d = compute_difficulty(query)
        assert d["hops"] == 1
        assert d["constraints"] == 0

    def test_comparison_query_with_dob_variable_args(self):
        # dob(Y, Var) with variable second arg is value retrieval, NOT a constraint
        query = [
            'CmpDL_5 @< CmpDR_5',
            'dob(Y_2, CmpDL_5)',
            'dob(Y_4, CmpDR_5)',
            'friend("Alice", Y_2)',
            'parent("Bob", Y_4)',
        ]
        d = compute_difficulty(query)
        assert d["hops"] == 1  # max(friend=1, parent=1)
        assert d["constraints"] == 0  # dob with variable args are not constraints

    def test_empty_query(self):
        d = compute_difficulty([])
        assert d["hops"] == 0
        assert d["constraints"] == 0
        assert d["composite"] == 0

    def test_hops_plus_constraints_equals_composite(self):
        queries = [
            ['friend("A", Y)'],
            ['nephew(Y, Z)', 'hobby(Y, "x")'],
            ['cousin(A, B)', 'job(A, "y")', 'hobby(B, "z")'],
        ]
        for q in queries:
            d = compute_difficulty(q)
            assert d["hops"] + d["constraints"] == d["composite"]


# ---------------------------------------------------------------------------
# Integration with output schema
# ---------------------------------------------------------------------------


class TestOutputSchema:
    """Verify the difficulty dict integrates into question output."""

    @pytest.fixture(autouse=True, scope="class")
    def _generate(self, tmp_path_factory):
        """Generate a small dataset and store questions."""
        from phantom_wiki import generate_dataset

        out = str(tmp_path_factory.mktemp("out"))
        generate_dataset(
            num_family_trees=1,
            max_family_tree_size=15,
            max_family_tree_depth=4,
            num_questions_per_type=2,
            max_hops=2,
            max_constraints=2,
            seed=42,
            output_dir=out,
            quiet=True,
        )
        questions = []
        qdir = os.path.join(out, "questions")
        for fname in os.listdir(qdir):
            if fname.endswith(".json"):
                with open(os.path.join(qdir, fname)) as f:
                    questions.extend(json.load(f))
        type(self)._questions = questions

    def test_difficulty_dict_present(self):
        for q in self._questions:
            assert isinstance(q["difficulty"], dict), f"Expected dict, got {type(q['difficulty'])}"

    def test_difficulty_has_all_fields(self):
        required = {"hops", "constraints", "composite"}
        for q in self._questions:
            assert required.issubset(set(q["difficulty"].keys()))

    def test_composite_equals_hops_plus_constraints(self):
        for q in self._questions:
            d = q["difficulty"]
            assert d["composite"] == d["hops"] + d["constraints"]

    def test_hops_positive_for_relation_questions(self):
        for q in self._questions:
            if q.get("is_aggregation_question"):
                continue
            prolog = q.get("prolog", {}).get("query", [])
            has_relation = any(
                not atom.strip().startswith("\\+")
                and "hobby(" not in atom
                and "job(" not in atom
                and "dob(" not in atom
                for atom in prolog
                if "(" in atom
            )
            if has_relation:
                assert q["difficulty"]["hops"] > 0


# ---------------------------------------------------------------------------
# Ground-truth tests for the corrected difficulty computation
# ---------------------------------------------------------------------------


class TestHopMapAssertions:
    """Verify derived hop counts match expected values from Prolog rules."""

    @pytest.fixture(autouse=True)
    def _hop_counts(self):
        derive_relation_hop_counts.cache_clear()
        self.hops = derive_relation_hop_counts()

    def test_hop_map_base_relations(self):
        assert self.hops["friend"] == 1
        assert self.hops["sibling"] == 1
        assert self.hops["parent"] == 1
        assert self.hops["child"] == 1

    def test_hop_map_compound_relations(self):
        assert self.hops["nephew"] == 2
        assert self.hops["niece"] == 2
        assert self.hops["uncle"] == 2
        assert self.hops["aunt"] == 2
        assert self.hops["grandchild"] == 2
        assert self.hops["granddaughter"] == 2
        assert self.hops["grandmother"] == 2

    def test_hop_map_deep_relations(self):
        assert self.hops["cousin"] == 3
        assert self.hops["great_aunt"] == 3
        assert self.hops["great_uncle"] == 3
        assert self.hops["great_grandchild"] == 3
        assert self.hops["great_grandmother"] == 3
        assert self.hops["great_granddaughter"] == 3
        assert self.hops["mother_in_law"] == 2
        assert self.hops["father_in_law"] == 2
        assert self.hops["sister_in_law"] == 2
        assert self.hops["brother_in_law"] == 2


class TestConstraintCounter:
    """Verify constraint counting distinguishes literals from variables."""

    def test_constraint_counter_skips_value_retrieval(self):
        query = ["dob(Y_2, CmpDL_6)", 'dob(Y_2, "0295-05-30")']
        d = compute_difficulty(query)
        assert d["constraints"] == 1

    def test_constraint_counter_counts_literals(self):
        query = ['hobby(X, "farming")', 'job(X, "farmer")']
        d = compute_difficulty(query)
        assert d["constraints"] == 2

    def test_dob_variable_not_constraint(self):
        query = ["dob(Y_8, CmpDR_6)"]
        d = compute_difficulty(query)
        assert d["constraints"] == 0

    def test_dob_literal_is_constraint(self):
        query = ['dob(Y_4, "0295-05-30")']
        d = compute_difficulty(query)
        assert d["constraints"] == 1


class TestHopCounterDecomposition:
    """Verify hop counter uses derived hop counts for compound relations."""

    def test_hop_counter_decomposes_niece(self):
        query = ['niece("Jeannine", Y)']
        d = compute_difficulty(query)
        assert d["hops"] == 2

    def test_hop_counter_decomposes_great_aunt(self):
        query = ['great_aunt("Shelli", Y)']
        d = compute_difficulty(query)
        assert d["hops"] == 3


class TestGroundTruthQuestions:
    """End-to-end tests for specific question patterns."""

    def test_full_question_1_ground_truth(self):
        query = [
            "CmpDL_6 @< CmpDR_6",
            "dob(Y_2, CmpDL_6)",
            "dob(Y_8, CmpDR_6)",
            "child(Y_4, Y_2)",
            'hobby(Y_4, "dairy farming")',
            'niece("Jeannine Wexler", Y_8)',
        ]
        result = compute_difficulty(query)
        assert result["hops"] == 2, f"Expected 2 hops, got {result['hops']}"
        assert result["constraints"] == 1, f"Expected 1 constraint, got {result['constraints']}"
        assert result["composite"] == 3

    def test_full_question_5_ground_truth(self):
        query = [
            "CmpDL_6 @< CmpDR_6",
            "dob(Y_2, CmpDL_6)",
            "dob(Y_8, CmpDR_6)",
            "friend(Y_4, Y_2)",
            'job(Y_4, "occupational therapist")',
            'great_aunt("Shelli Beltran", Y_8)',
        ]
        result = compute_difficulty(query)
        assert result["hops"] == 3, f"Expected 3 hops, got {result['hops']}"
        assert result["constraints"] == 1, f"Expected 1 constraint, got {result['constraints']}"
        assert result["composite"] == 4

    def test_full_question_6_ground_truth(self):
        query = [
            "CmpDL_6 @< CmpDR_6",
            "dob(Y_2, CmpDL_6)",
            "dob(Y_8, CmpDR_6)",
            "father_in_law(Y_4, Y_2)",
            'dob(Y_4, "0292-03-17")',
            'sister_in_law("Dominique Smock", Y_8)',
        ]
        result = compute_difficulty(query)
        assert result["hops"] == 2, f"Expected 2 hops, got {result['hops']}"
        assert result["constraints"] == 1, f"Expected 1 constraint, got {result['constraints']}"
        assert result["composite"] == 3


class TestCountComparisonBranches:
    """Verify count-comparison queries are split into K branches and max-scored."""

    def test_count_comparison_named_vs_named(self):
        # "Who has more friends, Aida or Aubrey?" — each branch is one
        # aggregate_all(friend) on a named entity. max(1, 1) = 1 hop.
        query = [
            'aggregate_all(count, distinct(friend("Aida Wang", X)), C1)',
            'aggregate_all(count, distinct(friend("Aubrey Smock", Y)), C2)',
            "C1 > C2",
        ]
        d = compute_difficulty(query)
        assert d["hops"] == 1
        assert d["constraints"] == 0
        assert d["composite"] == 1

    def test_count_comparison_chained_branches(self):
        # "Who has more friends, the sister of Alice or the brother of Bob?"
        # Each branch: aggregate_all(friend) + 1 chain hop = 2 hops. max = 2.
        query = [
            'aggregate_all(count, distinct(friend(Y_2, X)), C1)',
            'sister("Alice", Y_2)',
            'aggregate_all(count, distinct(friend(Y_4, Y)), C2)',
            'brother("Bob", Y_4)',
            "C1 > C2",
        ]
        d = compute_difficulty(query)
        assert d["hops"] == 2
        assert d["constraints"] == 0

    def test_count_comparison_asymmetric_branches(self):
        # Right branch is heavier (cousin = 3 hops + agg_all friend = 4) than
        # left (named-only agg_all = 1).  max picks the heavier branch.
        query = [
            'aggregate_all(count, distinct(friend("Alice", X)), C1)',
            'aggregate_all(count, distinct(friend(Y_4, Y)), C2)',
            'cousin("Bob", Y_4)',
            "C1 > C2",
        ]
        d = compute_difficulty(query)
        assert d["hops"] == 4  # max(1, agg=1 + cousin=3)
        assert d["constraints"] == 0

    def test_count_comparison_three_way(self):
        # K=3 branches: forward-looking generalization to N-way comparison.
        query = [
            'aggregate_all(count, distinct(friend("A", X1)), C1)',
            'aggregate_all(count, distinct(friend("B", X2)), C2)',
            'aggregate_all(count, distinct(friend("C", X3)), C3)',
            "C1 > C2",
            "C1 > C3",
        ]
        d = compute_difficulty(query)
        assert d["hops"] == 1  # max across 3 branches, each = 1
        assert d["constraints"] == 0

    def test_count_comparison_with_constraint_branch(self):
        # One branch has an attribute constraint on the chain.
        query = [
            'aggregate_all(count, distinct(friend(Y_2, X)), C1)',
            'sister("Alice", Y_2)',
            'hobby(Y_2, "shogi")',
            'aggregate_all(count, distinct(friend("Bob", Y)), C2)',
            "C1 > C2",
        ]
        d = compute_difficulty(query)
        # Left branch: agg_all(friend)=1 + sister=1 = 2 hops, hobby = 1 cons
        # Right branch: agg_all(friend) = 1 hop, 0 cons
        assert d["hops"] == 2
        assert d["constraints"] == 1

    def test_age_comparison_unaffected_by_count_logic(self):
        # Existing CmpDL/CmpDR age-comparison path must still work after
        # generalizing the splitter.
        query = [
            "CmpDL_5 @< CmpDR_5",
            "dob(Y_2, CmpDL_5)",
            "dob(Y_4, CmpDR_5)",
            'friend("Alice", Y_2)',
            'parent("Bob", Y_4)',
        ]
        d = compute_difficulty(query)
        assert d["hops"] == 1
        assert d["constraints"] == 0

    def test_count_comparison_chained_with_ans_binders(self):
        # Mirrors what `sample_comparison_count_extended_question` emits for
        # chain_depth=1 named-vs-named: the LeftAns/RightAns unifications are
        # plumbing for answer extraction, not difficulty hops/constraints.
        query = [
            'sister("Alice", LP1)',
            'brother("Bob", RP1)',
            'aggregate_all(count, distinct(friend(LP1, _LX)), CL)',
            'aggregate_all(count, distinct(friend(RP1, _RX)), CR)',
            "LeftAns = LP1",
            "RightAns = RP1",
            "CL > CR",
        ]
        d = compute_difficulty(query)
        # Each branch: aggregate_all(friend) = 1 hop + sister/brother = 1 hop = 2
        assert d["hops"] == 2
        assert d["constraints"] == 0

    def test_count_comparison_mc2_with_ans_binders(self):
        # chain_depth=0 with mc2 anchor on the left branch.
        # Left: agg_all(friend) over mc2 person = 1 hop, 2 attribute constraints.
        # Right: agg_all(friend) over named person = 1 hop, 0 constraints.
        # max → (1, 2).
        query = [
            'job(LP0, "actuary")',
            'hobby(LP0, "shogi")',
            'aggregate_all(count, distinct(friend(LP0, _LX)), CL)',
            'aggregate_all(count, distinct(friend("Bob", _RX)), CR)',
            "LeftAns = LP0",
            'RightAns = "Bob"',
            "CL > CR",
        ]
        d = compute_difficulty(query)
        assert d["hops"] == 1
        assert d["constraints"] == 2
