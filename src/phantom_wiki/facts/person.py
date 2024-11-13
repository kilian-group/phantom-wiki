# TODO simplify

from faker import Faker
import numpy as np
import random
import pandas as pd
# from pyDatalog import pyDatalog

current_year = 2024


# class Person(pyDatalog.Mixin):
#     def __init__(self, first_name, last_name, affix, age, gender):
#         super(Person, self).__init__()
#         self.first_name = first_name
#         self.last_name = last_name
#         self.affix = affix
#         self.age = age
#         self.gender = gender

#     def __repr__(self):
#         return f"{self.first_name} {self.last_name}"

#     def table(self):
#         affix = f" {self.affix}" if self.affix else ""
#         return f"Born\t{self.first_name} {self.last_name}{affix}\n{current_year-self.age} (age {self.age})\n{self.gender.capitalize()}\n"
from collections import namedtuple
Person = namedtuple("Person", ["first_name", "last_name", "affix", "age", "gender"])

def generate_person(rng=None,
                    localized=["en_US"],
                    gender_dist=[0.5, 0.5, 0]):
    fake = Faker(localized)
    gender = rng.choice(["male", "female", "NB"], p=gender_dist)
    age = rng.integers(0, 99, dtype=int)
    first_name, last_name, affix = None, None, None

    if gender == "male":
        first_name, last_name, affix = (
            fake.first_name_male(),
            fake.last_name_male(),
            fake.suffix_male(),
        )

    if gender == "female":
        first_name, last_name, affix = (
            fake.first_name_female(),
            fake.last_name_female(),
            fake.suffix_female(),
        )

    if gender == "NB":
        first_name, last_name, affix = (
            fake.first_name_nonbinary(),
            fake.last_name_nonbinary(),
            fake.suffix_nonbinary(),
        )

    if rng.random() < 0.99:
        affix = None

    person = Person(
        first_name=first_name, 
        last_name=last_name, 
        affix=affix, 
        age=age, 
        gender=gender
    )
    # convert namedtuple to a dictionary
    person = person._asdict()
    return person


def generate_population(size, seed=1):
    rng = np.random.default_rng(seed=seed)
    Faker.seed(seed)
    return [generate_person(rng=rng) for _ in range(size)]


# if __name__ == "__main__":
#     population = generate_population(100, lambda: vars(generate_person()))
#     print(population)
#     print(generate_person().table())
