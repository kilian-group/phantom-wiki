niece(X, Y) :-
    sibling(X, A),
    daughter(A, Y).

nephew(X, Y) :-
    sibling(X, A),
    son(A, Y).

grandparent(X, Y) :-
    parent(X, Z),
    parent(Z, Y).

grandmother(X, Y) :-
    grandparent(X, Y),
    female(Y).

grandfather(X, Y) :-
    grandparent(X, Y),
    male(Y).

great_aunt(X, Y) :-
    grandparent(X, A),
    sister(A, Y).

great_uncle(X, Y) :-
    grandparent(X, A),
    brother(A, Y).

grandchild(X, Y) :-
  grandparent(Y, X).

granddaughter(X, Y) :-
    grandchild(X, Y),
    female(Y).

grandson(X, Y) :-
    grandchild(X, Y),
    male(Y).

great_grandparent(X, Y) :-
  grandparent(X, Z),
  parent(Z, Y).

great_grandmother(X, Y) :-
    great_grandparent(X, Y),
    female(Y).

great_grandfather(X, Y) :-
    great_grandparent(X, Y),
    male(Y).

great_grandchild(X, Y) :-
  great_grandparent(Y, X).

great_granddaughter(X, Y) :-
    great_grandchild(X, Y),
    female(Y).

great_grandson(X, Y) :-
    great_grandchild(X, Y),
    male(Y).

second_aunt(X, Y) :-
    great_grandparent(X, A),
    sister(A, Y).

second_uncle(X, Y) :-
    great_grandparent(X, A),
    brother(A, Y).

aunt(X, Y) :-
    parent(X, A),
    sister(A, Y).

uncle(X, Y) :-
    parent(X, A),
    brother(A, Y).

cousin(X, Y) :-
    parent(X, A),
    parent(Y, B),
    sibling(A, B),
    X \= Y.

female_cousin(X, Y) :-
    cousin(X, Y),
    female(Y).

male_cousin(X, Y) :-
    cousin(X, Y),
    male(Y).

female_second_cousin(X, Y) :-
    parent(X, A),
    parent(Y, B),
    cousin(A, B),
    female(Y),
    X \= Y.

male_second_cousin(X, Y) :-
    parent(X, A),
    parent(Y, B),
    cousin(A, B),
    male(Y),
    X \= Y.

female_first_cousin_once_removed(X, Y) :-
    cousin(X, A),
    daughter(A, Y),
    X \= Y.

male_first_cousin_once_removed(X, Y) :-
    cousin(X, A),
    son(A, Y),
    X \= Y.

mother_in_law(X, Y) :-
    married(X, A),
    mother(A, Y).

father_in_law(X, Y) :-
    married(X, A),
    father(A, Y).

son_in_law(X, Y) :-
    child(X, A),
    husband(A, Y).

daughter_in_law(X, Y) :-
    child(X, A),
    wife(A, Y).

sister_in_law(X, Y) :-
    married(X, A),
    sister(A, Y).

brother_in_law(X, Y) :-
    married(X, A),
    brother(A, Y).
