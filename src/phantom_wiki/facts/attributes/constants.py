ATTRIBUTE_FACT_TEMPLATES = {
    "dob": "The date of birth of <subject> is",
    "job": "The occupation of <subject> is",
    "hobby": "The hobby of <subject> is",
    "gender": "The gender of <subject> is",
}

ATTRIBUTE_RELATION = [
    "dob",
    "job",
    "hobby",
    "gender",
]


# Source: https://www.kaggle.com/datasets/mrhell/list-of-hobbies?resource=download
# License: CC0: Public Domain
# preprocessing code
"""
import pandas as pd
hobbies = pd.read_csv("hobbylist.csv")
# make the Hobby-name column lowercase
hobbies["Hobby-name"] = hobbies["Hobby-name"].str.lower()
# aggregate by Type
hobbies = hobbies.groupby("Type")["Hobby-name"].apply(list).to_dict()
# save as json
import json
with open("hobbies.json", "w") as f:
    json.dump(hobbies, f, indent=4)
"""
# NOTE: some hobbies are modified to remove special characters, 
# words in parentheses, and 'X or Y' patterns that were in the original dataset
HOBBIES = {
    "Educational hobby": [
        "archaeology",
        "architecture",
        "astronomy",
        "animation",
        "aerospace",
        "biology",
        "botany",
        "business",
        "chemistry",
        "entrepreneurship",
        "finance",
        "geography",
        "history",
        "linguistics",
        "literature",
        "mathematics",
        "medical science",
        "microbiology",
        "mycology",
        "myrmecology",
        "neuroscience",
        "philosophy",
        "physics",
        "psychology",
        "railway studies",
        "religious studies",
        "research",
        "science and technology studies",
        "social studies",
        "sociology",
        "sports science",
        "story writing",
        "life science",
        "teaching",
        "web design",
        "engineering",
        "jurisprudential",
        "publishing",
        "wikipedia editing"
    ],
    "Indoor Collection hobby": [
        "action figure",
        "antiquing",
        "ant-keeping",
        "art collecting",
        "book collecting",
        "button collecting",
        "cartophily",
        "coin collecting",
        "comic book collecting",
        "compact discs",
        "crystals",
        "deltiology",
        "die-cast toy",
        "digital hoarding",
        "dolls",
        "element collecting",
        "ephemera collecting",
        "films",
        "fingerprint collecting",
        "fusilately",
        "knife collecting",
        "lapel pins",
        "lotology",
        "movie memorabilia collecting",
        "notaphily",
        "perfume",
        "philately",
        "phillumeny",
        "radio-controlled model collecting",
        "rail transport modelling",
        "record collecting",
        "rock tumbling",
        "scutelliphily",
        "shoes",
        "slot car",
        "sports memorabilia",
        "stamp collecting",
        "stuffed toy collecting",
        "tea bag collecting",
        "ticket collecting",
        "transit map collecting",
        "video game collecting",
        "vintage cars",
        "vintage clothing",
        "vinyl records"
    ],
    "Indoor Competitive hobby": [
        "air hockey",
        "animal fancy",
        "axe throwing",
        "backgammon",
        "badminton",
        "baking",
        "ballet dancing",
        "ballroom dancing",
        "baton twirling",
        "beauty pageants",
        "billiards",
        "book folding",
        "bowling",
        "boxing",
        "bridge",
        "cooking",
        "checkers (draughts)",
        "cheerleading",
        "chess",
        "color guard",
        "cribbage",
        "curling",
        "dancing",
        "darts",
        "debate",
        "dominoes",
        "eating",
        "esports",
        "fencing",
        "figure skating",
        "go",
        "gymnastics",
        "ice hockey",
        "ice skating",
        "judo",
        "jujitsu",
        "kabaddi",
        "knowledge/word games",
        "laser tag",
        "magic",
        "mahjong",
        "marbles",
        "martial arts",
        "model racing",
        "model united nations",
        "pinball",
        "poker",
        "pole dancing",
        "pool",
        "radio-controlled model playing",
        "role-playing games",
        "rughooking",
        "shogi",
        "slot car racing",
        "speedcubing",
        "sport stacking",
        "table football",
        "table tennis",
        "volleyball",
        "video gaming",
        "vr gaming",
        "weightlifting",
        "wrestling"
    ],
    "Indoor Observation hobby": [
        "audiophile",
        "ant farming",
        "fishkeeping",
        "learning",
        "meditation",
        "microscopy",
        "reading",
        "research",
        "shortwave listening"
    ],
    "Outdoor Collection hobby": [
        "antiquities",
        "auto audiophilia",
        "flower collecting and pressing",
        "fossil hunting",
        "insect collecting",
        "leaves",
        "magnet fishing",
        "metal detecting",
        "mineral collecting",
        "rock balancing",
        "sea glass collecting",
        "seashell collecting",
        "stone collecting"
    ],
    "Outdoor Competitive hobby": [
        "airsoft",
        "archery",
        "association football",
        "australian rules football",
        "auto racing",
        "baseball",
        "beach volleyball",
        "breakdancing",
        "capoeira",
        "climbing",
        "cornhole",
        "cricket",
        "croquet",
        "cycling",
        "disc golf",
        "dog sport",
        "equestrianism",
        "exhibition drill",
        "field hockey",
        "figure skating",
        "fishing",
        "fitness",
        "footbag",
        "frisbee",
        "rugby league football",
        "rowing",
        "shooting sports",
        "skateboarding",
        "skiing",
        "sled dog racing",
        "softball",
        "speed skating",
        "squash",
        "surfing",
        "swimming",
        "table tennis",
        "tennis",
        "tennis polo",
        "tether car",
        "tour skating",
        "tourism",
        "trapshooting",
        "triathlon",
        "ultimate frisbee",
        "volleyball",
        "water polo",
        "golfing",
        "handball",
        "horseback riding",
        "horsemanship",
        "horseshoes",
        "iceboat racing",
        "jukskei",
        "kart racing",
        "knife throwing",
        "lacrosse",
        "longboarding",
        "long-distance running",
        "marching band",
        "mini golf",
        "model aircraft",
        "orienteering",
        "pickleball",
        "powerboat racing",
        "quidditch",
        "race walking",
        "racquetball",
        "radio-controlled car racing",
        "radio-controlled model playing",
        "roller derby"
    ],
    "Outdoor Observation hobby": [
        "aircraft spotting",
        "amateur astronomy",
        "beekeeping",
        "benchmarking",
        "birdwatching",
        "bus spotting",
        "people-watching",
        "photography",
        "satellite watching",
        "trainspotting",
        "whale watching",
        "butterfly watching",
        "geocaching",
        "gongoozling",
        "herping",
        "hiking/backpacking",
        "meteorology"
    ],
    "Outdoors and sports": [
        "air sports",
        "airsoft",
        "amateur geology",
        "amusement park visiting",
        "archery",
        "auto detailing",
        "automobilism",
        "astronomy",
        "backpacking",
        "badminton",
        "base jumping",
        "baseball",
        "basketball",
        "beachcombing",
        "beekeeping",
        "birdwatching",
        "blacksmithing",
        "bmx",
        "board sports",
        "bodybuilding",
        "bus riding",
        "camping",
        "canoeing",
        "canyoning",
        "carrier pigeons",
        "car riding",
        "car tuning",
        "caving",
        "city trip",
        "climbing",
        "composting",
        "croquet",
        "cycling",
        "dairy farming",
        "dandyism",
        "darts",
        "dodgeball",
        "dog training",
        "dog walking",
        "dowsing",
        "driving",
        "farming",
        "fishing",
        "flag football",
        "flower growing",
        "flying",
        "flying disc",
        "flying model planes",
        "foraging",
        "fossicking",
        "freestyle football",
        "fruit picking",
        "gardening",
        "geocaching",
        "ghost hunting",
        "gold prospecting",
        "graffiti",
        "groundhopping",
        "guerrilla gardening",
        "gymnastics",
        "handball",
        "herbalism",
        "herping",
        "high-power rocketry",
        "hiking",
        "hobby horsing",
        "hobby tunneling",
        "hooping",
        "horseback riding",
        "hunting",
        "inline skating",
        "jogging",
        "jumping rope",
        "karting",
        "kayaking",
        "kite flying",
        "kitesurfing",
        "lacrosse",
        "larping",
        "letterboxing",
        "lomography",
        "longboarding",
        "martial arts",
        "magnet fishing",
        "metal detecting",
        "motorcycling",
        "meteorology",
        "motor sports",
        "mountain biking",
        "mountaineering",
        "museum visiting",
        "mushroom hunting/mycology",
        "netball",
        "noodling",
        "nordic skating",
        "orienteering",
        "paintball",
        "paragliding",
        "parkour",
        "photography",
        "pickleball",
        "picnicking",
        "podcast hosting",
        "polo",
        "powerlifting",
        "public transport riding",
        "qigong",
        "radio-controlled model playing",
        "rafting",
        "railway journeys",
        "railway modelling",
        "rappelling",
        "renaissance fair",
        "renovating",
        "road biking",
        "rock climbing",
        "rock painting",
        "roller skating",
        "roundnet",
        "rugby",
        "running",
        "safari",
        "sailing",
        "sand art",
        "scouting",
        "scuba diving",
        "rowing",
        "shooting",
        "shopping",
        "shuffleboard",
        "skateboarding",
        "skiing",
        "skimboarding",
        "skydiving",
        "slacklining",
        "sledding",
        "snorkeling",
        "snowboarding",
        "snowmobiling",
        "snowshoeing",
        "soccer",
        "stone skipping",
        "storm chasing",
        "sun bathing",
        "surfing",
        "survivalism",
        "swimming",
        "table tennis playing",
        "taekwondo",
        "tai chi",
        "tennis",
        "thru-hiking",
        "topiary",
        "tourism",
        "trade fair visiting",
        "travel",
        "unicycling",
        "urban exploration",
        "vacation",
        "vegetable farming",
        "vehicle restoration",
        "videography",
        "volleyball",
        "volunteering",
        "walking",
        "water sports",
        "zoo visiting"
    ]
}