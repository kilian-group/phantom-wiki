from numpy.random import default_rng
import json
from phantom_wiki.facts import get_database
from phantom_wiki.facts.attributes import db_generate_attributes
from phantom_wiki.facts.templates import generate_templates
from phantom_wiki.utils.nltk_generate import sample
from tests.facts.family import FAMILY_TREE_SMALL_EXAMPLE_PATH

QUESTION_TEMPLATES_DEPTH_6 = [
    "Who is the <relation>_3 of the person whose <attribute_name>_1 is <attribute_value>_1 ?",
    "Who is the <relation>_3 of <name>_2 ?",
    "Who is the person whose <attribute_name>_3 is <attribute_value>_3 ?",
    "What is the <attribute_name>_3 of the <relation>_2 of <name>_1 ?",
    "What is the <attribute_name>_3 of the person whose <attribute_name>_2 is <attribute_value>_2 ?",
    "How many <relation_plural>_4 does the <relation>_2 of <name>_1 have?",
    "How many <relation_plural>_4 does the person whose <attribute_name>_2 is <attribute_value>_2 have?",
    "How many <relation_plural>_4 does <name>_3 have?",
]

PROLOG_TEMPLATES_DEPTH_6 = [
    "<relation>_3(Y_2, Y_4), <attribute_name>_1(Y_2, <attribute_value>_1)",
    "<relation>_3(<name>_2, Y_4)",
    "<attribute_name>_3(Y_4, <attribute_value>_3)",
    "<attribute_name>_3(Y_3, Y_4), <relation>_2(<name>_1, Y_3)",
    "<attribute_name>_3(Y_3, Y_4), <attribute_name>_2(Y_3, <attribute_value>_2)",
    "aggregate_all(count, <relation_plural>_4(Y_3, Y_5), Count_5), <relation>_2(<name>_1, Y_3)",
    "aggregate_all(count, <relation_plural>_4(Y_3, Y_5), Count_5), <attribute_name>_2(Y_3, <attribute_value>_2)",
    "aggregate_all(count, <relation_plural>_4(<name>_3, Y_5), Count_5)",
]

PROLOG_ANSWERS_DEPTH_6 = ["Y_4", "Y_4", "Y_4", "Y_4", "Y_4", "Count_5", "Count_5", "Count_5"]

# 
# Begin unjoined templates
# 
QUESTION_TEMPLATES_DEPTH_6_UNJOINED = [
    [
        "Who is",
        "the",
        "<relation>_3",
        "of",
        "the person whose",
        "<attribute_name>_1",
        "is",
        "<attribute_value>_1",
        "?",
    ],
    ["Who is", "the", "<relation>_3", "of", "<name>_2", "?"],
    ["Who is", "the person whose", "<attribute_name>_3", "is", "<attribute_value>_3", "?"],
    ["What is", "the", "<attribute_name>_3", "of", "the", "<relation>_2", "of", "<name>_1", "?"],
    [
        "What is",
        "the",
        "<attribute_name>_3",
        "of",
        "the person whose",
        "<attribute_name>_2",
        "is",
        "<attribute_value>_2",
        "?",
    ],
    ["How many", "<relation_plural>_4", "does", "the", "<relation>_2", "of", "<name>_1", "have?"],
    [
        "How many",
        "<relation_plural>_4",
        "does",
        "the person whose",
        "<attribute_name>_2",
        "is",
        "<attribute_value>_2",
        "have?",
    ],
    ["How many", "<relation_plural>_4", "does", "<name>_3", "have?"],
]

PROLOG_TEMPLATES_DEPTH_6_UNJOINED = [
    ["<relation>_3(Y_2, Y_4)", "<attribute_name>_1(Y_2, <attribute_value>_1)"],
    ["<relation>_3(<name>_2, Y_4)"],
    ["<attribute_name>_3(Y_4, <attribute_value>_3)"],
    ["<attribute_name>_3(Y_3, Y_4)", "<relation>_2(<name>_1, Y_3)"],
    ["<attribute_name>_3(Y_3, Y_4)", "<attribute_name>_2(Y_3, <attribute_value>_2)"],
    ["aggregate_all(count, <relation_plural>_4(Y_3, Y_5), Count_5)", "<relation>_2(<name>_1, Y_3)"],
    ["aggregate_all(count, <relation_plural>_4(Y_3, Y_5), Count_5)", "<attribute_name>_2(Y_3, <attribute_value>_2)"],
    ["aggregate_all(count, <relation_plural>_4(<name>_3, Y_5), Count_5)"],
]
# 
# End unjoined templates
# 

def test_generate_templates_depth_6():
    templates = generate_templates(depth=6)
    for template, question, query, answer in zip(
        templates, QUESTION_TEMPLATES_DEPTH_6, PROLOG_TEMPLATES_DEPTH_6, PROLOG_ANSWERS_DEPTH_6
    ):
        assert " ".join(template[0]) == question
        assert ", ".join(template[1]) == query
        assert template[2] == answer

# 
# Tests for generating fully formed question-prolog pairs
# 
db = get_database(FAMILY_TREE_SMALL_EXAMPLE_PATH)
db_generate_attributes(db, seed=1)
# define random ages
age_rng = default_rng(seed=1)
age_facts = ["age(\'{}\', {})".format(name, age_rng.integers(10, 50)) for name in db.get_names()]
db.add(*age_facts)

