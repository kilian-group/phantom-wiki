from phantom_wiki.facts.question_template import get_prolog_templates, get_question_templates
from phantom_wiki.facts import get_database
from phantom_wiki.utils.nltk_generate import sample
from tests.facts.family import FAMILY_TREE_SMALL_EXAMPLE_PATH
from numpy.random import default_rng

QUESTION_TEMPLATES_DEPTH_5 = [
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

PROLOG_TEMPLATES_DEPTH_5 = [
    ["<relation>_3(Y_2, Y_4)", "<attribute_name>_1(Y_2, <attribute_value>_1)."],
    ["<relation>_3(<name>_2, Y_4)"],
    ["<attribute_name>_3(Y_4, <attribute_value>_3)."],
    ["<attribute_name>_3(Y_3, Y_4)", "<relation>_2(<name>_1, Y_3)."],
    ["<attribute_name>_3(Y_3, Y_4)", "<attribute_name>_2(Y_3, <attribute_value>_2)."],
    ["aggregate_all(count, <relation>_4(Y_3, Y_5), Count_5", "<relation>_2(<name>_1, Y_3)."],
    ["aggregate_all(count, <relation>_4(Y_3, Y_5), Count_5", "<attribute_name>_2(Y_3, <attribute_value>_2)."],
    ["aggregate_all(count, <relation>_4(<name>_3, Y_5), Count_5"],   
]


def test_get_question_templates_depth_5():
    assert get_question_templates(depth=5) == QUESTION_TEMPLATES_DEPTH_5


# def test_get_prolog_templates():
#     """
#     Question templates (depth=5)
#     0. 'Who is', 'the', relation1, 'of', 'the', 'relation2, 'of', 'name1, '?'
#             Who is the father of the mother of anastasia?
#             father(mother(anastasia), X)
#             father(Y, X), mother(anastasia, Y)
#         relation1(X,Y), relation2(name1,Y)
#         Answer: X
#     1. 'Who is', 'the', relation1 'of', 'the person whose', attributename1, 'is', attributevalue1, '?'
#             Who is the father of the person whose hobby is running?
#             father(hobby(running), X);
#             father(Y, X), hobby(Y, running).
#         relation1(Y, X), attributename1(Y, attributevalue1)
#         Answer: X
#     2. 'Who is', 'the', relation1, 'of', 'name1, '?'
#             Who is the father of anastasia?
#             father(anastasia, X)
#         relation1(name1, X)
#         Answer: X
#     3. 'Who is', 'the', person whose, attributename1, 'is', attributevalue1, '?'
#             Who is the person whose hobby is running?
#             hobby(X, running)
#         attributename1(X, attributevalue1).
#         Answer: X
#     4. 'What is', 'the', attributename1, 'of', 'the', relation1, 'of' name1 '?'
#             What is the job of the father of anastasia?
#             job(father(anastasia), X);
#             job(Y, X), father(anastasia, Y).
#         attributename1(Y, X), relation1(name1, Y).
#         Answer: X
#     5. 'What is', 'the', attributename1, 'of', 'the person whose', attributename2, 'is', attributevalue2, '?'
#             What is the job of the person whose hobby is running?
#             job(hobby(running), X);
#             job(Y, X), hobby(Y, running).
#         attributename1(Y, X), attributename2(Y, attributevalue2).
#         Answer: X
#     6. 'How many', relation1s, 'does', name1, 'have?'
#             How many children does anastasia have?
#             aggregate_all(count, children(anastasia, X), X);
#         aggregate_all(count, relation1(name1, Y), X).
#         Answer: X
#     """
#     # TODO add the new templates
#     PROLOG_TEMPLATES_DEPTH_5 = [
#         "<relation>_1(Y, X), <relation>_2(<name>_1, Y).",
#         "<relation>_1(Y, X), <attribute_name>_1(Y, <attribute_value>_1).",
#         "<relation>_1(<name>_1, X).",
#         "<attribute_name>_1(X, <attribute_value>_1).",
#         "<attribute_name>_1(Y, X), <relation>_1(<name>_1, Y).",
#         "<attribute_name>_1(Y, X), <attribute_name>_2(Y, <attribute_value>_2).",
#         "aggregate_all(count, <relation>_1(<name>_1, Y), X).",
#     ]

#     assert get_prolog_templates(QUESTION_TEMPLATES_DEPTH_5) == PROLOG_TEMPLATES_DEPTH_5

def test_sample_1():
    db = get_database(FAMILY_TREE_SMALL_EXAMPLE_PATH)
    # case 1: valid_only=False
    question_template_list = QUESTION_TEMPLATES_DEPTH_5[0]
    predicate_template_list = PROLOG_TEMPLATES_DEPTH_5[0]
    rng = default_rng(seed=1)
    any_query = sample(db, question_template_list, predicate_template_list, rng=rng, valid_only=False)
    # assert any_query == {
    #     "<name>_1": "vanessa",
    #     "<relation>_1": "child"
    # }
    # case 2: valid_only=True
    predicate_template_list = ["<relation>_1(<name>_1, X)"]
    rng = default_rng(seed=1)
    valid_query = sample(db, predicate_template_list, rng=rng, valid_only=True)
    assert valid_query == {
        "<name>_1": "vanessa",
        "<relation>_1": "daughter"
    }

def test_sample_2():
    db = get_database(FAMILY_TREE_SMALL_EXAMPLE_PATH)
    # case 1: valid_only=False
    predicate_template_list = ["<relation>_1(Y, X)", "<relation>_2(<name>_1, Y)"]
    rng = default_rng(seed=1)
    any_query = sample(db, predicate_template_list, rng=rng, valid_only=False)
    assert any_query == {
        "<name>_1": "vanessa",
        "<relation>_2": "child",
        "<relation>_1": "daughter"
    }
    # case 2: valid_only=True
    predicate_template_list = ["<relation>_1(Y, X)", "<relation>_2(<name>_1, Y)"]
    rng = default_rng(seed=1)
    valid_query = sample(db, predicate_template_list, rng=rng, valid_only=True)
    assert valid_query == {
        "<name>_1": "vanessa",
        "<relation>_2": "daughter",
        "<relation>_1": "daughter"
    }

def test_sample_3():
    db = get_database(FAMILY_TREE_SMALL_EXAMPLE_PATH)
    db.define("attribute/1")
    # NOTE: currently we don't have any attribute facts FAMILY_TREE_SMALL_EXAMPLE_PATH,
    # so no queries can be generated
    # case 1: valid_only=False
    predicate_template_list = ["<relation>_1(Y, X)", "<attribute_name>_1(X, <attribute_value>_1)"]
    rng = default_rng(seed=1)
    any_query = sample(db, predicate_template_list, rng=rng, valid_only=False)
    # assert any_query == {
    #     "<name>_1": "vanessa",
    #     "<relation>_2": "child",
    #     "<relation>_1": "daughter"
    # }
    # case 2: valid_only=True
    predicate_template_list = ["<relation>_1(Y, X)", "<attribute_name>_1(X, <attribute_value>_1)"]
    rng = default_rng(seed=1)
    valid_query = sample(db, predicate_template_list, rng=rng, valid_only=True)
    # assert valid_query == "valid": {
    #     "<name>_1": "vanessa",
    #     "<relation>_2": "daughter",
    #     "<relation>_1": "daughter"
    # }
    # import json
    # with open("tests/facts/sample_query.json", "w") as f:
    #     json.dump({"any": any_query, "valid": valid_query}, f, indent=4)

def test_sample_4():
    db = get_database(FAMILY_TREE_SMALL_EXAMPLE_PATH)
    # for the plural case
    predicate_template_list = ["aggregate_all(count, <relation>_1(<name>_3, Y_5), Count_5"]
    rng = default_rng(seed=1)
    valid_query = sample(db, predicate_template_list, rng=rng, valid_only=False)
 
    assert valid_query == {
        "<name>_1": "vanessa",
        "<relation>_2": "daughter",
        "<relation>_1": "daughter"
    }