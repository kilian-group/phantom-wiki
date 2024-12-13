# standard impors
import random

# phantom wiki functionality
from phantom_wiki.facts.database import Database
from phantom_wiki.facts.movies.generate import (
    match_create_actor,
    match_create_director,
    match_create_movie,
    match_create_person,
    match_create_producer,
    match_create_writer,
)

SQL_PATH = "src/phantom_wiki/facts/movies/movies-40.sql"


def db_generate_movies(db: Database, SQL_path: str):
    """
    Generate attributes for each person in the database.

    Args:
        db (Database): The database containing the facts.
        args (ArgumentParser): The command line arguments.

    How to create movie dataset in Prolog
    1. Create a movie:
        movie(Title, Releaseyear).
    2. Create the people involved in the movie
        type:
            - (TomH)-[:ACTED_IN {roles:['Hero Boy', 'Father', 'Conductor', 'Hobo', 'Scrooge', 'Santa Claus']}]->(ThePolarExpress),
                roles can be a list but for simplicity we will use a single role

                acted_in(Title, Actor).

            - (NancyM)-[:DIRECTED]->(SomethingsGottaGive),

                directed(Title, Director).

            - (JoelS)-[:PRODUCED]->(SpeedRacer)

                produced(Title, Producer).

            # optional
            -  (LanaW)-[:WROTE]->(SpeedRacer),

                wrote(Title, Writer).
    """
    names = db.get_names()
    moviestars_to_residents = map_residents_to_hollywood(names, SQL_path)

    # add the facts to the database
    facts = []
    with open(SQL_path) as f:
        lines = f.readlines()
    for line in lines:
        # if matched to a line that created movie cast information, then add to prolog database
        # TODO: add corresponding job for the person in the movie (e.g. actor, director, producer, writer)
        if actor := match_create_actor(line, moviestars_to_residents):
            facts.append(actor)
            continue
        elif director := match_create_director(line, moviestars_to_residents):
            facts.append(director)
            continue
        elif producer := match_create_producer(line, moviestars_to_residents):
            facts.append(producer)
            continue
        elif writer := match_create_writer(line, moviestars_to_residents):
            facts.append(writer)
            continue

        elif movie := match_create_movie(line):
            facts.append(movie)
            continue

    db.add(*facts)


def get_names_from_SQL(SQL_path):
    """Gets the names from a movie dataset created by SQL.
    Returns:
        List of people's names that appeared in the dataset.
    """
    with open(SQL_path) as f:
        lines = f.readlines()
    hollywood_people = []
    for line in lines:
        if match_create_person(line)[0] is not None:
            hollywood_people.append(match_create_person(line)[0])
    return hollywood_people


def map_residents_to_hollywood(residents, SQL_path):
    """Sample a subset of residents to be Hollywood people.
    Returns:
        Dictionary mapping residents to Hollywood people.
    """
    # first get the names of the Hollywood people
    hollywood_people = get_names_from_SQL(SQL_path)

    if len(hollywood_people) > len(residents):
        raise ValueError("Number of Hollywood people cannot be larger than number of residents.")

    # Randomly sample from residents without replacement
    sampled_residents = random.sample(residents, len(hollywood_people))

    # Create the mapping
    moviestars_to_residents = dict(zip(hollywood_people, sampled_residents))

    return moviestars_to_residents
