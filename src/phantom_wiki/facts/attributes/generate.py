from faker import Faker
from .constants import HOBBIES
from ..database import Database
from numpy.random import default_rng

def generate_jobs(names: list[str], seed=1) -> dict[str, str]:
    """
    Generate a job for each name in the list.
    """
    fake = Faker()
    print(f"Setting seed for Faker to {seed}")
    Faker.seed(seed)
    jobs = {}
    for name in names:
        jobs[name] = fake.job().lower()
    return jobs

def generate_hobbies(names: list[str], seed=1) -> dict[str, str]:
    rng = default_rng(seed)
    hobbies = {}
    for name in names:
        category = rng.choice(list(HOBBIES.keys()))
        hobbies[name] = rng.choice(HOBBIES[category])
    return hobbies
