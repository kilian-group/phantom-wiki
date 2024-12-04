from importlib.resources import files
# reference outputs for question generation
DEPTH_6_PATH = files("tests").joinpath("facts/templates_depth_6.json")
DEPTH_8_PATH = files("tests").joinpath("facts/templates_depth_8.json")
DEPTH_10_PATH = files("tests").joinpath("facts/templates_depth_10.json")
# reference outputs for attribute generation
JOBS_PATH = files("tests").joinpath("facts/jobs.json")
HOBBIES_PATH = files("tests").joinpath("facts/hobbies.json")