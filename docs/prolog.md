# Prolog Tutorial

Using the SWI-Prolog CLI:
https://www.swi-prolog.org/pldoc/man?section=quickstart

SWI-Prolog syntax: https://www.swi-prolog.org/pldoc/man?section=syntax
- According to the ISO standard and most Prolog systems, identifiers that start with an uppercase letter or an underscore are variables.

## Basic concepts

https://en.wikipedia.org/wiki/Prolog#Syntax_and_semantics

As a convention, let's use predicates to represent "of" relationships.
```
predicate(X,Y) -> the <predicate> of X is Y
```
For example:
```
parent(X,Y) -> the parent of X is Y
child(X,Y) -> the child of X is Y
hobby(X,Y) -> the hobby of X is Y
count(X,Y) -> the count of X is Y
```

Atoms must start with a lower case. Atoms can contain spaces by wrapping them in quotes. Note that single quotes and double quotes mean different things in SWI-Prolog, so `female('kamala harris').` and `female("kamala harris").` correspond to different atoms!

**Does the order of rules matter?**
Short answer is yes. (See https://lpn.swi-prolog.org/lpnpage.php?pagetype=html&pageid=lpn-htmlse10)

## Built-in SWI-Prolog predicates

**Query:** Gets all results
```
janus.query("parent(alice,X)") -> gets the parent of alice
```

**Dynamic predicates:**
1. `asserta/1`: adds clause to the top of the list of clauses
2. `assertz/1`: adds clause to the bottom of the list of clauses
3. `retract/1`: deletes a clause from the list of clauses

The order matters, for example, when using `query_once`.

**Aggregation:**

1. `aggregate_all`: 

## Naming conventions

1. Entities: usually represent specific people, locations, organizations, and miscellaneous items like movies, awards, etc.
  - Examples: `'ChristopherNolan'`, `'Dunkirk'`, `'BestDirector'`
2. Predicates: represent relationships between entities, literals or types
  - Examples: `director`, `dateOfBirth`, `type`
3. Types: represent the categories that these entities belong to
  - Examples: `Person`, `Film`, `AcademyAward`
  - NOTE: `type` is a special predicate that connects an entity to its category
4. Literals: represent constants like dates, population counts, quotations, and other strings and numbers 
  - Examples: `'30July1970'`, `'30Million'`, `'148Minutes'`

Reference: https://link.springer.com/book/10.1007/978-3-031-79512-1

As a convention, let's wrap entities and literals in single quotes, but types should be normal strings. For example,
```
type('running', hobby).
type('alfonso', person).
```