# standard imports
import json
from numpy.random import default_rng

# phantom wiki functionality
from phantom_wiki.facts import Database
from phantom_wiki.facts.sample import sample
from phantom_wiki.facts.templates import generate_templates
from phantom_wiki.utils import get_parser
# testing utils
from tests.facts import (DEPTH_6_PATH, 
                         DEPTH_8_PATH, 
                         DEPTH_10_PATH,
                         QUESTIONS_DICT,
                         QUESTIONS_VALID_DICT)
from tests.facts.family import FACTS_SMALL_EXAMPLE_PATH

# TODO: come up with a better way to test the question-prolog pair generation
SAVE_SAMPLE = False

with open(DEPTH_6_PATH) as f:
    DATA_DEPTH_6 = json.load(f)
with open(DEPTH_8_PATH) as f:
    DATA_DEPTH_8 = json.load(f)
with open(DEPTH_10_PATH) as f:
    DATA_DEPTH_10 = json.load(f)


def test_generate_templates_depth_6():
    templates = generate_templates(depth=6)
    for template, (question, query, answer) in zip(templates, DATA_DEPTH_6):
        assert template[0] == question
        assert template[1] == query
        assert template[2] == answer


def test_generate_templates_depth_8():
    templates = generate_templates(depth=8)
    for template, (question, query, answer) in zip(templates, DATA_DEPTH_8):
        assert template[0] == question
        assert template[1] == query
        assert template[2] == answer

def test_generate_templates_depth_10():
    templates = generate_templates(depth=10)
    for template, (question, query, answer) in zip(templates, DATA_DEPTH_10):
        assert template[0] == question
        assert template[1] == query
        assert template[2] == answer

def test_template_depth_subsets():
    """Templates at depth 6 are a subset of templates at depth 8."""
    templates_depth_6 = generate_templates(depth=6)
    templates_depth_8 = generate_templates(depth=8)
    templates_depth_10 = generate_templates(depth=10)

    # Hashable representation
    def condense_templates(q):
        return (" ".join(q[0]), ", ".join(q[1]), q[2])

    condensed_templates_depth_6 = set(map(condense_templates, templates_depth_6))
    condensed_templates_depth_8 = set(map(condense_templates, templates_depth_8))
    condensed_templates_depth_10 = set(map(condense_templates, templates_depth_10))

    assert condensed_templates_depth_6 <= condensed_templates_depth_8
    assert condensed_templates_depth_8 <= condensed_templates_depth_10


#
# Tests for sampling placeholders from the database
#
parser = get_parser()
args, _ = parser.parse_known_args(["--output_dir", "test_out", "--seed", "1"])
db = Database.from_disk(FACTS_SMALL_EXAMPLE_PATH)

def test_samples():
    for i, (question_template_list, predicate_template_list, _) in enumerate(DATA_DEPTH_6):
        rng = default_rng(seed=1)
        any_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=False)
        # with open(f"sample_{i}.json", "a") as f:
        #     json.dump(any_query, f, indent=4)
        assert any_query == QUESTIONS_DICT[i]

        valid_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=True)
        # with open(f"sample_{i}_valid.json", "a") as f:
        #     json.dump(valid_query, f, indent=4)
        assert valid_query == QUESTIONS_VALID_DICT[i]

# def test_sample_1():
#     # case 1: valid_only=False
#     question_template_list, predicate_template_list, _ = DATA_DEPTH_6[1]
#     rng = default_rng(seed=1)
#     any_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=False)
#     if SAVE_SAMPLE:
#         with open("sample_1.json", "a") as f:
#             json.dump(any_query, f, indent=4)
#     assert any_query == QUESTIONS_DICT[1]

#     # case 2: valid_only=True
#     valid_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=True)
#     if SAVE_SAMPLE:
#         with open("sample_1_valid.json", "a") as f:
#             json.dump(valid_query, f, indent=4)

# def test_sample_2():
#     # case 1: valid_only=False
#     question_template_list, predicate_template_list, _ = DATA_DEPTH_6[2]
#     rng = default_rng(seed=1)
#     any_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=False)
#     if SAVE_SAMPLE:
#         with open("sample_2.json", "a") as f:
#             json.dump(any_query, f, indent=4)
#     assert any_query == QUESTIONS_DICT[2]

#     # case 2: valid_only=True
#     valid_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=True)
#     if SAVE_SAMPLE:
#         with open("sample_2_valid.json", "a") as f:
#             json.dump(valid_query, f, indent=4)

