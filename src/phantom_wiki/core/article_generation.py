import random

from nltk import CFG

bio_list = []
cfg_list = []
for person in person_list:
    # get the job article
    job = fake.job()
    print(f"{person} is a {job}")
    # allow multiple tries and only write to file if a bio is successfully generated
    if args.skip_cfg:
        bio, cfg = generate_article_with_retries(
            None, None, CFG_file=os.path.join(args.cfg_dir, f"{person}_CFG.txt"), max_attempts=10
        )
    else:
        bio, cfg = generate_article_with_retries(person, job, CFG_file=None, max_attempts=10)

    # write the CFG to a file
    CFG_file = os.path.join(CFG_folder, f"{person}_CFG.txt")
    print(f"writing CFG for {person} to {person}_CFG.txt")
    with open(CFG_file, "w") as file:
        file.write(cfg)

    # write to file
    bio_file = os.path.join(bio_folder, f"{person}_bio.txt")
    print(f"writing bio for {person} to {person}_bio.txt")
    write_bio(bio, bio_file)

    bio_list.append(bio)
    cfg_list.append(cfg)


def generate_sentence(grammar, production=None):
    """Samples a sentence from a context-free grammar."""
    if production is None:
        production = grammar.start()

    if isinstance(production, str):
        return production
    else:
        chosen_prod = random.choice(grammar.productions(lhs=production))
        return " ".join(generate_sentence(grammar, prod) for prod in chosen_prod.rhs())


def generate_article_with_retries(
    person,
    job,
    # if using existing CFG, pass the path to
    CFG_file: str = None,
    max_attempts=100,
):
    if CFG_file is not None:
        try:
            # If a CFG file is provided, read the CFG from the file
            with open(CFG_file) as file:
                raw_text = file.read()
            processed_text = formatting_raw_input(raw_text)
            grammar = CFG.fromstring(processed_text)
            article = generate_sentence(grammar)
            if article:
                print(f"Successfully generated article for {person}")
                return article, processed_text

        except Exception as e:
            print(f"Error generating article - {e}")
            # regenerate the CFG with retries
            for attempt in range(max_attempts):
                try:
                    # Get a new CFG and attempt to generate an article
                    # Each time we get a potentially different CFG
                    CFG_file = get_response(person, job, cfg_str=None)
                    processed_text = formatting_raw_input(raw_text)
                    grammar = CFG.fromstring(processed_text)
                    article = generate_sentence(grammar)
                    if article:  # Check if the article is non-empty
                        print(f"Attempt {attempt + 1}: Successfully generated article for {person}")
                        return article, processed_text
                except Exception as e:
                    # Catch any exceptions that might occur during generation
                    print(f"Attempt {attempt + 1}: Error generating article - {e}")

    else:
        # If no CFG file is provided, generate a new CFG and attempt to generate an article
        for attempt in range(max_attempts):
            try:
                # Get a new CFG and attempt to generate an article
                # Each time we get a potentially different CFG
                CFG_file = get_CFG(person, job)
                processed_text = formatting_raw_input(raw_text)
                grammar = CFG.fromstring(processed_text)
                article = generate_sentence(grammar)
                if article:  # Check if the article is non-empty
                    print(f"Attempt {attempt + 1}: Successfully generated article for {person}")
                    return article, processed_text
            except Exception as e:
                # Catch any exceptions that might occur during generation
                print(f"Attempt {attempt + 1}: Error generating article - {e}")
    return "Failed to generate an article after multiple attempts."
