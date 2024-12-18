# standard imports
from argparse import ArgumentParser

# resource containing the attribute rules
from importlib.resources import files

# phantom wiki functionality
from ..database import Database
from .constants import ATTRIBUTE_FACT_TEMPLATES, ATTRIBUTE_RELATION, END_JOB_TEMPLATE, START_JOB_TEMPLATE
from .generate import generate_hobbies, generate_jobs, shuffle_job_market

ATTRIBUTE_RULES_PATH = files("phantom_wiki").joinpath("facts/attributes/rules.pl")

# TODO: add functionality to pass in CLI arguments

# Create parser for family tree generation
attributes_parser = ArgumentParser(description="Attributes generation", add_help=False)
attributes_parser.add_argument(
    "--unemployed-rate", type=float, default=0.0, help="The probability that a person is unemployed."
)
attributes_parser.add_argument(
    "--reemployed-rate", type=float, default=0.0, help="The probability that a person is reemployed."
)


#
# Functionality to read job information for each person in the database.
#
# job is a special attribute that has start and end date information
def get_job_info(db: Database, name: str):
    """
    Get job information for a person in the database.
    """
    jobs = []
    query = f"start_job('{name}', X, Y)"
    results = [{"job": result["X"], "start_date": result["Y"]} for result in db.query(query)]
    jobs.extend(results)
    query = f"end_job('{name}', X, Y)"
    results = [{"job": result["X"], "end_date": result["Y"]} for result in db.query(query)]
    jobs.extend(results)
    return jobs


def get_job_facts(db: Database, names: list[str]) -> dict[str, list[str]]:
    """
    Get job facts for a list of names.
    """
    facts = {}
    for name in names:
        jobs = get_job_info(db, name)
        person_facts = []
        for job in jobs:
            if "start_date" in job.keys() and job["job"] != "None":
                fact = (
                    START_JOB_TEMPLATE.replace("<subject>", name)
                    .replace("<job>", job["job"])
                    .replace("<date>", job["start_date"])
                )
            elif "end_date" in job.keys() and job["job"] != "None":
                fact = (
                    END_JOB_TEMPLATE.replace("<subject>", name)
                    .replace("<job>", job["job"])
                    .replace("<date>", job["end_date"])
                )
            else:
                fact = ""
            person_facts.append(fact)
        facts[name] = person_facts
    return facts


#
# Functionality to read the attributes for each person in the database.
#
def get_attributes(db: Database, name: str):
    """
    Get attributes for each person in the database.
    """
    attributes = {}
    for attr in ATTRIBUTE_RELATION:
        query = f"{attr}('{name}', X)"
        results = [result["X"] for result in db.query(query)]
        attributes[attr] = results
    return attributes


def get_attribute_facts(db: Database, names: list[str]) -> dict[str, list[str]]:
    """
    Get attribute facts for a list of names.
    """
    facts = {}
    for name in names:
        attributes = get_attributes(db, name)
        person_facts = []
        for attr, target in attributes.items():
            if target == []:
                continue
            attr_template = ATTRIBUTE_FACT_TEMPLATES[attr]
            fact = attr_template.replace("<subject>", name) + " " + ", ".join([str(s) for s in target]) + "."
            person_facts.append(fact)

        facts[name] = person_facts

    return facts


#
# Functionality to generate attributes for everyone in the database.
#
def db_generate_attributes(db: Database, args: ArgumentParser, familytrees: list):
    """
    Generate attributes for each person in the database.

    Args:
        db (Database): The database containing the facts.
        args (ArgumentParser): The command line arguments.
    """
    jobs = generate_jobs(familytrees, args.seed)
    shuffle_job_market(familytrees, args)
    names = db.get_names()
    hobbies = generate_hobbies(names, args.seed)

    # add the facts to the database
    facts = []
    for tree in familytrees:
        for person in tree:
            name = person.name
            # add jobs
            for career_event in person.Career_Events:
                if career_event.type == "start_job":
                    job = career_event.job
                    start_date = career_event.date
                    facts.append(f"start_job('{name}', '{job}', '{start_date}')")
                elif career_event.type == "end_job":
                    job = career_event.job
                    end_date = career_event.date
                    facts.append(f"end_job('{name}', '{job}', '{end_date}')")

            # add hobbies
            hobby = hobbies[name]
            facts.append(f"hobby('{name}', '{hobby}')")
            facts.append(f"attribute('{hobby}')")
    db.add(*facts)
