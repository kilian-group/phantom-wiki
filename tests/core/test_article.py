import os
from phantom_wiki.facts import get_database
from phantom_wiki.core.article import get_articles

def test_get_articles():
    output_path = "out"
    family_tree_path = "tests/facts/family/family_tree_26.pl"
    db = get_database(family_tree_path)

    print("Generating articles")
    article_dir = os.path.join(output_path, "articles")
    os.makedirs(article_dir, exist_ok=True)
    print(f"Saving articles to: {article_dir}")
    articles = get_articles(db, db.get_names())
    # save the articles to a file
    for name, article in articles.items():
        with open(os.path.join(article_dir, f"{name}_family.txt"), "w") as file:
            file.write(article)
    assert len(articles) == 26