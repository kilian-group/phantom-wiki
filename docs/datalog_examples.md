# Datalog Examples

## Basic

From https://harvardpl.github.io/AbcDatalog/

```
name(alice).
name(bob).
name(world).
hello(X) :- name(X).
```

Query: `hello(X)?`

Output:

```
hello(alice)
hello(bob)
hello(world)
```

## Family example

```
parent(john, mary).
parent(mary, susan).
ancestor(X, Y) :- parent(X, Y).
ancestor(X, Y) :- parent(X, Z), ancestor(Z, Y).
```

Query: `ancestor(john, susan)?`

Output:

```
ancestor(john, susan)
```
