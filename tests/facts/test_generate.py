from phantom_wiki.facts import get_database
from phantom_wiki.facts.person import generate_population
from phantom_wiki.facts.attributes.generate import (generate_jobs,
                                                    generate_hobbies)
from tests.facts.family import FAMILY_TREE_SMALL_EXAMPLE_PATH

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
    db = get_database(FAMILY_TREE_SMALL_EXAMPLE_PATH)
    db.define("female/1", "male/1", "nonbinary/1", "age/2")
    jobs = generate_jobs(db.get_names(), seed=1)
    assert jobs == {
        "anastasia": "contractor",
        "angelina": "teacher, adult education",
        "charlotte": "biomedical scientist",
        "clara": "freight forwarder",
        "elena": "commercial/residential surveyor",
        "helga": "research scientist (life sciences)",
        "lena": "production assistant, television",
        "lisa": "public house manager",
        "mary": "museum education officer",
        "mia": "engineer, manufacturing systems",
        "natalie": "chief marketing officer",
        "nora": "ranger/warden",
        "sarah": "air cabin crew",
        "vanessa": "newspaper journalist",
        "elias": "police officer",
        "fabian": "translator",
        "felix": "accountant, chartered",
        "gabriel": "product designer",
        "jan": "geographical information systems officer",
        "jonas": "estate manager/land agent",
        "lorenz": "therapist, art",
        "maximilian": "civil engineer, consulting",
        "michael": "investment banker, corporate",
        "oskar": "airline pilot",
        "patrick": "advertising copywriter",
        "simon": "agricultural engineer",
        "thomas": "special educational needs teacher",
        "vincent": "acupuncturist"
    }
def test_generate_hobbies():
    db = get_database(FAMILY_TREE_SMALL_EXAMPLE_PATH)
    db.define("female/1", "male/1", "nonbinary/1", "age/2")
    hobbies = generate_hobbies(db.get_names(), seed=1)
    # import json
    # with open("hobbies.json", "w") as f:
    #     json.dump(hobbies, f, indent=4)
    assert hobbies == {
        "anastasia": "meditation",
        "angelina": "meteorology",
        "charlotte": "biology",
        "clara": "meteorology",
        "elena": "dolls",
        "helga": "photography",
        "lena": "shogi",
        "lisa": "dominoes",
        "mary": "tether car",
        "mia": "architecture",
        "natalie": "geocaching",
        "nora": "trainspotting",
        "sarah": "bus spotting[22",
        "vanessa": "research",
        "elias": "geography",
        "fabian": "microbiology",
        "felix": "canoeing",
        "gabriel": "learning",
        "jan": "dairy farming",
        "jonas": "fossil hunting",
        "lorenz": "sociology",
        "maximilian": "finance",
        "michael": "meditation",
        "oskar": "wikipedia editing",
        "patrick": "radio-controlled car racing",
        "simon": "social studies",
        "thomas": "judo",
        "vincent": "flying disc"
    }