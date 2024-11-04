sibling(X, Y) :- 
  parent(A, X), 
  parent(A, Y),
  X \= Y.

married(X, Y) :-
  parent(X, Child),
  parent(Y, Child),
  X \= Y.

sister(X, Y) :-
    sibling(X, Y),
    female(X).

brother(X, Y) :-
    sibling(X, Y),
    male(X).

mother(X,Y) :- 
  parent(X,Y),
  female(X).

father(X,Y) :-
  parent(X,Y),
  male(X). 

child(X,Y) :- 
  parent(Y,X).

son(X,Y) :-
  child(X,Y),
  male(X).

daughter(X,Y) :-
  child(X,Y),
  female(X).

wife(X,Y) :-
  married(X,Y),
  female(X).

husband(X,Y) :- 
  married(X,Y),
  male(X).
