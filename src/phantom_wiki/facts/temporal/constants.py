"""Constants for temporal event generation."""

SCHOOLS = [
    "Westbrook Academy",
    "Oakridge High School",
    "Maplewood Preparatory",
    "Riverside Academy",
    "Hillcrest School",
    "Pinewood Institute",
    "Thornfield Academy",
    "Lakewood High School",
    "Cedar Grove Academy",
    "Birchwood Preparatory",
    "Stonehaven School",
    "Willowdale Academy",
    "Ashford Institute",
    "Briarwood School",
    "Elmwood Academy",
]

UNIVERSITIES = [
    "Northgate University",
    "Silverdale College",
    "Greenfield University",
    "Brimstone College",
    "Ironbridge University",
    "Crestwood College",
    "Havenport University",
    "Foxhollow College",
    "Stonewall University",
    "Clearwater College",
    "Windermere University",
    "Thornbury College",
    "Ashdale University",
    "Millbrook College",
    "Dawnridge University",
]

CITIES = [
    "Millbrook",
    "Oakville",
    "Riverside",
    "Springfield",
    "Fairview",
    "Georgetown",
    "Lakewood",
    "Cedarville",
    "Pinehurst",
    "Brookfield",
    "Maplewood",
    "Stonegate",
    "Ashford",
    "Birchwood",
    "Clearwater",
    "Foxborough",
    "Greenfield",
    "Havenport",
    "Ironbridge",
    "Kingston",
]

COMPANIES = [
    "Meridian Corp",
    "Apex Industries",
    "Horizon Tech",
    "Summit Enterprises",
    "Keystone Solutions",
    "Pinnacle Systems",
    "Atlas Group",
    "Beacon Holdings",
    "Crestline Partners",
    "Drake & Associates",
    "Falcon Dynamics",
    "Grove Capital",
    "Harbor Consulting",
    "Ivy Research",
    "Jasper Technologies",
]

# Event types as Prolog predicates
EVENT_TYPES = [
    "education",      # education(Name, School, GradYear)
    "career",         # career(Name, JobTitle, Company, StartYear, EndYear)
    "marriage_year",  # marriage_year(Name, SpouseName, Year)
    "lived_in",       # lived_in(Name, City, StartYear, EndYear)
]

# Templates for article generation
TEMPORAL_FACT_TEMPLATES = {
    "education": "{name} graduated from {school} in {year}.",
    "career": "{name} worked as a {job} at {company} from {start_year} to {end_year}.",
    "career_current": "{name} has been working as a {job} at {company} since {start_year}.",
    "marriage_year": "{name} married {spouse} in {year}.",
    "lived_in": "{name} lived in {city} from {start_year} to {end_year}.",
    "lived_in_current": "{name} has been living in {city} since {start_year}.",
}
