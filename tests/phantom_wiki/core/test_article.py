import os

from phantom_wiki.core.article import get_articles
from phantom_wiki.facts import Database
from tests.phantom_wiki.facts import DATABASE_SMALL_PATH


def test_get_articles():
    # NOTE: test_main.py also checks that get_articles returns the expected output for a small universe
    # TODO: add test that only checks the output of get_articles
    return

    db = Database.from_disk(DATABASE_SMALL_PATH)

    print("Generating articles")
    article_dir = os.path.join("test_out", "articles")
    os.makedirs(article_dir, exist_ok=True)
    print(f"Saving articles to: {article_dir}")
    articles = get_articles(db, db.get_person_names())
    # save the articles to a file
    for name, article in articles.items():
        with open(os.path.join(article_dir, f"{name}.txt"), "w") as file:
            file.write(article)

    # delete the articles
    for name in articles:
        os.remove(os.path.join(article_dir, f"{name}.txt"))
    os.rmdir(article_dir)
    print("Done")
