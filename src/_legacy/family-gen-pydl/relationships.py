from person import Person
from pyDatalog import pyDatalog

pyDatalog.create_terms(
    """
    X, Y, Z, married, child
    """
)
# parent, sibling, brother, sister,
#     father, mother, son, daughter, aunt, uncle, niece, nephew, cousin,
#     grandparent, grandfather, grandmother, wife, husband,
#     brother_in_law, sister_in_law, mother_in_law, father_in_law,
#     son_in_law, daughter_in_law

# Person.mother(X, Y) <= parent(X, Y) & (Person.gender[X] == "female")
# Person.father(X, Y) <= parent(X, Y) & (Person.gender[X] == "male")
# Person.age[X] == 18 <= Person.age[X] < 18


Person.aunt(X, Y) <= married(X, Z) & Person.uncle(Z, Y)
Person.aunt(X, Y) <= Person.nephew(Y, X) & (Person.gender[X] == "female")
Person.aunt(X, Y) <= Person.niece(Y, X) & (Person.gender[X] == "female")
Person.aunt(X, Y) <= Person.sibling(X, Z) & Person.parent(Z, Y) & (
    Person.gender[X] == "female"
)
Person.brother(X, Y) <= Person.sibling(X, Y) & (Person.gender[X] == "male")
Person.brother_in_law(X, Z) <= Person.brother(X, Y) & married(Y, Z)
Person.brother_in_law(X, Z) <= Person.husband(X, Y) & Person.sibling(Y, Z)
child(X, Z) <= child(X, Y) & married(Y, Z)
Person.cousin(X, Y) <= Person.cousin(Y, X)
Person.cousin(X, Y) <= Person.parent(Z, X) & Person.aunt(Z, Y)
Person.cousin(X, Y) <= Person.parent(Z, X) & Person.nephew(Y, Z)
Person.cousin(X, Y) <= Person.parent(Z, X) & Person.niece(Y, Z)
Person.cousin(X, Y) <= Person.parent(Z, X) & Person.uncle(Z, Y)
Person.daughter(X, Y) <= (Person.gender[X] == "female") & child(X, Y)
Person.daughter_in_law(X, Z) <= married(X, Y) & Person.son(Y, Z)
Person.father_in_law(X, Z) <= Person.father(X, Y) & married(Y, Z)
Person.grandfather(X, Y) <= Person.grandparent(X, Y) & (Person.gender[X] == "male")
Person.grandmother(X, Y) <= Person.grandparent(X, Y) & (Person.gender[X] == "female")
Person.grandparent(X, Z) <= Person.parent(X, Y) & Person.parent(Y, Z)
Person.mother_in_law(X, Z) <= Person.mother(X, Y) & married(Y, Z)
Person.nephew(X, Y) <= Person.aunt(Y, X) & (Person.gender[X] == "male")
Person.nephew(X, Y) <= Person.uncle(Y, X) & (Person.gender[X] == "male")
Person.niece(X, Y) <= Person.aunt(Y, X) & (Person.gender[X] == "female")
Person.niece(X, Y) <= Person.uncle(Y, X) & (Person.gender[X] == "female")
Person.parent(X, Y) <= Person.parent(X, Z) & Person.sibling(Y, Z)
Person.sibling(X, Y) <= Person.parent(Z, X) & Person.parent(Z, Y) & (X != Y)
Person.sibling(X, Y) <= Person.sibling(Y, X)
Person.sister(X, Y) <= Person.sibling(X, Y) & (Person.gender[X] == "female")
Person.sister_in_law(X, Z) <= Person.sister(X, Y) & married(Y, Z)
Person.sister_in_law(X, Z) <= Person.wife(X, Y) & Person.sibling(Y, Z)
Person.son_in_law(X, Z) <= married(X, Y) & Person.daughter(Y, Z)
Person.uncle(X, Y) <= married(X, Z) & Person.aunt(Z, Y)
Person.uncle(X, Y) <= Person.nephew(Y, X) & (Person.gender[X] == "male")
Person.uncle(X, Y) <= Person.niece(Y, X) & (Person.gender[X] == "male")
Person.uncle(X, Y) <= Person.sibling(X, Z) & Person.parent(Z, Y) & (
    Person.gender[X] == "male"
)


married(X, Y) <= married(Y, X)
Person.parent(X, Z) <= married(X, Y) & Person.parent(Y, Z)
Person.wife(X, Y) <= Person.husband(Y, X)
Person.wife(X, Y) <= (Person.gender[X] == "female") & married(X, Y)
Person.son(X, Y) <= (Person.gender[X] == "male") & child(X, Y)
Person.parent(X, Y) <= child(Y, X)
Person.father(X, Y) <= Person.parent(X, Y) & (Person.gender[X] == "male")
Person.husband(X, Y) <= (Person.gender[X] == "male") & married(X, Y)
Person.mother(X, Y) <= Person.parent(X, Y) & (Person.gender[X] == "female")


jane = Person("Jane", "Doe", None, 40, "female")
john = Person("John", "Doe", None, 40, "male")

jack = Person("Jack", "Doe", None, 10, "male")

# +(Person.age[P] == 18) <= (Person.age[P] < 18)
+married(jane, john)
+child(jack, jane)

print(Person.husband(X, jane))
print()
print(Person.mother(X, jack))
print()
print(Person.father(X, jack))
