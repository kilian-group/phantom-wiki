import os
from phantom_wiki.facts import get_database
from phantom_wiki.core.article import get_articles
from tests.facts.family import FAMILY_TREE_SMALL_EXAMPLE_PATH

def test_get_articles():
    output_path = "out"
    db = get_database(FAMILY_TREE_SMALL_EXAMPLE_PATH)
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
