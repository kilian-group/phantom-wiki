from faker import Faker
import re
import os

import openai
import textwrap
from cfg import generate_sentence, create_bio
from nltk import CFG

def write_bio(bio, file_path):
    bio = textwrap.fill(bio, width=80)
    with open(file_path, "w") as file:
        file.write(bio)

def match_name(line):
    # import pdb; pdb.set_trace()
    pattern = r"\((?:[A-Z][a-z]+|[a-z]+(?:\s[A-Z][a-z]+)*)\)"
    matches = re.findall(pattern, line)
    names = [match.strip("()") for match in matches]
    return names[0]

def extract_content_between_triple_quotes(paragraph):
    # Regex pattern to capture content between the first pair of triple quotes
    match = re.search(r"'''(.*?)'''", paragraph, flags=re.DOTALL)
    
    if match:
        return match.group(1).strip()
    else:
        return paragraph  # Return an empty string if no triple quotes are found

if __name__ == "__main__":
    # set seed
    Faker.seed(0)
    fake = Faker()
    # load the prolog file
    import pdb; pdb.set_trace()
    with open("tests/family_tree.pl", "r") as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("female") or line.startswith("male"):
                person = match_name(line)
                job = fake.job()
                print(f"{person} is a {job}")

            # prompt openai to generate a cfg using gpt-4o
            # TODO need a better prompt to prevent the model from adding a family name
            prompt = f"write me a CFG using arrow notation to generate a bio for {person} whose occupation is {job} using fictional names and entities, ONLY OUTPUT THE CFG" 
            response =openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": prompt}
                ]
            )
            raw_text = response.choices[0].message.content
            raw_text = raw_text.replace("```", "")
            # parse the grammar and generate a bio
            grammar = CFG.fromstring(raw_text)
            bio = generate_sentence(grammar)
            # write to file
            bio_folder = "tests/bios"
            os.makedirs(bio_folder, exist_ok=True)
            bio_file = os.path.join(bio_folder, f"{person}_bio.txt")
            write_bio(bio, bio_file)
            print(f"writen bio for {person} to {person}_bio.txt")