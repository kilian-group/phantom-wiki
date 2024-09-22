sibling(X, Y) :- parent(_, X), parent(_, Y), X \= Y.
same_generation(X,Y) :- generation(X, _), generation(Y, _).
