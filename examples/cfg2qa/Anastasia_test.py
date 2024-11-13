import random

import textwrap

# Define possible choices for each CFG terminal
bio_choices = ["intro career hobby personal_life"]
intro_choices = ["Anastasia surname is a talented occupation hailing from the vibrant city of city . "]
surname_choices = ["Vivaldi", "Belcanto", "Stradivarius"]
occupation_choices = ["musician"]
city_choices = ["Trevalin", "Nornwell", "Melodica"]
career_choices = ["She began her musical journey at the age of age , and has since performed at renowned venues like venue and festival . "]
age_choices = ["six", "nine", "eleven"]
venue_choices = ["the Harmonia Hall", "Symphony Theater", "Crescendo Arena"]
festival_choices = ["Harmony Fest", "Equinox Jubilee", "Allegro Night"]
hobby_choices = ["Apart from performing, Anastasia enjoys activity and often finds inspiration in the works of mentor . "]
activity_choices = ["composing original pieces", "teaching music", "exploring new musical genres"]
mentor_choices = ["Maestro Celesta", "the acclaimed lyricist Sonata Grove", "the legendary conductor Opus Forte"]
personal_life_choices = ["In her personal life, she shares her home with her companion, companion , and dreams of one day releasing an album titled album_title . "]
companion_choices = ["a charming cat named Melody", "a loyal dog called Rhapsody", "a talkative parrot named Aria"]
album_title_choices = ["Songs of the Horizon", "Celestial Echoes", "Euphonic Voyage"]

# Define questions associated with each CFG terminal
questions = {
    "intro": "What is Anastasia's introduction?",
    "surname": "What is Anastasia's last name?",
    "occupation": "What is Anastasia's profession?",
    "city": "Which city does Anastasia come from?",
    "career": "What is Anastasia's career path and achievements?",
    "age": "At what age did Anastasia begin her musical journey?",
    "venue": "At which venues has Anastasia performed?",
    "festival": "Which festivals has Anastasia performed at?",
    "hobby": "What are Anastasia's hobbies or interests apart from performing?",
    "activity": "What activities does Anastasia enjoy doing?",
    "mentor": "Whose works inspire Anastasia?",
    "personal_life": "Can you tell me about Anastasia's personal life and aspirations?",
    "companion": "Who is Anastasia's companion at home?",
    "album_title": "What is the title of the album Anastasia dreams of releasing one day?",
}

# Randomly generate values for each CFG terminal
bio = random.choice(bio_choices)
intro = random.choice(intro_choices)
surname = random.choice(surname_choices)
occupation = random.choice(occupation_choices)
city = random.choice(city_choices)
career = random.choice(career_choices)
age = random.choice(age_choices)
venue = random.choice(venue_choices)
festival = random.choice(festival_choices)
hobby = random.choice(hobby_choices)
activity = random.choice(activity_choices)
mentor = random.choice(mentor_choices)
personal_life = random.choice(personal_life_choices)
companion = random.choice(companion_choices)
album_title = random.choice(album_title_choices)

# Recursive expansion of the CFG to build the article
def expand_rule(rule):
    components = rule.split()
    expanded = []
    for component in components:
        if component.lower() in globals():
            expanded.append(expand_rule(globals()[component.lower()]))
        else:
            expanded.append(component.strip('"'))
    return ' '.join(expanded)

article = expand_rule(random.choice(bio_choices))

# Generate answers to each question based on selected values
answers = {
    questions["intro"]: intro,
    questions["surname"]: surname,
    questions["occupation"]: occupation,
    questions["city"]: city,
    questions["career"]: career,
    questions["age"]: age,
    questions["venue"]: venue,
    questions["festival"]: festival,
    questions["hobby"]: hobby,
    questions["activity"]: activity,
    questions["mentor"]: mentor,
    questions["personal_life"]: personal_life,
    questions["companion"]: companion,
    questions["album_title"]: album_title,
}


def write_questions():
    # Write to file
    with open("Anastasia_questions.txt", "w") as f:
        f.write("Article:\n" + textwrap.fill(article,width=80) + "\n\n")
        for question, answer in answers.items():
            f.write(f"{question}: {answer}\n")
