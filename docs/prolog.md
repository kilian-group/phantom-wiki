# Prolog Tutorial

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

# Built-in SWI-Prolog predicates

**aggregate_all**