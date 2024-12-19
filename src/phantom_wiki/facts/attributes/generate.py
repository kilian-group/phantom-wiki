import random
from datetime import timedelta

from faker import Faker
from numpy.random import default_rng

from ..family.person_factory import Career_Event, Person
from .constants import HOBBIES


def generate_jobs(familytrees: list[Person], seed=1):
    """
    Generate a job for each person in the family trees.
    For each person, check if they lived past the age of 18.
    If they did, generate a job for them. And add the job as a career event.
    For example: start_job("software engineer", "2020-01-01")
    Otherwise, skip them.

    Args:
        familytrees: a list of family trees (args.num_samples)
        seed: random seed

    Returns:
        None
    """
    fake = Faker()
    print(f"Setting seed for Faker to {seed}")
    Faker.seed(seed)
    for tree in familytrees:
        for person in tree:
            dod = person.date_of_death
            dob = person.date_of_birth
            age_at_death = dod.year - dob.year - ((dod.month, dod.day) < (dob.month, dob.day))
            # if the person died before the age of 18, they don't have a job
            if age_at_death < 18:
                continue
            else:
                while True:
                    job = fake.job().lower()
                    if "'" not in job:
                        break
                # start_date of the job is the person's 18th birthday
                start_date = dob.replace(year=dob.year + 18)
                # add the job as a career event for the person
                person.Career_Events.append(Career_Event("start_job", job, start_date))


def shuffle_job_market(familytrees: list[Person], args) -> None:
    """
    Similar to divorce and remarry, end jobs and start new ones.
    first round: end jobs
    For each person, check if they have a job.
    If yes and random number is less than unemployed_rate, end the job.
    The end date is a random date between the start date and the date of death.

    second round: start new jobs
    For each person, check if they are unemployed.
    If yes and random number is less than reemployed_rate, start a new job.
    The start date is a random date between the end date of the last job and the date of death.

    Args:
        familytrees: a list of family trees (args.num_samples)
        args:
            unemployed_rate: the probability that a person will be unemployed
            reemployed_rate: the probability that a person will be reemployed
            seed: random seed

    Returns:
        None
    """
    fake = Faker()
    print(f"Setting seed for Faker to {args.seed}")
    Faker.seed(args.seed)

    # loop over each person in the tree to end their current job
    for tree in familytrees:
        for person in tree:
            if len(person.Career_Events) == 0:
                continue
            elif random.random() < args.unemployed_rate:
                # end the current job
                if person.Career_Events:
                    last_event = person.Career_Events[-1]
                    job = last_event.job
                    type = last_event.type
                    assert type == "start_job", "The last event should be a start_job event."
                    delta = person.date_of_death - last_event.date
                    random_days = random.randint(0, delta.days)
                    end_date = last_event.date + timedelta(days=random_days)
                    person.Career_Events.append(Career_Event("end_job", job, end_date))
                else:
                    continue

    # loop over each person in the tree to start a new job
    for tree in familytrees:
        for person in tree:
            if random.random() < args.reemployed_rate:
                if len(person.Career_Events) > 0 and len(person.Career_Events) % 2 == 0:
                    last_event = person.Career_Events[-1]
                    assert last_event.type == "end_job", "The last event should be an end_job event."
                    delta = person.date_of_death - last_event.date
                    random_days = random.randint(0, delta.days)
                    start_date = last_event.date + timedelta(days=random_days)
                    while True:
                        job = fake.job().lower()
                        if "'" not in job and job != last_event.job:
                            break
                    person.Career_Events.append(Career_Event("start_job", job, start_date))
            else:
                continue


def generate_hobbies(names: list[str], seed=1) -> dict[str, str]:
    """
    Generate a hobby for each person in the list of names.

    Args:
        names: list of names
        seed: random seed

    Returns:
        hobbies: a dictionary with the name as the key and the hobby as the value.
        For example: {"John": "gardening"}

    """
    rng = default_rng(seed)
    hobbies = {}
    for name in names:
        category = rng.choice(list(HOBBIES.keys()))
        hobbies[name] = rng.choice(HOBBIES[category])
    return hobbies
