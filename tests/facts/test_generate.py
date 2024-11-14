from phantom_wiki.facts import get_database
from phantom_wiki.facts.person import generate_population
from phantom_wiki.facts.attributes.generate import generate_jobs
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
    jobs = generate_jobs(db.get_names(), seed=1)
    assert jobs == {
        "anastasia": "Contractor",
        "angelina": "Teacher, adult education",
        "charlotte": "Biomedical scientist",
        "clara": "Freight forwarder",
        "elena": "Commercial/residential surveyor",
        "helga": "Research scientist (life sciences)",
        "lena": "Production assistant, television",
        "lisa": "Public house manager",
        "mary": "Museum education officer",
        "mia": "Engineer, manufacturing systems",
        "natalie": "Chief Marketing Officer",
        "nora": "Ranger/warden",
        "sarah": "Air cabin crew",
        "vanessa": "Newspaper journalist",
        "elias": "Police officer",
        "fabian": "Translator",
        "felix": "Accountant, chartered",
        "gabriel": "Product designer",
        "jan": "Geographical information systems officer",
        "jonas": "Estate manager/land agent",
        "lorenz": "Therapist, art",
        "maximilian": "Civil engineer, consulting",
        "michael": "Investment banker, corporate",
        "oskar": "Airline pilot",
        "patrick": "Advertising copywriter",
        "simon": "Agricultural engineer",
        "thomas": "Special educational needs teacher",
        "vincent": "Acupuncturist"
    }
