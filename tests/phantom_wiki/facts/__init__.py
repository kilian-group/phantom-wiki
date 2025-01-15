import json
from importlib.resources import files

# Reference outputs for question generation
TEMPLATES_DEPTH_6_PATH = files("tests").joinpath("phantom_wiki/resources/templates/templates_depth_6.json")
TEMPLATES_DEPTH_8_PATH = files("tests").joinpath("phantom_wiki/resources/templates/templates_depth_8.json")
TEMPLATES_DEPTH_10_PATH = files("tests").joinpath("phantom_wiki/resources/templates/templates_depth_10.json")

# Reference outputs for attribute generation
JOBS_PATH = files("tests").joinpath("phantom_wiki/resources/facts/jobs.json")
HOBBIES_PATH = files("tests").joinpath("phantom_wiki/resources/facts/hobbies.json")

# Reference database
DATABASE_SMALL_PATH = files("tests").joinpath("phantom_wiki/resources/databases/small.pl")
DATABASE_SMALL_107 = files("tests").joinpath("phantom_wiki/resources/databases/small_107.pl")

# Question reference outputs
QUESTIONS_DICT = {}
for i in range(8):
    with open(files("tests").joinpath(f"phantom_wiki/resources/questions/sample_{i}.json")) as f:
        # NOTE: json saves tuples as lists, so we need to convert them back to tuples
        QUESTIONS_DICT[i] = tuple(json.load(f))

QUESTIONS_VALID_DICT = {}
for i in range(8):
    with open(files("tests").joinpath(f"phantom_wiki/resources/questions/sample_{i}_valid.json")) as f:
        QUESTIONS_VALID_DICT[i] = tuple(json.load(f))
