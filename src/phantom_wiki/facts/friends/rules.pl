friend(X,Y) :- 
  friend_(X,Y); 
  friend_(Y,X).
