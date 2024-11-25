# standard imports
import json
import os
import shutil

# phantom wiki functionality
from phantom_wiki.facts.family import fam_gen_parser
from phantom_wiki.utils import get_parser
from phantom_wiki.__main__ import main

def test_main():
    parser = get_parser(parents=[fam_gen_parser])
    args, _ = parser.parse_known_args(["--output_dir", "test_out", "--seed", "1"])
    main(args)

    # test that the articles were generated correctly
    article_dir = os.path.join("test_out", "articles")
    with open(os.path.join(article_dir, "alfonso.txt")) as file:
        article = file.read()
        assert (
            article
            == "# alfonso\n\n## Family\nalfonso's siblings are antionette, colby, dominick, kari.\nThe sister of alfonso is antionette, kari.\nThe brother of alfonso is colby, dominick.\nThe mother of alfonso is kanesha.\nThe father of alfonso is derick.\nThe child of alfonso is ellis.\nThe son of alfonso is ellis.\nThe wife of alfonso is ila.\n\n## Friends\nThe friend of alfonso is vicente, kanesha, lyndia, meghann, rosalee.\n\n## Attributes\nThe date of birth of alfonso is 0240-12-31.\nThe job of alfonso is translator.\nThe hobby of alfonso is microbiology.\n"
        )

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
            "<attribute_name>_1",
            "is",
            "<attribute_value>_1",
            "?",
        ]
        assert data[0]["question"] == "Who is the daughter of the person whose job is air cabin crew ?"
        assert data[0]["query"] == ["daughter(Y_2, Y_4)", "job(Y_2, 'air cabin crew')"]
        assert data[0]["answer"] == []

    # clean up test_out directory
    shutil.rmtree("test_out")
