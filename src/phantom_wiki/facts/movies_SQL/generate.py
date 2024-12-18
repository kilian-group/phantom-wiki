# standard imports
import re

create_person_pattern = r"CREATE \((\w+):Person \{name:'([^']*)', born:(\d+)\}\)"


def match_create_person(text):
    match = re.match(create_person_pattern, text.replace('"', "'"))

    if match:
        return match.group(1), match.group(2), match.group(3)
    return None, None, None


create_movie_pattern = r"CREATE \((\w+):Movie \{title:'(.*?)', released:(\d+), tagline:'(.*?)'\}\)"


def match_create_movie(text):
    match = re.match(create_movie_pattern, text)

    if match:
        movie_name = match.group(1)
        release_year = match.group(3)
        prolog_str = f"movie('{movie_name}', {release_year})."
        return prolog_str
    return None


create_actor_pattern = r"\((\w+)\)-\[:ACTED_IN \{roles:\[(.*?)\]\}\]->\((\w+)\)"


def match_create_actor(text, mapping: dict):
    match = re.match(create_actor_pattern, text)

    if match:
        actor = match.group(1)
        movie_name = match.group(3)
        resident = mapping[actor]
        prolog_str = f"acted_in('{movie_name}', '{resident}')."
        return prolog_str
    return None


create_director_pattern = r"\((\w+)\)-\[:DIRECTED\]->\((\w+)\)"


def match_create_director(text, mapping: dict):
    match = re.match(create_director_pattern, text)

    if match:
        director = match.group(1)
        movie_name = match.group(2)
        resident = mapping[director]
        prolog_str = f"directed('{movie_name}', '{resident}')."
        return prolog_str
    return None


create_producer_pattern = r"\((\w+)\)-\[:PRODUCED\]->\((\w+)\)"


def match_create_producer(text, mapping: dict):
    match = re.match(create_producer_pattern, text)

    if match:
        producer = match.group(1)
        movie_name = match.group(2)
        resident = mapping[producer]
        prolog_str = f"produced('{movie_name}', '{resident}')."
        return prolog_str
    return None


create_writer_pattern = r"\((\w+)\)-\[:WROTE\]->\((\w+)\)"


def match_create_writer(text, mapping: dict):
    match = re.match(create_writer_pattern, text)

    if match:
        writer = match.group(1)
        movie_name = match.group(2)
        resident = mapping[writer]
        prolog_str = f"wrote('{movie_name}', '{resident}')."
        return prolog_str
    return None
