# standard imports
from numpy.random import default_rng
import json
# phantom wiki functionality
from phantom_wiki.facts import get_database
from phantom_wiki.facts.attributes import db_generate_attributes
from phantom_wiki.facts.templates import generate_templates
from phantom_wiki.facts.sample import sample
from phantom_wiki.utils import get_parser
from tests.facts.family import FAMILY_TREE_SMALL_EXAMPLE_PATH
from tests.facts import (DEPTH6_PATH,
                         DEPTH8_PATH,)
# TODO: come up with a better way to test the question-prolog pair generation
SAVE_SAMPLE = False

with open(DEPTH6_PATH, "r") as f:
    DATA_DEPTH_6 = json.load(f)
with open(DEPTH8_PATH, "r") as f:
    DATA_DEPTH_8 = json.load(f)

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

# 
# Tests for sampling placeholders from the database
# 
parser = get_parser()
args, _ = parser.parse_known_args(["--output_dir", "test_out", "--seed", "1"])

db = get_database(FAMILY_TREE_SMALL_EXAMPLE_PATH)
db_generate_attributes(db, args)
# define dob predicate since it is not defined in the small example
db.define("dob/2")

def test_sample_0():
    # case 1: valid_only=False
    question_template_list, predicate_template_list, _ = DATA_DEPTH_6[0]
    rng = default_rng(seed=1)
    any_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=False)
    if SAVE_SAMPLE:
        with open("sample.json", "a") as f:
            json.dump(any_query, f, indent=4)
    # assert any_query == (
    #     {"<attribute_name>_1": "age", "<relation>_3": "child"},
    #     "Who is the child of the person whose age is <attribute_value>_1 ?",
    #     ["child(Y_2, Y_4)", "age(Y_2, <attribute_value>_1)"],
    # )
    
    # case 2: valid_only=True
    valid_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=True)
    if SAVE_SAMPLE:
        with open("sample.json", "a") as f:
            json.dump(valid_query, f, indent=4)
    # assert valid_query == (
    #     {'<relation>_3': 'father', '<attribute_name>_1': 'hobby', '<attribute_value>_1': 'running'},
    #     'Who is the father of the person whose hobby is running ?',
    #     ['father(Y_2, Y_4)', 'hobby(Y_2, running)']
    # )


def test_sample_1():
    # case 1: valid_only=False
    question_template_list, predicate_template_list, _ = DATA_DEPTH_6[1]
    rng = default_rng(seed=1)
    any_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=False)
    if SAVE_SAMPLE:
        with open("sample.json", "a") as f:
            json.dump(any_query, f, indent=4)
    # assert any_query == (
    #     {"<name>_2": "vanessa", "<relation>_3": "child"},
    #     "Who is the child of vanessa ?",
    #     ["child('vanessa', Y_4)"],
    # )
    
    # case 2: valid_only=True
    valid_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=True)
    if SAVE_SAMPLE:
        with open("sample.json", "a") as f:
            json.dump(valid_query, f, indent=4)
    # assert valid_query == (
    #     {"<name>_2": "maximilian", "<relation>_3": "wife"},
    #     "Who is the wife of maximilian ?",
    #     ["wife('maximilian', Y_4)"],
    # )


def test_sample_3():
    # case 1: valid_only=False
    question_template_list, predicate_template_list, _ = DATA_DEPTH_6[3]
    rng = default_rng(seed=1)
    any_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=False)
    if SAVE_SAMPLE:
        with open("sample.json", "a") as f:
            json.dump(any_query, f, indent=4)
    # assert any_query == (
    #     {"<name>_1": "vanessa", "<relation>_2": "child", "<attribute_name>_3": "job"},
    #     "What is the job of the child of vanessa ?",
    #     ["job(Y_3, Y_4)", "child('vanessa', Y_3)"],
    # )

    valid_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=True)
    if SAVE_SAMPLE:
        with open("sample.json", "a") as f:
            json.dump(valid_query, f, indent=4)
    # assert valid_query == {
    #     "<name>_1": "vanessa",
    #     "<relation>_2": "daughter",
    #     "<relation>_1": "daughter"
    # }
    
def test_sample_4():
    question_template_list, predicate_template_list, _ = DATA_DEPTH_6[4]
    rng = default_rng(seed=1)
    any_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=False)
    if SAVE_SAMPLE:
        with open("sample.json", "a") as f:
            json.dump(any_query, f, indent=4)
    # assert any_query == (
    #     {"<attribute_name>_2": "age", "<attribute_name>_3": "job"},
    #     "What is the job of the person whose age is <attribute_value>_2 ?",
    #     ["job(Y_3, Y_4)", "age(Y_3, <attribute_value>_2)"],
    # )

    valid_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=True)
    if SAVE_SAMPLE:
        with open("sample.json", "a") as f:
            json.dump(valid_query, f, indent=4)


def test_sample_5():
    question_template_list, predicate_template_list, _ = DATA_DEPTH_6[5]
    rng = default_rng(seed=1)
    any_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=False)
    if SAVE_SAMPLE:
        with open("sample.json", "a") as f:
            json.dump(any_query, f, indent=4)
    # assert any_query == (
    #     {"<name>_1": "vanessa", "<relation>_2": "child", "<relation_plural>_4": "sons"},
    #     "How many sons does the child of vanessa have?",
    #     ["aggregate_all(count, son(Y_3, Y_5), Count_5)", "child('vanessa', Y_3)"],
    # )
    
    valid_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=True)
    if SAVE_SAMPLE:
        with open("sample.json", "a") as f:
            json.dump(valid_query, f, indent=4)


def test_sample_6():
    question_template_list, predicate_template_list, _ = DATA_DEPTH_6[6]
    rng = default_rng(seed=1)
    any_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=False)
    if SAVE_SAMPLE:
        with open("sample.json", "a") as f:
            json.dump(any_query, f, indent=4)
    # assert any_query == (
    #     {"<attribute_name>_2": "age", "<relation_plural>_4": "children"},
    #     "How many children does the person whose age is <attribute_value>_2 have?",
    #     ["aggregate_all(count, child(Y_3, Y_5), Count_5)", "age(Y_3, <attribute_value>_2)"],
    # )
    
    valid_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=True)
    if SAVE_SAMPLE:
        with open("sample.json", "a") as f:
            json.dump(valid_query, f, indent=4)


def test_sample_7():
    question_template_list, predicate_template_list, _ = DATA_DEPTH_6[7]
    rng = default_rng(seed=1)
    any_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=False)
    if SAVE_SAMPLE:
        with open("sample.json", "a") as f:
            json.dump(any_query, f, indent=4)
    # assert any_query == (
    #     {"<name>_3": "vanessa", "<relation_plural>_4": "children"},
    #     "How many children does vanessa have?",
    #     ["aggregate_all(count, child('vanessa', Y_5), Count_5)"],
    # )

    valid_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=True)
    if SAVE_SAMPLE:
        with open("sample.json", "a") as f:
            json.dump(valid_query, f, indent=4)