# def test_sample_3():
#     # case 1: valid_only=False
#     question_template_list, predicate_template_list, _ = DATA_DEPTH_6[3]
#     rng = default_rng(seed=1)
#     any_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=False)
#     if SAVE_SAMPLE:
#         with open("sample_3.json", "a") as f:
#             json.dump(any_query, f, indent=4)
#     # assert any_query == (
#     #     {"<name>_1": "vanessa", "<relation>_2": "child", "<attribute_name>_3": "job"},
#     #     "What is the job of the child of vanessa ?",
#     #     ["job(Y_3, Y_4)", "child('vanessa', Y_3)"],
#     # )

#     valid_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=True)
#     if SAVE_SAMPLE:
#         with open("sample_3_valid.json", "a") as f:
#             json.dump(valid_query, f, indent=4)
#     # assert valid_query == {
#     #     "<name>_1": "vanessa",
#     #     "<relation>_2": "daughter",
#     #     "<relation>_1": "daughter"
#     # }


# def test_sample_4():
#     question_template_list, predicate_template_list, _ = DATA_DEPTH_6[4]
#     rng = default_rng(seed=1)
#     any_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=False)
#     if SAVE_SAMPLE:
#         with open("sample_4.json", "a") as f:
#             json.dump(any_query, f, indent=4)
#     # assert any_query == (
#     #     {"<attribute_name>_2": "age", "<attribute_name>_3": "job"},
#     #     "What is the job of the person whose age is <attribute_value>_2 ?",
#     #     ["job(Y_3, Y_4)", "age(Y_3, <attribute_value>_2)"],
#     # )

#     valid_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=True)
#     if SAVE_SAMPLE:
#         with open("sample_4_valid.json", "a") as f:
#             json.dump(valid_query, f, indent=4)


# def test_sample_5():
#     question_template_list, predicate_template_list, _ = DATA_DEPTH_6[5]
#     rng = default_rng(seed=1)
#     any_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=False)
#     if SAVE_SAMPLE:
#         with open("sample_5.json", "a") as f:
#             json.dump(any_query, f, indent=4)
#     # assert any_query == (
#     #     {"<name>_1": "vanessa", "<relation>_2": "child", "<relation_plural>_4": "sons"},
#     #     "How many sons does the child of vanessa have?",
#     #     ["aggregate_all(count, son(Y_3, Y_5), Count_5)", "child('vanessa', Y_3)"],
#     # )

#     valid_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=True)
#     if SAVE_SAMPLE:
#         with open("sample_5_valid.json", "a") as f:
#             json.dump(valid_query, f, indent=4)


# def test_sample_6():
#     question_template_list, predicate_template_list, _ = DATA_DEPTH_6[6]
#     rng = default_rng(seed=1)
#     any_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=False)
#     if SAVE_SAMPLE:
#         with open("sample_6.json", "a") as f:
#             json.dump(any_query, f, indent=4)
#     # assert any_query == (
#     #     {"<attribute_name>_2": "age", "<relation_plural>_4": "children"},
#     #     "How many children does the person whose age is <attribute_value>_2 have?",
#     #     ["aggregate_all(count, child(Y_3, Y_5), Count_5)", "age(Y_3, <attribute_value>_2)"],
#     # )

#     valid_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=True)
#     if SAVE_SAMPLE:
#         with open("sample_6_valid.json", "a") as f:
#             json.dump(valid_query, f, indent=4)


# def test_sample_7():
#     question_template_list, predicate_template_list, _ = DATA_DEPTH_6[7]
#     rng = default_rng(seed=1)
#     any_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=False)
#     if SAVE_SAMPLE:
#         with open("sample_7.json", "a") as f:
#             json.dump(any_query, f, indent=4)
#     # assert any_query == (
#     #     {"<name>_3": "vanessa", "<relation_plural>_4": "children"},
#     #     "How many children does vanessa have?",
#     #     ["aggregate_all(count, child('vanessa', Y_5), Count_5)"],
#     # )

#     valid_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=True)
#     if SAVE_SAMPLE:
#         with open("sample_7_valid.json", "a") as f:
#             json.dump(valid_query, f, indent=4)


def test_sample_depth_subsets():
    """Questions at depth 6 are a subset of questions at depth 8."""
    data_depth_6_str = [str(q) for q in DATA_DEPTH_6]
    data_depth_8_str = [str(q) for q in DATA_DEPTH_8]
    for q in data_depth_6_str:
        assert q in data_depth_8_str
