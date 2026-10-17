"""Generate temporal life events for characters.

Events are generated to be consistent with:
- Birth dates (no events before birth, school after age 5, etc.)
- Family relations (marriage events match married couples)
- Career progression (jobs don't overlap, start after education)
"""

from dataclasses import dataclass
from datetime import date

from numpy.random import default_rng

from ...utils import decode
from ..database import Database
from .constants import CITIES, COMPANIES, SCHOOLS, UNIVERSITIES


@dataclass
class TemporalEvent:
    """A temporal event in a character's life."""

    person_name: str
    event_type: str
    # Fields vary by event type
    details: dict

    def to_prolog(self) -> str:
        if self.event_type == "education":
            return (
                f'education("{self.person_name}", "{self.details["school"]}", '
                f'{self.details["grad_year"]})'
            )
        elif self.event_type == "career":
            return (
                f'career("{self.person_name}", "{self.details["job_title"]}", '
                f'"{self.details["company"]}", {self.details["start_year"]}, '
                f'{self.details["end_year"]})'
            )
        elif self.event_type == "marriage_year":
            return (
                f'marriage_year("{self.person_name}", '
                f'"{self.details["spouse"]}", {self.details["year"]})'
            )
        elif self.event_type == "lived_in":
            return (
                f'lived_in("{self.person_name}", "{self.details["city"]}", '
                f'{self.details["start_year"]}, {self.details["end_year"]})'
            )
        else:
            raise ValueError(f"Unknown event type: {self.event_type}")


def _parse_dob(dob_str: str) -> int:
    """Extract birth year from DOB string like '0259-06-10'."""
    return int(dob_str.split("-")[0])


def generate_temporal_events(
    names: list[str],
    db: Database,
    seed: int = 1,
) -> dict[str, list[TemporalEvent]]:
    """Generate temporal events for all people.

    Args:
        names: List of person names.
        db: Prolog database with existing facts (dob, job, married).
        seed: Random seed.

    Returns:
        Dict mapping person name to list of TemporalEvent.
    """
    rng = default_rng(seed)
    all_events: dict[str, list[TemporalEvent]] = {name: [] for name in names}

    # Gather DOBs
    dobs: dict[str, int] = {}
    for name in names:
        results = list(db.prolog.query(f'dob("{name}", D)'))
        if results:
            dobs[name] = _parse_dob(decode(results[0]["D"]))

    # Gather existing jobs
    jobs: dict[str, str] = {}
    for name in names:
        results = list(db.prolog.query(f'job("{name}", J)'))
        if results:
            jobs[name] = decode(results[0]["J"])

    # Gather married couples
    married_pairs: set[tuple[str, str]] = set()
    for name in names:
        results = list(db.prolog.query(f'married("{name}", S)'))
        for r in results:
            spouse = decode(r["S"])
            pair = tuple(sorted([name, spouse]))
            married_pairs.add(pair)

    # Track marriage years for consistency (both spouses get the same year)
    marriage_years: dict[tuple[str, str], int] = {}
    for pair in married_pairs:
        name1, name2 = pair
        dob1 = dobs.get(name1, 100)
        dob2 = dobs.get(name2, 100)
        # Marriage happens when both are at least 18
        min_marriage_year = max(dob1, dob2) + 18
        max_marriage_year = min_marriage_year + 30
        marriage_year = int(rng.integers(min_marriage_year, max_marriage_year + 1))
        marriage_years[pair] = marriage_year

    for name in names:
        birth_year = dobs.get(name, 100)
        events = []

        # 1. Education: school graduation (age 16-20)
        school = rng.choice(SCHOOLS)
        school_grad_year = birth_year + int(rng.integers(16, 21))
        events.append(
            TemporalEvent(name, "education", {"school": school, "grad_year": school_grad_year})
        )

        # Possibly university (70% chance)
        if rng.random() < 0.7:
            university = rng.choice(UNIVERSITIES)
            uni_grad_year = school_grad_year + int(rng.integers(3, 6))
            events.append(
                TemporalEvent(name, "education", {"school": university, "grad_year": uni_grad_year})
            )
            career_start = uni_grad_year
        else:
            career_start = school_grad_year

        # 2. Career history: 1-3 jobs
        num_jobs = int(rng.integers(1, 4))
        current_year = career_start + int(rng.integers(0, 3))
        current_job = jobs.get(name, "consultant")

        for j in range(num_jobs):
            company = rng.choice(COMPANIES)
            if j < num_jobs - 1:
                # Past job
                duration = int(rng.integers(2, 10))
                end_year = current_year + duration
                job_title = rng.choice(
                    ["intern", "assistant", "associate", "analyst", "coordinator", "specialist"]
                    if j == 0
                    else ["manager", "director", "consultant", "lead", "senior analyst"]
                )
                events.append(
                    TemporalEvent(
                        name,
                        "career",
                        {
                            "job_title": job_title,
                            "company": company,
                            "start_year": current_year,
                            "end_year": end_year,
                        },
                    )
                )
                current_year = end_year
            else:
                # Current job (use the assigned job from attributes)
                # end_year = 9999 signals "current"
                events.append(
                    TemporalEvent(
                        name,
                        "career",
                        {
                            "job_title": current_job,
                            "company": company,
                            "start_year": current_year,
                            "end_year": 9999,
                        },
                    )
                )

        # 3. Marriage year (if married)
        for pair, year in marriage_years.items():
            if name in pair:
                spouse = pair[0] if pair[1] == name else pair[1]
                events.append(
                    TemporalEvent(name, "marriage_year", {"spouse": spouse, "year": year})
                )

        # 4. City moves: 1-4 cities
        num_moves = int(rng.integers(1, 5))
        move_start = birth_year
        used_cities = []
        for m in range(num_moves):
            city = rng.choice([c for c in CITIES if c not in used_cities] or CITIES)
            used_cities.append(city)
            if m < num_moves - 1:
                duration = int(rng.integers(3, 20))
                end_year = move_start + duration
                events.append(
                    TemporalEvent(
                        name,
                        "lived_in",
                        {"city": city, "start_year": move_start, "end_year": end_year},
                    )
                )
                move_start = end_year
            else:
                # Current city (end_year = 9999 signals "current")
                events.append(
                    TemporalEvent(
                        name,
                        "lived_in",
                        {"city": city, "start_year": move_start, "end_year": 9999},
                    )
                )

        all_events[name] = events

    return all_events
