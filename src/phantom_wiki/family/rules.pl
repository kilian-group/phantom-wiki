sibling(X, Y) :- 
  parent(A, X), 
  parent(A, Y),
  X \= Y.

same_generation(X, Y) :- 
  generation(X, A), 
  generation(Y, A).

single(X) :- 
  \+(married(X, A)).

can_get_married(X,Y) :-
  same_generation(X, Y),
  single(X),
  single(Y),
  male(X),
  female(Y),
  \+(sibling(X, Y)),
  X \= Y.

married(X,Y) :-
  married(Y,X).

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

grandparent(X,Y) :-
  parent(X,Z),
  parent(Z,Y).

grandchild(X,Y) :-
  grandparent(Y,X).

wife(X,Y) :-
  married(X,Y),
  female(X).

husband(X,Y) :- 
  married(X,Y),
  male(X).

greatgrandparent(X,Y) :-
  grandparent(X,Z),
  parent(Z,Y).

greatgrandchild(X,Y) :-
  greatgrandparent(Y,X).

cousin(X,Y) :-
  parent(A, X),
  parent(B, Y),
  sibling(A, B),
  X \= Y.

% TODO (potentially): cousin, aunt, uncle, niece, nephew, greatniece, greatnephew, greataunt, greatuncle, greatcousin
