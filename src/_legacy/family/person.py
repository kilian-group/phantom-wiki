# TODO simplify

from faker import Faker
import numpy as np
import random
import pandas as pd
from pyDatalog import pyDatalog

current_year = 2024


class Person(pyDatalog.Mixin):
    def __init__(self, first_name, last_name, affix, age, gender):
        super(Person, self).__init__()
        self.first_name = first_name
        self.last_name = last_name
        self.affix = affix
        self.age = age
        self.gender = gender

    def __repr__(self):
        return f"{self.first_name} {self.last_name}"

    def table(self):
        affix = f" {self.affix}" if self.affix else ""
        return f"Born\t{self.first_name} {self.last_name}{affix}\n{current_year-self.age} (age {self.age})\n{self.gender.capitalize()}\n"


def generate_person(
    localized=["en_US"],
    gender_dist=[0.5, 0.5, 0],
    get_age=lambda: np.random.randint(0, 99),
):
    fake = Faker(localized)
    gender = random.choices(["male", "female", "NB"], weights=gender_dist)[0]
    age = get_age()
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

    if np.random.rand() < 0.99:
        affix = None

    return Person(first_name, last_name, affix, age, gender)


def generate_population(size, generate_person):
    return pd.DataFrame([generate_person() for _ in range(size)])


if __name__ == "__main__":
    population = generate_population(100, lambda: vars(generate_person()))
    print(population)
    print(generate_person().table())
