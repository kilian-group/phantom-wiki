# Usage:
# Creating questions:
#   python -m phantom_wiki -op <output path>

# standard imports
import json
import os
import numpy as np

# phantom wiki functionality
from .facts import (get_database,
                    db_generate_population,
                    db_generate_friendships,
                    db_generate_attributes)
from .core.article import get_articles
from .facts import db_generate_attributes, db_generate_population, get_database
from .facts.templates import generate_templates
from .facts.sample import sample
from .utils import blue, get_parser, generate_unique_id
from .facts.family import fam_gen_parser

def main(args):
    print(f"Output dir: {args.output_dir}")
    
    # 
    # Step 1. Generate facts
    #
    db = get_database()
    db.define("nonbinary/1", "age/2")
    blue("Generating facts")
    if False:
        db_generate_population(db, 100, args.seed)
        db.define("parent/2")
    else:
        # TODO: add our implementation of family graph
        from .facts import db_generate_family
        db_generate_family(db, args)
    # generate friend relationships between people in the database
    db_generate_friendships(db, args.seed)
    # generate jobs, hobbies for each person in the database
    db_generate_attributes(db, args.seed)

    #
    # Step 2. Generate articles
    # Currently, the articles are comprised of a list of facts.
    #
    blue("Generating articles")
    # TODO: add code to merge family and CFG articles
    # currently, we just pass in the family article
    articles = get_articles(db, db.get_names())
    if args.article_format == "txt":
        article_dir = os.path.join(args.output_dir, "articles")
        print(f"Saving articles to: {article_dir}")
        os.makedirs(article_dir, exist_ok=True)
        for name, article in articles.items():
            with open(os.path.join(article_dir, f"{name}.txt"), "w") as file:
                file.write(article)
    elif args.article_format == "json":
        save_path = os.path.join(args.output_dir, "articles.json")
        print(f"Saving articles to: {save_path}")
        with open(save_path, "w") as file:
            json.dump([{"title" : name, "article" : article} for name, article in articles.items()], file, indent=4)
    else:
        raise ValueError(f"Article format {args.article_format} not supported!")

    #
    # Step 3. Generate question-answer pairs
    #
    blue("Generating question answer pairs")
    # TODO: add CLI argument for the depth
    # TODO: add CLI argument for the number of questions per type
    # TODO: add valid only flag
    templates = generate_templates(depth=6)
    # sample questions for each template (i.e., type)
    if args.question_format == "json_by_type":
        question_dir = os.path.join(args.output_dir, "questions")
        print(f"Saving questions to: {question_dir}")
        os.makedirs(question_dir, exist_ok=True)

    rng = np.random.default_rng(args.seed)
    n_questions = 10
    for i, (question_template, query_template, answer) in enumerate(templates):
        questions = []
        for _ in range(n_questions):
            _, question, query = sample(
                db, 
                question_template, 
                query_template, 
                rng=rng,
                valid_only=False
            )
            results = [str(x[answer]) for x in db.query(", ".join(query))]
            questions.append({
                "id": generate_unique_id(),
                "question": question,
                "answer": results,
                "query": query,
                "template": question_template,
                "type": i, # this references the template type
            })
            
            if args.question_format == "json_by_type":
                with open(os.path.join(question_dir, f"type{i}.json"), "w") as file:
                    json.dump(questions, file, indent=4)

    if args.question_format == "json":
        # save all questions to a single file
        save_path = os.path.join(args.output_dir, "questions.json")
        print(f"Saving questions to: {save_path}")
        with open(save_path, "w") as file:
            json.dump(questions, file, indent=4)

if __name__ == "__main__":
    # we combine a base parser with the family generator parser
    # TODO: add parser for other generation components
    # - friend
    # - attribute
    parser = get_parser(parents=[fam_gen_parser])
    args, _ = parser.parse_known_args()
    main(args)
