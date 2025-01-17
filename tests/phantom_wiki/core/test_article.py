import os
import json
from importlib.resources import files

ARTICLES_PATH = files("tests").joinpath("phantom_wiki/resources/articles/articles.json")

from phantom_wiki.core.article import get_articles
from phantom_wiki.facts.database import Database
from tests.phantom_wiki.facts import DATABASE_SMALL_107

db = Database.from_disk(DATABASE_SMALL_107)

def test_get_articles():
    print("Generating articles")
    articles = get_articles(db, db.get_names())
    # save the articles to a file
    # with open("articles.json", "w") as f:
    #     json.dump(articles, f, indent=4)

    # load the articles from the file
    with open(ARTICLES_PATH, "r") as f:
        expected_articles = json.load(f)

    assert articles == expected_articles