# Question 1 
# Recursive relationship question
S -> "Who is the" R "?" | "What is the" A "?" | "How many" RN "does" N "have?"
R -> RN "of" R | RN "of" N | "whose" AN "is" AV
RN -> <relation>
N -> <name> 

# Question 2 
S -> 
A -> AN "of" R
R -> RN "of" R | RN "of" N 
AN -> "hobby" # e.g.

# Question 3
S -> 
RN -> "siblings" | "children" # (all the relationship from the prolog rules)
N -> "Anastasia" | "Elias" # (all the names from the prolog rules)

# Question 4


