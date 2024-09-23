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
  \+(sibling(X, Y)),
  X \= Y.

% TODO (potentially): mother, father, parent, child, sibling, cousin, grandparent, grandchild, aunt, uncle, niece, nephew, greatgrandparent, greatgrandchild, greatniece, greatnephew, greataunt, greatuncle, greatcousin, wife, husband
