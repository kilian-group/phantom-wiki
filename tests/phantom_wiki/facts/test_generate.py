from phantom_wiki.facts import Database
from phantom_wiki.facts.attributes.generate import generate_hobbies, generate_jobs
from tests.phantom_wiki.facts import DATABASE_SMALL_PATH

#
# Test for attributes
#
def test_generate_jobs():
    db = Database.from_disk(DATABASE_SMALL_PATH)
    jobs = generate_jobs(sorted(db.get_names()), seed=1)
    import json

    from tests.phantom_wiki.facts import JOBS_PATH

    with open(JOBS_PATH) as f:
        reference_jobs = json.load(f)
    # with open("jobs.json", "w") as f:
    #     json.dump(jobs, f, indent=4)
    assert jobs == reference_jobs


def test_generate_hobbies():
    db = Database.from_disk(DATABASE_SMALL_PATH)
    hobbies = generate_hobbies(sorted(db.get_names()), seed=1)
    import json

    from tests.phantom_wiki.facts import HOBBIES_PATH

    with open(HOBBIES_PATH) as f:
        reference_hobbies = json.load(f)
    # with open("hobbies.json", "w") as f:
    #     json.dump(hobbies, f, indent=4)
    assert hobbies == reference_hobbies
