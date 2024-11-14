from faker import Faker
from ..database import Database

def generate_jobs(names: list[str], seed=1) -> dict[str, str]:
    """
    Generate a job for each name in the list.
    """
    fake = Faker()
    print(f"Setting seed for Faker to {seed}")
    Faker.seed(seed)
    jobs = {}
    for name in names:
        jobs[name] = fake.job()
    return jobs

def generate_hobbies(names: list[str], seed=1) -> dict[str, str]:
    pass
