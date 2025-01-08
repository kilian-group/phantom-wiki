# types
PERSON_TYPE = "person"

FAMILY_FACT_TEMPLATES = {
    "brother": "The brother of <subject> is",
    "sister": "The sister of <subject> is",
    "sibling": "<subject>'s sibling is",
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
    "father_in_law": "The father-in-law of <subject> is",
    "mother_in_law": "The mother-in-law of <subject> is",
    "brother_in_law": "The brother-in-law of <subject> is",
    "sister_in_law": "The sister-in-law of <subject> is",
    "son_in_law": "The son-in-law of <subject> is",
    "daughter_in_law": "The daughter-in-law of <subject> is",
}

FAMILY_FACT_TEMPLATES_PL = {
    "brother": "The brothers of <subject> are",
    "sister": "The sisters of <subject> are",
    "sibling": "<subject>'s siblings are",
    "child": "The children of <subject> are",
    "son": "The sons of <subject> are",
    "daughter": "The daughters of <subject> are",
    "uncle": "The uncles of <subject> are",
    "aunt": "The aunts of <subject> are",
    "brother_in_law": "The brother-in-laws of <subject> are",
    "sister_in_law": "The sister-in-laws of <subject> are",
    "son_in_law": "The son-in-laws of <subject> are",
    "daughter_in_law": "The daughter-in-laws of <subject> are",
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
    "father_in_law",
    "mother_in_law",
    "brother_in_law",
    "sister_in_law",
    "son_in_law",
    "daughter_in_law",
]

FAMILY_RELATION_EASY_PLURALS = [
    "siblings",
    "sisters",
    "brothers",
    "children",
    "sons",
    "daughters",
    "brother_in_laws",
    "sister_in_laws",
    "son_in_laws",
    "daughter_in_laws",
]


FAMILY_RELATION_EASY_PL2SG = {
    "siblings": "sibling",
    "sisters": "sister",
    "brothers": "brother",
    "children": "child",
    "sons": "son",
    "daughters": "daughter",
}

FAMILY_RELATION_HARD_PLURALS = [
    "nieces",
    "nephews",
    "greatAunts",
    "greatUncles",
    "grandChildren",
    "grandDaughters",
    "grandSons",
]
