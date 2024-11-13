FAMILY_FACT_TEMPLATES = {
    "brother": "The brother of <subject> is",
    "sister": "The sister of <subject> is",
    "sibling": "<subject>'s siblings are",
    "father": "The father of <subject> is",
    "mother": "The mother of <subject> is",
    "spouse": "<subject>'s spouse is",
    "child": "The child of <subject> is",
    "son": "The son of <subject> is",
    "daughter": "The daughter of <subject> is",
    "wife": "The wife of <subject> is",
    "husband": "The husband of <subject> is",
    "stepfather": "The stepfather of <subject> is",
    "stepmother": "The stepmother of <subject> is",
    "number of children": "The number of children <subject> has is",
    "uncle": "The uncle of <subject> is",
    "aunt": "The aunt of <subject> is",
}

# Base rules
FAMILY_RELATION_EASY = [
    "sibling",
    "sister",
    "brother",
    "mother",
    "father",
    "child",
    "son",
    "daughter",
    "wife",
    "husband",
]

# Derived rules
FAMILY_RELATION_HARD = [
    "niece",
    "nephew",
    "grandParent",
    "grandMother",
    "grandFather",
    "greatAunt",
    "greatUncle",
    "grandChild",
    "grandDaughter",
    "grandSon",
]
