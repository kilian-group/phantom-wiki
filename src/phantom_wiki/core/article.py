
bio_list = []
cfg_list = []
for person in person_list:
    # get the job article
    job = fake.job()
    print(f"{person} is a {job}")
    # allow multiple tries and only write to file if a bio is successfully generated
    if args.skip_cfg:
        bio, cfg = generate_article_with_retries(None, None, CFG_file=os.path.join(args.cfg_dir, f"{person}_CFG.txt"), max_attempts=10)
    else:
        bio, cfg = generate_article_with_retries(person, job, CFG_file=None, max_attempts=10)

    # write the CFG to a file
    CFG_file = os.path.join(CFG_folder, f"{person}_CFG.txt")
    print(f"writting CFG for {person} to {person}_CFG.txt")
    with open(CFG_file, "w") as file:
        file.write(cfg)

    # write to file
    bio_file = os.path.join(bio_folder, f"{person}_bio.txt")
    print(f"writting bio for {person} to {person}_bio.txt")
    write_bio(bio, bio_file)

    bio_list.append(bio)
    cfg_list.append(cfg)
