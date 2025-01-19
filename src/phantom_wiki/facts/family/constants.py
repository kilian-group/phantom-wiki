PERSON_TYPE = "person"

FAMILY_FACT_TEMPLATES = {
    "brother": "The brother of <subject> is",
    "sister": "The sister of <subject> is",
    "sibling": "<subject>'s sibling is",
    "parent": "The parent of <subject> is",
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
    "parent": "The parents of <subject> are",
    "child": "The children of <subject> are",
    "son": "The sons of <subject> are",
    "daughter": "The daughters of <subject> are",
    "uncle": "The uncles of <subject> are",
    "aunt": "The aunts of <subject> are",
    "brother_in_law": "The brothers-in-law of <subject> are",
    "sister_in_law": "The sisters-in-law of <subject> are",
    "son_in_law": "The sons-in-law of <subject> are",
    "daughter_in_law": "The daughters-in-law of <subject> are",
}

FAMILY_RELATION_PLURAL_ALIAS = {
    "parent": "parents",
    "sibling": "siblings",
    "sister": "sisters",
    "brother": "brothers",
    "mother": "mothers",
    "father": "fathers",
    "child": "children",
    "son": "sons",
    "daughter": "daughters",
    "wife": "wives",
    "husband": "husbands",
    "niece": "nieces",
    "nephew": "nephews",
    "grandparent": "grandparents",
    "grandmother": "grandmothers",
    "grandfather": "grandfathers",
    "great_aunt": "great-aunts",
    "great_uncle": "great-uncles",
    "grandchild": "grandchildren",
    "granddaughter": "granddaughters",
    "grandson": "grandsons",
    "great_grandparent": "great-grandparents",
    "great_grandmother": "great-grandmothers",
    "great_grandfather": "great-grandfathers",
    "great_grandchild": "great-grandchildren",
    "great_granddaughter": "great-granddaughters",
    "great_grandson": "great-grandsons",
    "second_aunt": "second aunts",
    "second_uncle": "second uncles",
    "aunt": "aunts",
    "uncle": "uncles",
    "cousin": "cousins",
    "female_cousin": "female cousins",
    "male_cousin": "male cousins",
    "female_second_cousin": "female second cousins",
    "male_second_cousin": "male second cousins",
    "female_first_cousin_once_removed": "female first cousins once removed",
    "male_first_cousin_once_removed": "male first cousins once removed",
    "father_in_law": "fathers-in-law",
    "mother_in_law": "mothers-in-law",
    "brother_in_law": "brothers-in-law",
    "sister_in_law": "sisters-in-law",
    "son_in_law": "sons-in-law",
    "daughter_in_law": "daughters-in-law",
}

FAMILY_RELATION_ALIAS = {
    "parent": "parent",
    "sibling": "sibling",
    "sister": "sister",
    "brother": "brother",
    "mother": "mother",
    "father": "father",
    "child": "child",
    "son": "son",
    "daughter": "daughter",
    "wife": "wife",
    "husband": "husband",
    "niece": "niece",
    "nephew": "nephew",
    "grandparent": "grandparent",
    "grandmother": "grandmother",
    "grandfather": "grandfather",
    "great_aunt": "great-aunt",
    "great_uncle": "great-uncle",
    "grandchild": "grandchild",
    "granddaughter": "granddaughter",
    "grandson": "grandson",
    "great_grandparent": "great-grandparent",
    "great_grandmother": "great-grandmother",
    "great_grandfather": "great-grandfather",
    "great_grandchild": "great-grandchild",
    "great_granddaughter": "great-granddaughter",
    "great_grandson": "great-grandson",
    "second_aunt": "second aunt",
    "second_uncle": "second uncle",
    "aunt": "aunt",
    "uncle": "uncle",
    "cousin": "cousin",
    "female_cousin": "female cousin",
    "male_cousin": "male cousin",
    "female_second_cousin": "female second cousin",
    "male_second_cousin": "male second cousin",
    "female_first_cousin_once_removed": "female first cousin once removed",
    "male_first_cousin_once_removed": "male first cousin once removed",
    "father_in_law": "father-in-law",
    "mother_in_law": "mother-in-law",
    "brother_in_law": "brother-in-law",
    "sister_in_law": "sister-in-law",
    "son_in_law": "son-in-law",
    "daughter_in_law": "daughter-in-law",
}

FAMILY_RELATION_HARD_PLURALS = [
    "nieces",
    "nephews",
    "grandParents",
    "grandMothers",
    "grandFathers",
    "greatAunts",
    "greatUncles",
    "grandChildren",
    "grandDaughters",
    "grandSons",
    "father_in_laws",
    "mother_in_laws",
    "brother_in_laws",
    "sister_in_laws",
    "son_in_laws",
    "daughter_in_laws",
]

"""Intrinsic difficulty for different family relations.\

For all the predicates that occur in the articles the difficulty is 1.
For harder predicates the difficulty is incremented by the extra articles that need to be checked to determine
the relation.
"""
FAMILY_RELATION_DIFFICULTY = {
    "parent": 1,
    "sibling": 1,
    "sister": 1,
    "brother": 1,
    "mother": 1,
    "father": 1,
    "child": 1,
    "son": 1,
    "daughter": 1,
    "wife": 1,
    "husband": 1,
    "aunt": 2,
    "uncle": 2,
    "niece": 2,
    "nephew": 2,
    "grandparent": 2,
    "grandmother": 2,
    "grandfather": 2,
    "grandchild": 2,
    "granddaughter": 2,
    "grandson": 2,
    "father_in_law": 2,
    "mother_in_law": 2,
    "brother_in_law": 2,
    "sister_in_law": 2,
    "son_in_law": 2,
    "daughter_in_law": 2,
    "great_aunt": 3,
    "great_uncle": 3,
    "great_grandparent": 3,
    "great_grandmother": 3,
    "great_grandfather": 3,
    "great_grandchild": 3,
    "great_granddaughter": 3,
    "great_grandson": 3,
    "cousin": 3,
    "female_cousin": 3,
    "male_cousin": 3,
    "female_first_cousin_once_removed": 4,
    "male_first_cousin_once_removed": 4,
    "second_aunt": 4,
    "second_uncle": 4,
    "female_second_cousin": 5,
    "male_second_cousin": 5,
}
