import os
import argparse
import random
import openai
from faker import Faker
from nltk import CFG

from CFG_utils import * 

def get_arguments():
    parser = argparse.ArgumentParser(description="Generate articles from Prolog files")
    parser.add_argument("--pl_file", type=str, default='tests/family_tree.pl', help="Path to the Prolog file")
    parser.add_argument("--output_folder", type=str, default= 'output', help="Path to the output folder")
    return parser.parse_args()

if __name__ == "__main__":
    # get arguments
    args = get_arguments()
    # set seed
    Faker.seed(0)
    fake = Faker()
    #make directories
    bio_folder = os.path.join(args.output_folder, 'bio')
    CFG_folder = os.path.join(args.output_folder, 'CFG')
    # TODO want to put prologs and DLVs also in the same folder
    os.makedirs(CFG_folder, exist_ok=True)
    os.makedirs(bio_folder, exist_ok=True)
    # load the prolog file
    with open(args.pl_file, "r") as f:
        lines = f.readlines()
        for line in lines:
            import pdb; pdb.set_trace()
            if line.startswith("female") or line.startswith("male"):
                person = match_name(line)
                job = fake.job()
                print(f"{person} is a {job}")
            else:
                print('skip line')
                continue

            # import pdb; pdb.set_trace()
            # allow multiple tries and only write to file if a bio is successfully generated
            bio, cfg = generate_article_with_retries(person, job, max_attempts=10)

            # write the CFG to a file
            CFG_file = os.path.join(CFG_folder, f"{person}_CFG.txt")
            with open(CFG_file, "w") as file:
                file.write(cfg)

            # write to file
            bio_file = os.path.join(bio_folder, f"{person}_bio.txt")
            write_bio(bio, bio_file)
            print(f"writen bio for {person} to {person}_bio.txt")