female(X) :-
  gender(X, "female").
male(X) :-
  gender(X, "male").
nonbinary(X) :-
  gender(X, "nonbinary").

sibling(X, Y) :-
  parent(X, A),
  parent(Y, A),
  X \= Y.

married(X, Y) :-
  parent(Child, X),
  parent(Child, Y),
  X \= Y.

sister(X, Y) :-
  sibling(X, Y),
  female(Y).

brother(X, Y) :-
  sibling(X, Y),
  male(Y).

mother(X, Y) :-
  parent(X, Y),
  female(Y).

father(X, Y) :-
  parent(X, Y),
  male(Y).

child(X, Y) :-
  parent(Y, X).

son(X, Y) :-
  child(X, Y),
  male(Y).

daughter(X, Y) :-
  child(X, Y),
  female(Y).

wife(X, Y) :-
  married(X, Y),
  female(Y).

husband(X, Y) :-
  married(X, Y),
  male(Y).
