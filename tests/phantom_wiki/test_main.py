# standard imports
import json
import os
import shutil

from phantom_wiki.__main__ import main
from phantom_wiki.facts import question_parser

# phantom wiki functionality
from phantom_wiki.facts.family import fam_gen_parser
from phantom_wiki.facts.friends import friend_gen_parser
from phantom_wiki.utils import get_parser
from tests.phantom_wiki import ARTICLE_EXAMPLE_PATH


def test_main():
    parser = get_parser(
        parents=[
            fam_gen_parser,
            question_parser,
            friend_gen_parser,
        ]
    )
    args, _ = parser.parse_known_args(["--output-dir", "test_out", "--seed", "1", "--valid-only", "--debug"])
    main(args)

    # get example article
    with open(ARTICLE_EXAMPLE_PATH) as f:
        example_article = f.read()
    # test that the articles were generated correctly
    article_dir = os.path.join("test_out", "articles")
    with open(os.path.join(article_dir, "Aida Wang.txt")) as file:
        article = file.read()
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

        assert data[0]["question"] == "Who is the father of the person whose job is biomedical scientist?"
        assert data[0]["prolog"]["query"] == ["father(Y_4, Y_2)", 'job(Y_4, "biomedical scientist")']
        assert data[0]["answer"] == ["Ryan Wang"]

    # clean up test_out directory
    shutil.rmtree("test_out")
