from faker import Faker
from .constants import HOBBIES
from ..family.person_factory import Person
from numpy.random import default_rng

def generate_jobs(familytrees: list[Person], seed=1) -> dict[str, str]:
    """
    Generate a job for each person in the family trees.
    """
    fake = Faker()
    print(f"Setting seed for Faker to {seed}")
    Faker.seed(seed)
    jobs = {}
    for tree in familytrees:
        for person in tree:
            name = person.name
            jobs[name] = {}
            dod = person.date_of_death
            dob = person.date_of_birth
            age_at_death = dod.year - dob.year - ((dod.month, dod.day) < (dob.month, dob.day))
            # if the person died before the age of 18, they don't have a job
            if age_at_death < 18:
                jobs[name]['job'] = None
                jobs[name]['start_date'] = None
                continue
            else:
                while True:
                    job = fake.job().lower()
                    if "'" not in job:
                        break
                jobs[name]['job'] = job
                # start_date of the job is the person's 18th birthday
                jobs[name]['start_date'] = dob.replace(year=dob.year + 18)
    return jobs

def generate_hobbies(names: list[str], seed=1) -> dict[str, str]:
    rng = default_rng(seed)
    hobbies = {}
    for name in names:
        category = rng.choice(list(HOBBIES.keys()))
        hobbies[name] = rng.choice(HOBBIES[category])
    return hobbies
