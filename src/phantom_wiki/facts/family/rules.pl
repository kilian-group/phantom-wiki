sibling(X, Y) :-
  parent(A, X),
  parent(A, Y),
  X \= Y.

same_generation(X, Y) :-
  generation(X, A),
  generation(Y, A).

can_get_married(X,Y) :-
  same_generation(X, Y),
  single(X),
  single(Y),
  male(X),
  female(Y),
  \+(sibling(X, Y)),
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

niece(X, Y) :-
    sibling(Y, A),
    daughter(X, A).

nephew(X, Y) :-
    sibling(Y, A),
    son(X, A).

grandparent(X,Y) :-
  parent(X,Z),
  parent(Z,Y).

grandmother(X, Y) :-
  grandparent(X, Y),
  female(X).

grandfather(X, Y) :-
    grandparent(X, Y),
    male(X).

greatAunt(X, Y) :-
    grandparent(A, Y),
    sister(X, A).

greatUncle(X, Y) :-
    grandParent(A, Y),
    brother(X, A).

grandchild(X,Y) :-
  grandparent(Y,X).

granddaughter(X, Y) :-
    grandchild(X, Y),
    female(X).

grandson(X, Y) :-
    grandchild(X, Y),
    male(X).

wife(X,Y) :-
  married(X,Y),
  female(X).

husband(X,Y) :-
  married(X,Y),
  male(X).

greatGrandparent(X,Y) :-
  grandparent(X,Z),
  parent(Z,Y).

greatGrandmother(X, Y) :-
    greatGrandparent(X, Y),
    female(X).

greatGrandfather(X, Y) :-
    greatGrandparent(X, Y),
    male(X).

greatGrandchild(X,Y) :-
  greatGrandparent(Y,X).

greatGranddaughter(X, Y) :-
    greatGrandchild(X, Y),
    female(X).

greatGrandson(X, Y) :-
    greatGrandchild(X, Y),
    male(X).

secondAunt(X, Y) :-
    greatGrandparent(A, Y),
    sister(X, A).

secondUncle(X, Y) :-
    greatGrandparent(A, Y),
    brother(X, A).

aunt(X, Y) :-
    parent(A, Y),
    sister(X, A).

uncle(X, Y) :-
    parent(A, Y),
    brother(X, A).

cousin(X,Y) :-
  parent(A, X),
  parent(B, Y),
  sibling(A, B),
  X \= Y.

girlCousin(X, Y) :-
    cousin(X, Y),
    female(X).

boyCousin(X, Y) :-
    cousin(X, Y),
    male(X).

girlSecondCousin(X, Y) :-
    parent(A, X),
    parent(B, Y),
    cousin(A, B),
    female(X).

boySecondCousin(X, Y) :-
    parent(A, X),
    parent(B, Y),
    cousin(A, B),
    male(X).

girlFirstCousinOnceRemoved(X, Y) :-
    cousin(A, Y),
    daughter(X, A).

boyFirstCousinOnceRemoved(X, Y) :-
    cousin(A, Y),
    son(X, A).
