niece(X, Y) :-
    sibling(Y, A),
    daughter(X, A).

nephew(X, Y) :-
    sibling(Y, A),
    son(X, A).

grandParent(X,Y) :-
  parent(X,Z),
  parent(Z,Y).

grandmother(X, Y) :-
  grandParent(X, Y),
  female(X).

grandFather(X, Y) :-
    grandParent(X, Y),
    male(X).

greatAunt(X, Y) :-
    grandParent(A, Y),
    sister(X, A).

greatUncle(X, Y) :-
    grandParent(A, Y),
    brother(X, A).

grandChild(X,Y) :-
  grandParent(Y,X).

grandDaughter(X, Y) :-
    grandChild(X, Y),
    female(X).

grandSon(X, Y) :-
    grandChild(X, Y),
    male(X).

greatGrandparent(X,Y) :-
  grandParent(X,Z),
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