generation(jane, 1).
generation(john, 1).

generation(alice, 2).
generation(bob, 2).
generation(carol, 2).
generation(david, 2).

% female(jane).
% female(alice).
% female(carol).

% male(john).
% male(bob).
% male(david).

single(alice).
single(bob).
single(carol).
single(david).

married(jane, john).


% Alice and Bob are siblings
parent(jane, alice).
parent(john, alice).

parent(jane, bob).
parent(john, bob).

parent(cm, carol).
parent(cf, carol).

parent(dm, david).
parent(df, david).