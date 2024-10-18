# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     custom_cell_magics: kql
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.11.2
#   kernelspec:
#     display_name: dataset
#     language: python
#     name: dataset
# ---

# %%
import nltk
from nltk import CFG
import random

# %%

# Define the grammar
grammar = CFG.fromstring("""
    S -> Intro Background Expertise Projects Education

    Intro -> "Meet" | "Introducing" | "Presenting"
    Background -> "[Name], an experienced architect with a focus on" Area "." | "[Name] is a talented architect known for specializing in" Area "."
    Area -> "residential buildings" | "urban design" | "sustainable architecture" | "commercial spaces" | "historic preservation"
    Expertise -> "With over" Experience "years of experience, [Name] has successfully delivered various" ProjectType "."
    Experience -> "5" | "10" | "15" | "20+"
    ProjectType -> "residential homes" | "commercial complexes" | "green buildings" | "urban landscapes" | "adaptive reuse projects"

    Projects -> "Some of their notable projects include" ProjectList "." | "[Name]'s work is featured in projects like" ProjectList "."
    ProjectList -> "the revitalization of CityPark" | "the design of EcoTower" | "the development of GreenHaven Community" | "the restoration of Landmark Theater"

    Education -> "[Name] holds a degree in architecture from" University ", where they specialized in" Specialization "."
    University -> "Harvard University" | "MIT" | "Columbia University" | "University of Tokyo" | "ETH Zurich"
    Specialization -> "sustainable design" | "urban planning" | "building technology" | "architectural theory"
""")

# grammar = CFG.fromstring("""
#     S -> Intro Background Expertise Projects Education Family

#     Intro -> "Meet" | "Introducing" | "Presenting"
#     Background -> "[Name], an experienced architect with a focus on" Area "." | "[Name] is a talented architect known for specializing in" Area "."
#     Area -> "residential buildings" | "urban design" | "sustainable architecture" | "commercial spaces" | "historic preservation"
#     Expertise -> "With over" Experience "years of experience, [Name] has successfully delivered various" ProjectType "."
#     Experience -> "5" | "10" | "15" | "20+"
#     ProjectType -> "residential homes" | "commercial complexes" | "green buildings" | "urban landscapes" | "adaptive reuse projects"

#     Projects -> "Some of their notable projects include" ProjectList "." | "[Name]'s work is featured in projects like" ProjectList "."
#     ProjectList -> "the revitalization of CityPark" | "the design of EcoTower" | "the development of GreenHaven Community" | "the restoration of Landmark Theater"

#     Education -> "[Name] holds a degree in architecture from" University ", where they specialized in" Specialization "."
#     University -> "Harvard University" | "MIT" | "Columbia University" | "University of Tokyo" | "ETH Zurich"
#     Specialization -> "sustainable design" | "urban planning" | "building technology" | "architectural theory"

#     Family -> 
# """)


# %%

# Function to generate a random sentence from the CFG
def generate_sentence(grammar, production=None):
    if production is None:
        production = grammar.start()

    if isinstance(production, str):
        return production
    else:
        chosen_prod = random.choice(grammar.productions(lhs=production))
        return ' '.join(generate_sentence(grammar, prod) for prod in chosen_prod.rhs())



# %%

# Replace the placeholder with the architect's name
def create_bio(name):
    raw_bio = generate_sentence(grammar)
    return raw_bio.replace("[Name]", name)


# %%
architect_name = "John Doe"  # Replace with the desired architect's name
bio = create_bio(architect_name)
print(bio)


# %%
# save bio to a txt file with line width 80 chars using textwrap
import textwrap
bio = textwrap.fill(bio, width=80)
with open("architect_bio.txt", "w") as file:
    file.write(bio)

# %%