def test_sample_0():
    # case 1: valid_only=False
    question_template_list = QUESTION_TEMPLATES_DEPTH_6_UNJOINED[0]
    predicate_template_list = PROLOG_TEMPLATES_DEPTH_6_UNJOINED[0]
    rng = default_rng(seed=1)
    any_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=False)
    with open("sample.json", "a") as f:
        json.dump(any_query, f, indent=4)
    # assert any_query == (
    #     {"<attribute_name>_1": "age", "<relation>_3": "child"},
    #     "Who is the child of the person whose age is <attribute_value>_1 ?",
    #     ["child(Y_2, Y_4)", "age(Y_2, <attribute_value>_1)"],
    # )
    
    # case 2: valid_only=True
    valid_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=True)
    with open("sample.json", "a") as f:
        json.dump(valid_query, f, indent=4)
    # assert valid_query == (
    #     {'<relation>_3': 'father', '<attribute_name>_1': 'hobby', '<attribute_value>_1': 'running'},
    #     'Who is the father of the person whose hobby is running ?',
    #     ['father(Y_2, Y_4)', 'hobby(Y_2, running)']
    # )


def test_sample_1():
    # case 1: valid_only=False
    question_template_list = QUESTION_TEMPLATES_DEPTH_6_UNJOINED[1]
    predicate_template_list = PROLOG_TEMPLATES_DEPTH_6_UNJOINED[1]
    rng = default_rng(seed=1)
    any_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=False)
    with open("sample.json", "a") as f:
        json.dump(any_query, f, indent=4)
    # assert any_query == (
    #     {"<name>_2": "vanessa", "<relation>_3": "child"},
    #     "Who is the child of vanessa ?",
    #     ["child('vanessa', Y_4)"],
    # )
    
    # case 2: valid_only=True
    valid_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=True)
    with open("sample.json", "a") as f:
        json.dump(valid_query, f, indent=4)
    # assert valid_query == (
    #     {"<name>_2": "maximilian", "<relation>_3": "wife"},
    #     "Who is the wife of maximilian ?",
    #     ["wife('maximilian', Y_4)"],
    # )


def test_sample_3():
    # case 1: valid_only=False
    predicate_template_list = PROLOG_TEMPLATES_DEPTH_6_UNJOINED[3]
    question_template_list = QUESTION_TEMPLATES_DEPTH_6_UNJOINED[3]
    rng = default_rng(seed=1)
    any_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=False)
    with open("sample.json", "a") as f:
        json.dump(any_query, f, indent=4)
    # assert any_query == (
    #     {"<name>_1": "vanessa", "<relation>_2": "child", "<attribute_name>_3": "job"},
    #     "What is the job of the child of vanessa ?",
    #     ["job(Y_3, Y_4)", "child('vanessa', Y_3)"],
    # )

    valid_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=True)
    with open("sample.json", "a") as f:
        json.dump(valid_query, f, indent=4)
    # assert valid_query == {
    #     "<name>_1": "vanessa",
    #     "<relation>_2": "daughter",
    #     "<relation>_1": "daughter"
    # }
    
def test_sample_4():
    question_template_list = QUESTION_TEMPLATES_DEPTH_6_UNJOINED[4]
    predicate_template_list = PROLOG_TEMPLATES_DEPTH_6_UNJOINED[4]
    rng = default_rng(seed=1)
    any_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=False)
    with open("sample.json", "a") as f:
        json.dump(any_query, f, indent=4)
    # assert any_query == (
    #     {"<attribute_name>_2": "age", "<attribute_name>_3": "job"},
    #     "What is the job of the person whose age is <attribute_value>_2 ?",
    #     ["job(Y_3, Y_4)", "age(Y_3, <attribute_value>_2)"],
    # )

    valid_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=True)
    with open("sample.json", "a") as f:
        json.dump(valid_query, f, indent=4)


def test_sample_5():
    question_template_list = QUESTION_TEMPLATES_DEPTH_6_UNJOINED[5]
    predicate_template_list = PROLOG_TEMPLATES_DEPTH_6_UNJOINED[5]
    rng = default_rng(seed=1)
    any_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=False)
    with open("sample.json", "a") as f:
        json.dump(any_query, f, indent=4)
    # assert any_query == (
    #     {"<name>_1": "vanessa", "<relation>_2": "child", "<relation_plural>_4": "sons"},
    #     "How many sons does the child of vanessa have?",
    #     ["aggregate_all(count, son(Y_3, Y_5), Count_5)", "child('vanessa', Y_3)"],
    # )
    
    valid_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=True)
    with open("sample.json", "a") as f:
        json.dump(valid_query, f, indent=4)


def test_sample_6():
    question_template_list = QUESTION_TEMPLATES_DEPTH_6_UNJOINED[6]
    predicate_template_list = PROLOG_TEMPLATES_DEPTH_6_UNJOINED[6]
    rng = default_rng(seed=1)
    any_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=False)
    with open("sample.json", "a") as f:
        json.dump(any_query, f, indent=4)
    # assert any_query == (
    #     {"<attribute_name>_2": "age", "<relation_plural>_4": "children"},
    #     "How many children does the person whose age is <attribute_value>_2 have?",
    #     ["aggregate_all(count, child(Y_3, Y_5), Count_5)", "age(Y_3, <attribute_value>_2)"],
    # )
    
    valid_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=True)
    with open("sample.json", "a") as f:
        json.dump(valid_query, f, indent=4)


def test_sample_7():
    question_template_list = QUESTION_TEMPLATES_DEPTH_6_UNJOINED[7]
    predicate_template_list = PROLOG_TEMPLATES_DEPTH_6_UNJOINED[7]
    rng = default_rng(seed=1)
    any_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=False)
    with open("sample.json", "a") as f:
        json.dump(any_query, f, indent=4)
    # assert any_query == (
    #     {"<name>_3": "vanessa", "<relation_plural>_4": "children"},
    #     "How many children does vanessa have?",
    #     ["aggregate_all(count, child('vanessa', Y_5), Count_5)"],
    # )

    valid_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=True)
    with open("sample.json", "a") as f:
        json.dump(valid_query, f, indent=4)
