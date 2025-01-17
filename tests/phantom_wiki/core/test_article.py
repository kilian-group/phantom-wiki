import os

from phantom_wiki.core.article import get_articles
from phantom_wiki.facts import get_database
from tests.phantom_wiki.facts import DATABASE_SMALL_107


def test_get_articles():
    return

    # TODO: add test that only checks the output of get_articles
    # for now, just use test_main.py to test the entire pipeline
    output_path = "out"
    db = get_database(DATABASE_SMALL_107)
    # define predicates that are not in the above family tree
    db.define("nonbinary/1", "age/2", "job/2", "hobby/2")

    print("Generating articles")
    article_dir = os.path.join(output_path, "articles")
    os.makedirs(article_dir, exist_ok=True)
    print(f"Saving articles to: {article_dir}")
    articles = get_articles(db, db.get_names())
    # save the articles to a file
    for name, article in articles.items():
        with open(os.path.join(article_dir, f"{name}_family.txt"), "w") as file:
            file.write(article)
