sibling(X, Y) :- 
  parent(_, X), 
  parent(_, Y),
  X \= Y.

same_generation(X, Y) :- 
  generation(X, _), 
  generation(Y, _).

can_get_married(X, Y) :- 
  same_generation(X, Y), 
  single(X), 
  single(Y), 
  parent(A, X),
  parent(B, Y),
  parent(C, X),
  parent(D, Y),
  A \= B,
  C \= D,
  A \= C,
  B \= D,
  X \= Y. % TODO

% TODO (potentially): mother, father, parent, child, sibling, cousin, grandparent, grandchild, aunt, uncle, niece, nephew, greatgrandparent, greatgrandchild, greatniece, greatnephew, greataunt, greatuncle, greatcousin, wife, husband
