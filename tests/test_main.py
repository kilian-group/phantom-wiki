# standard imports
import json
import os

import numpy as np

from phantom_wiki.core.article import get_articles

# phantom wiki functionality
from phantom_wiki.facts import (
    db_generate_attributes,
    db_generate_friendships,
    db_generate_population,
    get_database,
)
from phantom_wiki.facts.family import fam_gen_parser
from phantom_wiki.facts.sample import sample
from phantom_wiki.facts.templates import generate_templates
from phantom_wiki.utils import blue, get_parser


def test_generate_articles():
    parser = get_parser(parents=[fam_gen_parser])
    args, _ = parser.parse_known_args()

    #
    # Step 1. Generate facts
    #
    db = get_database()
    db.define("nonbinary/1", "age/2")
    blue("Generating facts")
    if False:
        db_generate_population(db, 10, args.seed)
        db.define("parent/2")
    else:
        from phantom_wiki.facts import db_generate_family

        db_generate_family(db, args)
    db_generate_friendships(db, args.seed)
    db_generate_attributes(db, args.seed)

    # Step 2. Generate articles
    #
    blue("Generating articles")
    # TODO: add code to merge family and CFG articles
    # currently, we just pass in the family article
    article_dir = os.path.join(args.output_dir, "articles")
    print(f"Saving articles to: {article_dir}")
    os.makedirs(article_dir, exist_ok=True)
    articles = get_articles(db, db.get_names())
    for name, article in articles.items():
        with open(os.path.join(article_dir, f"{name}_article.txt"), "w") as file:
            file.write(article)

    #
    # Step 3. Generate question-answer pairs
    #
    blue("Generating question answer pairs")
    # TODO: add CLI argument for the depth
    # TODO: add CLI argument for the number of questions per type
    # TODO: add valid only flag
    templates = generate_templates(depth=6)
    # sample questions for each template (i.e., type)
    question_dir = os.path.join(args.output_dir, "questions")
    print(f"Saving questions to: {question_dir}")
    os.makedirs(question_dir, exist_ok=True)
    rng = np.random.default_rng(args.seed)
    n_questions = 10
    for i, (question_template, query_template, answer) in enumerate(templates):
        questions = []
        for _ in range(n_questions):
            _, question, query = sample(db, question_template, query_template, rng=rng, valid_only=False)
            results = [str(x[answer]) for x in db.query(", ".join(query))]
            questions.append(
                {
                    "template": question_template,
                    "question": question,
                    "query": query,
                    "answer": results,
                }
            )
            with open(os.path.join(question_dir, f"type{i}_question.json"), "w") as file:
                json.dump(questions, file, indent=4)

    # test that the articles were generated correctly
    with open(os.path.join(article_dir, "alix_article.txt")) as file:
        article = file.read()
        assert (
            article
            == "# alix\n\n## Family\nalix's siblings are alton, gabriel.\nThe brother of alix is alton, gabriel.\nThe mother of alix is dixie.\nThe father of alix is brooks.\n\n## Friends\nThe friend of alix is bernadine, freda, katelyn, kendrick.\n\n## Attributes\nThe job of alix is contractor.\nThe hobby of alix is meditation.\n"
        )

    # test that the questions were generated correctly
    with open(os.path.join(question_dir, "type0_question.json")) as file:
        data = json.load(file)
        assert len(data) == 10
        assert len(data[0]) == 4
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
