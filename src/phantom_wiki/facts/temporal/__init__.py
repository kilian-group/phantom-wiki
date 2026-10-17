import logging
import time
from importlib.resources import files

from ..database import Database
from .generate_events import generate_temporal_events

TEMPORAL_RULES_PATH = files("phantom_wiki").joinpath("facts/temporal/rules.pl")


def db_generate_temporal_events(db: Database, seed: int) -> None:
    """Generate temporal life events for each person in the database.

    Events include: education, career history, marriage year, and city moves.
    All events are consistent with birth dates and family relations.

    Args:
        db: The database containing the facts.
        seed: Global seed for random number generator.
    """
    start_time = time.time()
    names = db.get_person_names()
    events = generate_temporal_events(names, db, seed)

    facts = []
    for name, event_list in events.items():
        for event in event_list:
            facts.append(event.to_prolog())

    logging.info(f"Generated temporal events for {len(names)} individuals in {time.time()-start_time:.3f}s.")
    db.add(*facts)
    db.consult(str(TEMPORAL_RULES_PATH))
