import json
from importlib.resources import files
# reference outputs for question generation
DEPTH_6_PATH = files("tests").joinpath("facts/templates_depth_6.json")
DEPTH_8_PATH = files("tests").joinpath("facts/templates_depth_8.json")
DEPTH_10_PATH = files("tests").joinpath("facts/templates_depth_10.json")
# reference outputs for attribute generation
JOBS_PATH = files("tests").joinpath("facts/jobs.json")
HOBBIES_PATH = files("tests").joinpath("facts/hobbies.json")
# question reference outputs
QUESTIONS_DICT = {}
for i in range(8):
    with open(files("tests").joinpath(f"facts/sample_{i}.json")) as f:
        # NOTE: json saves tuples as lists
        # so we need to convert them back to tuples
        QUESTIONS_DICT[i] = tuple(json.load(f))
QUESTIONS_VALID_DICT = {}
for i in range(8):
    with open(files("tests").joinpath(f"facts/sample_{i}_valid.json")) as f:
        QUESTIONS_VALID_DICT[i] = tuple(json.load(f))