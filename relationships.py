from person import Person
from pyDatalog import pyDatalog

pyDatalog.create_terms("Person, parent, X, Y")


Person.mother(X, Y) <= parent(X, Y) & (Person.gender[X] == "female")
Person.father(X, Y) <= parent(X, Y) & (Person.gender[X] == "male")


jane = Person("Jane", "Doe", None, 40, "female")
john = Person("John", "Doe", None, 40, "male")

jack = Person("Jack", "Doe", None, 10, "male")

+parent(jane, jack)
+parent(john, jack)


print(Person.mother(X, jack))
print(Person.father(X, jack))
