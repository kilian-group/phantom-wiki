from numpy.random import default_rng

from .constants import HOBBIES, JOBS


def generate_jobs(names: list[str], seed=1) -> dict[str, str]:
    """
    Generate a job for each name in the list.
    """
    rng = default_rng(seed)
    jobs = {}
    for name in names:
        jobs[name] = rng.choice(JOBS)
    return jobs


def generate_hobbies(names: list[str], seed=1) -> dict[str, str]:
    rng = default_rng(seed)
    hobbies = {}
    for name in names:
        category = rng.choice(list(HOBBIES.keys()))
        hobbies[name] = rng.choice(HOBBIES[category])
    return hobbies
