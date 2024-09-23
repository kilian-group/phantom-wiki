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

mother(X,Y) :- 
  parent(X,Y),
  female(X).

father(X,Y) :-
  parent(X,Y),
  male(X). 

child(X,Y) :- 
  parent(Y,X).

% TODO (potentially): mother, father, parent, child, sibling, cousin, grandparent, grandchild, aunt, uncle, niece, nephew, greatgrandparent, greatgrandchild, greatniece, greatnephew, greataunt, greatuncle, greatcousin, wife, husband
