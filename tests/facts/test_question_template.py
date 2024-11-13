from phantom_wiki.facts.question_template import get_prolog_templates, get_question_templates

QUESTION_TEMPLATES_DEPTH_5 = [
    ["Who is", "the", "<relation>", "of", "the", "<relation>", "of", "<name>", "?"],
    [
        "Who is",
        "the",
        "<relation>",
        "of",
        "the person whose",
        "<attribute_name>",
        "is",
        "<attribute_value>",
        "?",
    ],
    ["Who is", "the", "<relation>", "of", "<name>", "?"],
    ["Who is", "the person whose", "<attribute_name>", "is", "<attribute_value>", "?"],
    ["What is", "the", "<attribute_name>", "of", "the", "<relation>", "of", "<name>", "?"],
    [
        "What is",
        "the",
        "<attribute_name>",
        "of",
        "the person whose",
        "<attribute_name>",
        "is",
        "<attribute_value>",
        "?",
    ],
    ["How many", "<relation_plural>", "does", "the", "<relation>", "of", "<name>", "have?"],
    [
        "How many",
        "<relation_plural>",
        "does",
        "the person whose",
        "<attribute_name>",
        "is",
        "<attribute_value>",
        "have?",
    ],
    ["How many", "<relation_plural>", "does", "<name>", "have?"],
]


def test_get_question_templates_depth_5():
    assert get_question_templates(depth=5) == QUESTION_TEMPLATES_DEPTH_5


def test_get_prolog_templates():
    """
    Question templates (depth=5)
    0. 'Who is', 'the', relation1, 'of', 'the', 'relation2, 'of', 'name1, '?'
            Who is the father of the mother of anastasia?
            father(mother(anastasia), X)
            father(Y, X), mother(anastasia, Y)
        relation1(X,Y), relation2(name1,Y)
        Answer: X
    1. 'Who is', 'the', relation1 'of', 'the person whose', attributename1, 'is', attributevalue1, '?'
            Who is the father of the person whose hobby is running?
            father(hobby(running), X);
            father(Y, X), hobby(Y, running).
        relation1(Y, X), attributename1(Y, attributevalue1)
        Answer: X
    2. 'Who is', 'the', relation1, 'of', 'name1, '?'
            Who is the father of anastasia?
            father(anastasia, X)
        relation1(name1, X)
        Answer: X
    3. 'Who is', 'the', person whose, attributename1, 'is', attributevalue1, '?'
            Who is the person whose hobby is running?
            hobby(X, running)
        attributename1(X, attributevalue1).
        Answer: X
    4. 'What is', 'the', attributename1, 'of', 'the', relation1, 'of' name1 '?'
            What is the job of the father of anastasia?
            job(father(anastasia), X);
            job(Y, X), father(anastasia, Y).
        attributename1(Y, X), relation1(name1, Y).
        Answer: X
    5. 'What is', 'the', attributename1, 'of', 'the person whose', attributename2, 'is', attributevalue2, '?'
            What is the job of the person whose hobby is running?
            job(hobby(running), X);
            job(Y, X), hobby(Y, running).
        attributename1(Y, X), attributename2(Y, attributevalue2).
        Answer: X
    6. 'How many', relation1s, 'does', name1, 'have?'
            How many children does anastasia have?
            aggregate_all(count, children(anastasia, X), X);
        aggregate_all(count, relation1(name1, Y), X).
        Answer: X
    """
    # TODO add the new templates
    PROLOG_TEMPLATES_DEPTH_5 = [
        "<relation>_1(Y, X), <relation>_2(<name>_1, Y).",
        "<relation>_1(Y, X), <attribute_name>_1(X, <attribute_value>_1).",
        "<relation>_1(<name>_1, X).",
        "<attribute_name>_1(X, <attribute_value>_1).",
        "<attribute_name>_1(Y, X), <relation>_1(<name>_1, Y).",
        "<attribute_name>_1(Y, X), <attribute_name>_2(Y, <attribute_value>_2).",
        "aggregate_all(count, <relation>_1(<name>_1, Y), X).",
    ]

    assert get_prolog_templates(QUESTION_TEMPLATES_DEPTH_5) == PROLOG_TEMPLATES_DEPTH_5
