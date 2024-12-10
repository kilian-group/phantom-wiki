import random
import re

create_person_pattern = r"CREATE \((\w+):Person \{name:'([^']*)', born:(\d+)\}\)"
create_movie_pattern = r"CREATE \((\w+):Movie \{title:'(.*?)', released:(\d+), tagline:'(.*?)'\}\)"

create_actor_pattern = r"\((\w+)\)-\[:ACTED_IN \{roles:\[(.*?)\]\}\]->\((\w+)\)"
create_director_pattern = r"\((\w+)\)-\[:DIRECTED\]->\((\w+)\)"
create_producer_pattern = r"\((\w+)\)-\[:PRODUCED\]->\((\w+)\)"
create_writer_pattern = r"\((\w+)\)-\[:WROTE\]->\((\w+)\)"


def match_create_person(text):
    match = re.match(create_person_pattern, text.replace('"', "'"))

    if match:
        return match.group(1), match.group(2), match.group(3)
    return None, None, None


def match_create_movie(text):
    match = re.match(create_movie_pattern, text)

    if match:
        return match.group(1), match.group(2), match.group(3), match.group(4)
    return None, None, None


def match_create_actor(text):
    match = re.match(create_actor_pattern, text)

    if match:
        return match.group(1), match.group(2), match.group(3)
    return None, None, None


def match_create_director(text):
    match = re.match(create_director_pattern, text)

    if match:
        return match.group(1), match.group(2)
    return None, None


def match_create_producer(text):
    match = re.match(create_producer_pattern, text)

    if match:
        return match.group(1), match.group(2)
    return None, None


def match_create_writer(text):
    match = re.match(create_writer_pattern, text)

    if match:
        return match.group(1), match.group(2)
    return None, None


def get_names_from_SQL(path):
    """Gets the names from a movie dataset created by SQL.
    Returns:
        List of people's names that appeared in the dataset.
    """
    with open(path) as f:
        lines = f.readlines()
    hollywood_people = []
    for line in lines:
        if match_create_person(line)[0] is not None:
            hollywood_people.append(match_create_person(line)[0])
    return hollywood_people


def map_residents_to_hollywood(residents, hollywood_people):
    """Sample a subset of residents to be Hollywood people.
    Returns:
        Dictionary mapping residents to Hollywood people.
    """
    if len(hollywood_people) > len(residents):
        raise ValueError("Number of Hollywood people cannot be larger than number of residents.")

    # Randomly sample from residents without replacement
    sampled_elements = random.sample(residents, len(hollywood_people))

    # Create the mapping
    moviestart_to_residents = dict(zip(hollywood_people, sampled_elements))

    return moviestart_to_residents
