import glob
import json
import os
import shutil

from phantom_wiki.facts.templates import is_aggregation_question
from phantom_wiki.generate_dataset import generate_dataset
from tests.phantom_wiki import ARTICLE_EXAMPLE_PATH


def test_generate_dataset():
    generate_dataset(output_dir="test_out", seed=1, easy_mode=True)

    # get example article
    with open(ARTICLE_EXAMPLE_PATH) as fname:
        example_article = fname.read()
    # test that the articles were generated correctly
    article_dir = os.path.join("test_out", "articles")

    with open(os.path.join(article_dir, "Aida Wang.txt")) as file:
        article = file.read()
        print("HELLO", article == example_article)
        assert article == example_article

    # test that the questions were generated correctly
    question_dir = os.path.join("test_out", "questions")
    with open(os.path.join(question_dir, "type0.json")) as file:
        data = json.load(file)
        assert len(data) == 10
        assert data[0]["template"] == [
            "Who is",
            "the",
            "<relation>_3",
            "of",
            "the person whose",
            "<attribute_name>_5",
            "is",
            "<attribute_value>_5",
            "?",
        ]

        assert (
            data[0]["question"]
            == "Who is the daughter of the person whose occupation is early years teacher?"
        )
        assert data[0]["prolog"]["query"] == ["daughter(Y_4, Y_2)", 'job(Y_4, "early years teacher")']
        assert data[0]["answer"] == ["Valentina Wexler"]
        for entry in data:
            assert not entry[
                "is_aggregation_question"
            ], f"'Who is' questions like {entry['question']} should not marked as aggregation questions"

    # Glob over all type*.json files, and check:
    # - the number of questions is 10
    # - the is_aggregation_question field matches is_aggregation_question(question) function
    for fname in glob.glob(os.path.join(question_dir, "type*.json")):
        with open(fname) as file:
            data = json.load(file)
            assert len(data) == 10
            for entry in data:
                assert entry["is_aggregation_question"] == is_aggregation_question(entry["question"])

    # clean up test_out directory
    shutil.rmtree("test_out")
