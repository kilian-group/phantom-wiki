from phantom_wiki.facts import Database
from phantom_wiki.facts.person import generate_population
from phantom_wiki.facts.attributes.generate import (generate_jobs,
                                                    generate_hobbies)
from tests.phantom_wiki.facts.family import FACTS_SMALL_EXAMPLE_PATH

# 
# Test for population generation
# 
def test_generate_population():
    population = generate_population(size=10)
    assert population == [
        {
            "first_name": "Brandy",
            "last_name": "Boone",
            "affix": None,
            "age": 74,
            "gender": "female"
        },
        {
            "first_name": "Dawn",
            "last_name": "Simpson",
            "affix": None,
            "age": 94,
            "gender": "female"
        },
        {
            "first_name": "Matthew",
            "last_name": "Kramer",
            "affix": None,
            "age": 27,
            "gender": "male"
        },
        {
            "first_name": "Alyssa",
            "last_name": "Houston",
            "affix": None,
            "age": 81,
            "gender": "female"
        },
        {
            "first_name": "Pamela",
            "last_name": "Smith",
            "affix": None,
            "age": 82,
            "gender": "female"
        },
        {
            "first_name": "Mikayla",
            "last_name": "Perez",
            "affix": None,
            "age": 53,
            "gender": "female"
        },
        {
            "first_name": "Steven",
            "last_name": "Johnson",
            "affix": None,
            "age": 96,
            "gender": "male"
        },
        {
            "first_name": "Joshua",
            "last_name": "Crosby",
            "affix": None,
            "age": 13,
            "gender": "male"
        },
        {
            "first_name": "Claire",
            "last_name": "Henderson",
            "affix": None,
            "age": 6,
            "gender": "female"
        },
        {
            "first_name": "Connie",
            "last_name": "Kim",
            "affix": None,
            "age": 27,
            "gender": "female"
        }
    ]

# 
# Test for attributes
# 
def test_generate_jobs():
    db = Database.from_disk(FACTS_SMALL_EXAMPLE_PATH)
    jobs = generate_jobs(sorted(db.get_person_names()), seed=1)
    from tests.phantom_wiki.facts import JOBS_PATH
    import json
    with open(JOBS_PATH, "r") as f:
        reference_jobs = json.load(f)
    # with open("jobs.json", "w") as f:
    #     json.dump(jobs, f, indent=4)
    assert jobs == reference_jobs

def test_generate_hobbies():
    db = Database.from_disk(FACTS_SMALL_EXAMPLE_PATH)
    hobbies = generate_hobbies(sorted(db.get_person_names()), seed=1)
    from tests.phantom_wiki.facts import HOBBIES_PATH
    import json
    with open(HOBBIES_PATH, "r") as f:
        reference_hobbies = json.load(f)
    # with open("hobbies.json", "w") as f:
    #     json.dump(hobbies, f, indent=4)
    assert hobbies == reference_hobbies
