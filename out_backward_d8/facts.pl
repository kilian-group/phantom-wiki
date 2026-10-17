
sister_in_law(X, Y) :-
    married(X, A),
    sister(A, Y).

wife(X, Y) :-
    married(X, Y),
    female(Y).

:- multifile prolog_predicate_name/2.


male(X) :-
    gender(X, "male").

:- dynamic prolog_load_file/2.
:- multifile prolog_load_file/2.


husband(X, Y) :-
    married(X, Y),
    male(Y).

daughter_in_law(X, Y) :-
    child(X, A),
    wife(A, Y).

nonbinary(X) :-
    gender(X, "nonbinary").

son_in_law(X, Y) :-
    child(X, A),
    husband(A, Y).

son(X, Y) :-
    child(X, Y),
    male(Y).

:- multifile prolog_list_goal/1.


female(X) :-
    gender(X, "female").

:- dynamic portray/1.
:- multifile portray/1.


daughter(X, Y) :-
    child(X, Y),
    female(Y).

father_in_law(X, Y) :-
    married(X, A),
    father(A, Y).

:- dynamic expand_answer/2.
:- multifile expand_answer/2.


mother_in_law(X, Y) :-
    married(X, A),
    mother(A, Y).

father(X, Y) :-
    parent(X, Y),
    male(Y).

child(X, Y) :-
    parent(Y, X).

male_first_cousin_once_removed(X, Y) :-
    cousin(X, A),
    son(A, Y),
    X\=Y.

female_first_cousin_once_removed(X, Y) :-
    cousin(X, A),
    daughter(A, Y),
    X\=Y.

brother(X, Y) :-
    sibling(X, Y),
    male(Y).

mother(X, Y) :-
    parent(X, Y),
    female(Y).

male_second_cousin(X, Y) :-
    parent(X, A),
    parent(Y, B),
    cousin(A, B),
    male(Y),
    X\=Y.

female_second_cousin(X, Y) :-
    parent(X, A),
    parent(Y, B),
    cousin(A, B),
    female(Y),
    X\=Y.

married(X, Y) :-
    parent(Child, X),
    parent(Child, Y),
    X\=Y.

:- dynamic exception/3.
:- multifile exception/3.


:- dynamic resource/2.
:- multifile resource/2.


:- dynamic term_expansion/2.
:- multifile term_expansion/2.


sister(X, Y) :-
    sibling(X, Y),
    female(Y).

male_cousin(X, Y) :-
    cousin(X, Y),
    male(Y).

female_cousin(X, Y) :-
    cousin(X, Y),
    female(Y).

sibling(X, Y) :-
    parent(X, A),
    parent(Y, A),
    X\=Y.

:- dynamic goal_expansion/4.
:- multifile goal_expansion/4.


:- dynamic parent/2.

parent("Aida Wang", "Dino Beltran").
parent("Aida Wang", "Shelli Beltran").
parent("Aubrey Smock", "Alvaro Smock").
parent("Aubrey Smock", "Lannie Smock").
parent("Deane Smock", "Alvaro Smock").
parent("Deane Smock", "Lannie Smock").
parent("Dino Beltran", "Brian Beltran").
parent("Dino Beltran", "Daisy Beltran").
parent("Gene Smock", "Alvaro Smock").
parent("Gene Smock", "Lannie Smock").
parent("Isabell Smock", "Alvaro Smock").
parent("Isabell Smock", "Lannie Smock").
parent("Jeannine Wexler", "Dino Beltran").
parent("Jeannine Wexler", "Shelli Beltran").
parent("Johnetta Wang", "Aida Wang").
parent("Johnetta Wang", "Ryan Wang").
parent("Leeann Hackworth", "Ricardo Hackworth").
parent("Leeann Hackworth", "Vicki Hackworth").
parent("Lenore Hackworth", "Ricardo Hackworth").
parent("Lenore Hackworth", "Vicki Hackworth").
parent("Myrle Smock", "Alison Smock").
parent("Myrle Smock", "Williams Smock").
parent("Orlando Beltran", "Brian Beltran").
parent("Orlando Beltran", "Daisy Beltran").
parent("Shelli Beltran", "Alison Smock").
parent("Shelli Beltran", "Williams Smock").
parent("Valentina Wexler", "Jeannine Wexler").
parent("Valentina Wexler", "Saul Wexler").
parent("Vicki Hackworth", "Dino Beltran").
parent("Vicki Hackworth", "Shelli Beltran").
parent("Williams Smock", "Dominique Smock").
parent("Williams Smock", "Gene Smock").
parent("Alberto Saari", "Shawnta Saari").
parent("Alberto Saari", "Trevor Saari").
parent("Alycia Cormier", "Bert Deluna").
parent("Alycia Cormier", "Geri Deluna").
parent("Christoper Cormier", "Patsy Cormier").
parent("Christoper Cormier", "Sol Cormier").
parent("Clifford Cormier", "Dion Cormier").
parent("Clifford Cormier", "Ming Cormier").
parent("Dion Cormier", "Foster Cormier").
parent("Dion Cormier", "Leda Cormier").
parent("Earle Cormier", "Foster Cormier").
parent("Earle Cormier", "Leda Cormier").
parent("Ella Saari", "Shawnta Saari").
parent("Ella Saari", "Trevor Saari").
parent("Foster Cormier", "Alycia Cormier").
parent("Foster Cormier", "Christoper Cormier").
parent("Leann Cormier", "Clifford Cormier").
parent("Leann Cormier", "Deborah Cormier").
parent("Ming Cormier", "Andy Clemons").
parent("Ming Cormier", "Jeana Clemons").
parent("Shawnta Saari", "Dion Cormier").
parent("Shawnta Saari", "Ming Cormier").
parent("Sherry Cormier", "Foster Cormier").
parent("Sherry Cormier", "Leda Cormier").
parent("Therese Cormier", "Earle Cormier").
parent("Therese Cormier", "Julia Cormier").
parent("Trevor Saari", "Hunter Saari").
parent("Trevor Saari", "Virgie Saari").
parent("Amberly Mcnew", "Haywood Mcnew").
parent("Amberly Mcnew", "Rae Mcnew").
parent("Cole Mcnew", "Don Mcnew").
parent("Cole Mcnew", "Lorelei Mcnew").
parent("Ernesto Mcnew", "Cole Mcnew").
parent("Ernesto Mcnew", "Roxy Mcnew").
parent("Garry Mcnew", "Cole Mcnew").
parent("Garry Mcnew", "Roxy Mcnew").
parent("Goldie Henderson", "Noelia Henderson").
parent("Goldie Henderson", "Stefan Henderson").
parent("Hayden Mcnew", "Cole Mcnew").
parent("Hayden Mcnew", "Roxy Mcnew").
parent("Haywood Mcnew", "Amanda Mcnew").
parent("Haywood Mcnew", "Merrill Mcnew").
parent("Jeanelle Mcnew", "Don Mcnew").
parent("Jeanelle Mcnew", "Lorelei Mcnew").
parent("Lorelei Mcnew", "Noelia Henderson").
parent("Lorelei Mcnew", "Stefan Henderson").
parent("Marcelino Mcnew", "Don Mcnew").
parent("Marcelino Mcnew", "Lorelei Mcnew").
parent("Maxwell Henderson", "Jung Henderson").
parent("Maxwell Henderson", "Marko Henderson").
parent("Merrill Mcnew", "Don Mcnew").
parent("Merrill Mcnew", "Lorelei Mcnew").
parent("Milton Henderson", "Jung Henderson").
parent("Milton Henderson", "Marko Henderson").
parent("Noelia Henderson", "Caleb Haber").
parent("Noelia Henderson", "Kris Haber").
parent("Rae Mcnew", "Dudley Wise").
parent("Rae Mcnew", "Jacinta Wise").
parent("Stefan Henderson", "Jung Henderson").
parent("Stefan Henderson", "Marko Henderson").
parent("Aletha Nicolas", "Cherry Nicolas").
parent("Aletha Nicolas", "Ulysses Nicolas").
parent("Anthony Nicolas", "Cherry Nicolas").
parent("Anthony Nicolas", "Ulysses Nicolas").
parent("Bradford Nicolas", "Cherry Nicolas").
parent("Bradford Nicolas", "Ulysses Nicolas").
parent("Carrol Nicolas", "Bradford Nicolas").
parent("Carrol Nicolas", "Phylis Nicolas").
parent("Connie Nicolas", "Anthony Nicolas").
parent("Connie Nicolas", "Edythe Nicolas").
parent("Dwayne Langley", "Barney Langley").
parent("Dwayne Langley", "Sha Langley").
parent("Edythe Nicolas", "Theodore Crain").
parent("Edythe Nicolas", "Yoshiko Crain").
parent("Eldon Nicolas", "Anthony Nicolas").
parent("Eldon Nicolas", "Edythe Nicolas").
parent("Errol Brook", "Lera Brook").
parent("Errol Brook", "Rufus Brook").
parent("Lera Brook", "Anthony Nicolas").
parent("Lera Brook", "Edythe Nicolas").
parent("Lucas Crain", "Theodore Crain").
parent("Lucas Crain", "Yoshiko Crain").
parent("Marilyn Nicolas", "Anthony Nicolas").
parent("Marilyn Nicolas", "Edythe Nicolas").
parent("Rosalinda Francois", "Cherry Nicolas").
parent("Rosalinda Francois", "Ulysses Nicolas").
parent("Rubye Crain", "Eula Crain").
parent("Rubye Crain", "Lucas Crain").
parent("Sha Langley", "Preston Francois").
parent("Sha Langley", "Rosalinda Francois").
parent("Thurman Crain", "Theodore Crain").
parent("Thurman Crain", "Yoshiko Crain").
parent("Zulema Crain", "Theodore Crain").
parent("Zulema Crain", "Yoshiko Crain").
parent("Chuck Lizotte", "Dwain Lizotte").
parent("Chuck Lizotte", "Rosina Lizotte").
parent("Dwain Lizotte", "Odis Lizotte").
parent("Dwain Lizotte", "Ora Lizotte").
parent("Hanh Mohan", "Dwain Lizotte").
parent("Hanh Mohan", "Rosina Lizotte").
parent("Hoa Skaggs", "Jeannine Skaggs").
parent("Hoa Skaggs", "Weldon Skaggs").
parent("Lila Petry", "Kirk Petry").
parent("Lila Petry", "Reyna Petry").
parent("Lucas Mckenna", "Carey Mckenna").
parent("Lucas Mckenna", "Windy Mckenna").
parent("Maranda Lizotte", "Dwain Lizotte").
parent("Maranda Lizotte", "Rosina Lizotte").
parent("Margot Skaggs", "Hanh Mohan").
parent("Margot Skaggs", "Jarrod Mohan").
parent("Minerva Wilkie", "Harold Wilkie").
parent("Minerva Wilkie", "Yoko Wilkie").
parent("Nathanial Lizotte", "Dwain Lizotte").
parent("Nathanial Lizotte", "Rosina Lizotte").
parent("Reyna Petry", "Odis Lizotte").
parent("Reyna Petry", "Ora Lizotte").
parent("Rolland Mckenna", "Carey Mckenna").
parent("Rolland Mckenna", "Windy Mckenna").
parent("Rosendo Skaggs", "Jeannine Skaggs").
parent("Rosendo Skaggs", "Weldon Skaggs").
parent("Shirley Skaggs", "Margot Skaggs").
parent("Shirley Skaggs", "Rosendo Skaggs").
parent("Windy Mckenna", "Odis Lizotte").
parent("Windy Mckenna", "Ora Lizotte").
parent("Yoko Wilkie", "Dwain Lizotte").
parent("Yoko Wilkie", "Rosina Lizotte").
parent("Ashely Kee", "Edmond Schreiner").
parent("Ashely Kee", "Kristi Schreiner").
parent("Benton Earnest", "Maria Earnest").
parent("Benton Earnest", "Roland Earnest").
parent("Calvin Woodman", "Geri Woodman").
parent("Calvin Woodman", "Ron Woodman").
parent("Cherise Earnest", "Benton Earnest").
parent("Cherise Earnest", "Samantha Earnest").
parent("Duncan Pannell", "Randell Pannell").
parent("Duncan Pannell", "Tamala Pannell").
parent("Eduardo Earnest", "Benton Earnest").
parent("Eduardo Earnest", "Samantha Earnest").
parent("Edythe Earnest", "Benton Earnest").
parent("Edythe Earnest", "Samantha Earnest").
parent("Geri Woodman", "Maria Earnest").
parent("Geri Woodman", "Roland Earnest").
parent("Ian Pannell", "Ivory Pannell").
parent("Ian Pannell", "Lanny Pannell").
parent("Ivory Pannell", "Ashely Kee").
parent("Ivory Pannell", "Dane Kee").
parent("Lanny Pannell", "Duncan Pannell").
parent("Lanny Pannell", "Mona Pannell").
parent("Quincy Pannell", "Ian Pannell").
parent("Quincy Pannell", "Johnnie Pannell").
parent("Reggie Earnest", "Benton Earnest").
parent("Reggie Earnest", "Samantha Earnest").
parent("Roland Earnest", "Hazel Earnest").
parent("Roland Earnest", "Mickey Earnest").
parent("Samantha Earnest", "Ian Pannell").
parent("Samantha Earnest", "Johnnie Pannell").
parent("Adalberto Cedillo", "Domonique Cedillo").
parent("Adalberto Cedillo", "Kasey Cedillo").
parent("Alberta Abraham", "Oliver Abraham").
parent("Alberta Abraham", "Taneka Abraham").
parent("Dillon Abraham", "Oliver Abraham").
parent("Dillon Abraham", "Taneka Abraham").
parent("Domonique Cedillo", "Dillon Abraham").
parent("Domonique Cedillo", "Shirleen Abraham").
parent("Elissa Cedillo", "Domonique Cedillo").
parent("Elissa Cedillo", "Kasey Cedillo").
parent("Jimmy Cedillo", "Lucienne Cedillo").
parent("Jimmy Cedillo", "Ron Cedillo").
parent("Kasey Cedillo", "Bee Cedillo").
parent("Kasey Cedillo", "Ned Cedillo").
parent("Lorine Wasserman", "Elsy Hornback").
parent("Lorine Wasserman", "Reinaldo Hornback").
parent("Luisa Hornback", "Gerardo Hornback").
parent("Luisa Hornback", "Karla Hornback").
parent("Murray Cedillo", "Lucienne Cedillo").
parent("Murray Cedillo", "Ron Cedillo").
parent("Reinaldo Hornback", "Gerardo Hornback").
parent("Reinaldo Hornback", "Karla Hornback").
parent("Ron Cedillo", "Domonique Cedillo").
parent("Ron Cedillo", "Kasey Cedillo").
parent("Shanda Wasserman", "Aurelio Wasserman").
parent("Shanda Wasserman", "Lorine Wasserman").
parent("Shirleen Abraham", "Elsy Hornback").
parent("Shirleen Abraham", "Reinaldo Hornback").
parent("Stuart Abraham", "Oliver Abraham").
parent("Stuart Abraham", "Taneka Abraham").
parent("Yvette Cedillo", "Lucienne Cedillo").
parent("Yvette Cedillo", "Ron Cedillo").
parent("Anibal Schoonmaker", "Ali Schoonmaker").
parent("Anibal Schoonmaker", "Robyn Schoonmaker").
parent("Annabelle Schoonmaker", "Ali Schoonmaker").
parent("Annabelle Schoonmaker", "Robyn Schoonmaker").
parent("Blair Etheridge", "Anibal Schoonmaker").
parent("Blair Etheridge", "Effie Schoonmaker").
parent("Esteban Schoonmaker", "Ali Schoonmaker").
parent("Esteban Schoonmaker", "Robyn Schoonmaker").
parent("Ester Palermo", "Malik Loftus").
parent("Ester Palermo", "Tessie Loftus").
parent("Francisco Palermo", "Enoch Palermo").
parent("Francisco Palermo", "Sylvia Palermo").
parent("Hannah Palermo", "Enoch Palermo").
parent("Hannah Palermo", "Sylvia Palermo").
parent("Joel Palermo", "Ester Palermo").
parent("Joel Palermo", "Francisco Palermo").
parent("Jona Carrell", "Ali Schoonmaker").
parent("Jona Carrell", "Robyn Schoonmaker").
parent("Liane Schoonmaker", "Ali Schoonmaker").
parent("Liane Schoonmaker", "Robyn Schoonmaker").
parent("Madelyn Palermo", "Ester Palermo").
parent("Madelyn Palermo", "Francisco Palermo").
parent("Monique Palermo", "Enoch Palermo").
parent("Monique Palermo", "Sylvia Palermo").
parent("Ofelia Carrell", "Jona Carrell").
parent("Ofelia Carrell", "Rigoberto Carrell").
parent("Roman Palermo", "Ester Palermo").
parent("Roman Palermo", "Francisco Palermo").
parent("Rosanna Palermo", "Enoch Palermo").
parent("Rosanna Palermo", "Sylvia Palermo").
parent("Sylvia Palermo", "Blair Etheridge").
parent("Sylvia Palermo", "Cary Etheridge").
parent("Zoraida Palermo", "Ester Palermo").
parent("Zoraida Palermo", "Francisco Palermo").
parent("Abraham Decosta", "Elwood Decosta").
parent("Abraham Decosta", "Niesha Decosta").
parent("Adolph Brannan", "Marcel Brannan").
parent("Adolph Brannan", "Margo Brannan").
parent("Carson Kovach", "Everett Kovach").
parent("Carson Kovach", "Margaret Kovach").
parent("Charlie Kovach", "Everett Kovach").
parent("Charlie Kovach", "Margaret Kovach").
parent("Daniel Brannan", "Adolph Brannan").
parent("Daniel Brannan", "Rosalinda Brannan").
parent("Elissa Kovach", "Everett Kovach").
parent("Elissa Kovach", "Margaret Kovach").
parent("Elwood Decosta", "Stuart Decosta").
parent("Elwood Decosta", "Zoila Decosta").
parent("Jacques Decosta", "Stuart Decosta").
parent("Jacques Decosta", "Zoila Decosta").
parent("Laura Kovach", "Charlie Kovach").
parent("Laura Kovach", "Ester Kovach").
parent("Laurel Decosta", "Stuart Decosta").
parent("Laurel Decosta", "Zoila Decosta").
parent("Laverna Kovach", "Everett Kovach").
parent("Laverna Kovach", "Margaret Kovach").
parent("Lea Levy", "Adolph Brannan").
parent("Lea Levy", "Rosalinda Brannan").
parent("Marcel Brannan", "Casey Brannan").
parent("Marcel Brannan", "Deborah Brannan").
parent("Margaret Kovach", "Adolph Brannan").
parent("Margaret Kovach", "Rosalinda Brannan").
parent("Margo Brannan", "Stuart Decosta").
parent("Margo Brannan", "Zoila Decosta").
parent("Pasquale Levy", "Jules Levy").
parent("Pasquale Levy", "Lea Levy").
parent("Bruce Mason", "Clarence Mason").
parent("Bruce Mason", "Joslyn Mason").
parent("Clayton Shirk", "Jame Shirk").
parent("Clayton Shirk", "Maurine Shirk").
parent("Craig Boutte", "Johnathan Boutte").
parent("Craig Boutte", "Marlana Boutte").
parent("Darin Shirk", "Clayton Shirk").
parent("Darin Shirk", "Nada Shirk").
parent("Freddy Shirk", "Darin Shirk").
parent("Freddy Shirk", "Mercedes Shirk").
parent("Hilton Griffiths", "Monique Griffiths").
parent("Hilton Griffiths", "Spencer Griffiths").
parent("Johnathan Boutte", "Hanh Boutte").
parent("Johnathan Boutte", "Kevin Boutte").
parent("Lauretta Mason", "Elton Griffiths").
parent("Lauretta Mason", "Olivia Griffiths").
parent("Marlana Boutte", "Elton Griffiths").
parent("Marlana Boutte", "Olivia Griffiths").
parent("Maurine Shirk", "Bryant Bradberry").
parent("Maurine Shirk", "Chelsie Bradberry").
parent("Olivia Griffiths", "Clayton Shirk").
parent("Olivia Griffiths", "Nada Shirk").
parent("Roger Griffiths", "Monique Griffiths").
parent("Roger Griffiths", "Spencer Griffiths").
parent("Spencer Griffiths", "Elton Griffiths").
parent("Spencer Griffiths", "Olivia Griffiths").
parent("Zoila Mason", "Bruce Mason").
parent("Zoila Mason", "Lauretta Mason").

cousin(X, Y) :-
    parent(X, A),
    parent(Y, B),
    sibling(A, B),
    X\=Y.

:- dynamic term_expansion/4.
:- multifile term_expansion/4.


uncle(X, Y) :-
    parent(X, A),
    brother(A, Y).

aunt(X, Y) :-
    parent(X, A),
    sister(A, Y).

second_uncle(X, Y) :-
    great_grandparent(X, A),
    brother(A, Y).

:- multifile message_property/2.


:- dynamic gender/2.

gender("Aida Wang", "female").
gender("Alison Smock", "female").
gender("Alvaro Smock", "male").
gender("Aubrey Smock", "male").
gender("Brian Beltran", "male").
gender("Daisy Beltran", "female").
gender("Deane Smock", "female").
gender("Dino Beltran", "male").
gender("Dominique Smock", "female").
gender("Gene Smock", "male").
gender("Isabell Smock", "female").
gender("Jeannine Wexler", "female").
gender("Johnetta Wang", "female").
gender("Lannie Smock", "female").
gender("Leeann Hackworth", "female").
gender("Lenore Hackworth", "female").
gender("Myrle Smock", "female").
gender("Orlando Beltran", "male").
gender("Ricardo Hackworth", "male").
gender("Ryan Wang", "male").
gender("Saul Wexler", "male").
gender("Shelli Beltran", "female").
gender("Valentina Wexler", "female").
gender("Vicki Hackworth", "female").
gender("Williams Smock", "male").
gender("Alberto Saari", "male").
gender("Alycia Cormier", "female").
gender("Andy Clemons", "male").
gender("Bert Deluna", "male").
gender("Christoper Cormier", "male").
gender("Clifford Cormier", "male").
gender("Deborah Cormier", "female").
gender("Dion Cormier", "male").
gender("Earle Cormier", "male").
gender("Ella Saari", "female").
gender("Foster Cormier", "male").
gender("Geri Deluna", "female").
gender("Hunter Saari", "male").
gender("Jeana Clemons", "female").
gender("Julia Cormier", "female").
gender("Leann Cormier", "female").
gender("Leda Cormier", "female").
gender("Ming Cormier", "female").
gender("Patsy Cormier", "female").
gender("Shawnta Saari", "female").
gender("Sherry Cormier", "female").
gender("Sol Cormier", "male").
gender("Therese Cormier", "female").
gender("Trevor Saari", "male").
gender("Virgie Saari", "female").
gender("Amanda Mcnew", "female").
gender("Amberly Mcnew", "female").
gender("Caleb Haber", "male").
gender("Cole Mcnew", "male").
gender("Don Mcnew", "male").
gender("Dudley Wise", "male").
gender("Ernesto Mcnew", "male").
gender("Garry Mcnew", "male").
gender("Goldie Henderson", "female").
gender("Hayden Mcnew", "male").
gender("Haywood Mcnew", "male").
gender("Jacinta Wise", "female").
gender("Jeanelle Mcnew", "female").
gender("Jung Henderson", "female").
gender("Kris Haber", "female").
gender("Lorelei Mcnew", "female").
gender("Marcelino Mcnew", "male").
gender("Marko Henderson", "male").
gender("Maxwell Henderson", "male").
gender("Merrill Mcnew", "male").
gender("Milton Henderson", "male").
gender("Noelia Henderson", "female").
gender("Rae Mcnew", "female").
gender("Roxy Mcnew", "female").
gender("Stefan Henderson", "male").
gender("Aletha Nicolas", "female").
gender("Anthony Nicolas", "male").
gender("Barney Langley", "male").
gender("Bradford Nicolas", "male").
gender("Carrol Nicolas", "male").
gender("Cherry Nicolas", "female").
gender("Connie Nicolas", "female").
gender("Dwayne Langley", "male").
gender("Edythe Nicolas", "female").
gender("Eldon Nicolas", "male").
gender("Errol Brook", "male").
gender("Eula Crain", "female").
gender("Lera Brook", "female").
gender("Lucas Crain", "male").
gender("Marilyn Nicolas", "female").
gender("Phylis Nicolas", "female").
gender("Preston Francois", "male").
gender("Rosalinda Francois", "female").
gender("Rubye Crain", "female").
gender("Rufus Brook", "male").
gender("Sha Langley", "female").
gender("Theodore Crain", "male").
gender("Thurman Crain", "male").
gender("Ulysses Nicolas", "male").
gender("Yoshiko Crain", "female").
gender("Zulema Crain", "female").
gender("Carey Mckenna", "male").
gender("Chuck Lizotte", "male").
gender("Dwain Lizotte", "male").
gender("Hanh Mohan", "female").
gender("Harold Wilkie", "male").
gender("Hoa Skaggs", "female").
gender("Jarrod Mohan", "male").
gender("Jeannine Skaggs", "female").
gender("Kirk Petry", "male").
gender("Lila Petry", "female").
gender("Lucas Mckenna", "male").
gender("Maranda Lizotte", "female").
gender("Margot Skaggs", "female").
gender("Minerva Wilkie", "female").
gender("Nathanial Lizotte", "male").
gender("Odis Lizotte", "male").
gender("Ora Lizotte", "female").
gender("Reyna Petry", "female").
gender("Rolland Mckenna", "male").
gender("Rosendo Skaggs", "male").
gender("Rosina Lizotte", "female").
gender("Shirley Skaggs", "female").
gender("Weldon Skaggs", "male").
gender("Windy Mckenna", "female").
gender("Yoko Wilkie", "female").
gender("Ashely Kee", "female").
gender("Benton Earnest", "male").
gender("Calvin Woodman", "male").
gender("Cherise Earnest", "female").
gender("Dane Kee", "male").
gender("Duncan Pannell", "male").
gender("Edmond Schreiner", "male").
gender("Eduardo Earnest", "male").
gender("Edythe Earnest", "female").
gender("Geri Woodman", "female").
gender("Hazel Earnest", "female").
gender("Ian Pannell", "male").
gender("Ivory Pannell", "female").
gender("Johnnie Pannell", "female").
gender("Kristi Schreiner", "female").
gender("Lanny Pannell", "male").
gender("Maria Earnest", "female").
gender("Mickey Earnest", "male").
gender("Mona Pannell", "female").
gender("Quincy Pannell", "male").
gender("Randell Pannell", "male").
gender("Reggie Earnest", "male").
gender("Roland Earnest", "male").
gender("Ron Woodman", "male").
gender("Samantha Earnest", "female").
gender("Tamala Pannell", "female").
gender("Adalberto Cedillo", "male").
gender("Alberta Abraham", "female").
gender("Aurelio Wasserman", "male").
gender("Bee Cedillo", "female").
gender("Dillon Abraham", "male").
gender("Domonique Cedillo", "female").
gender("Elissa Cedillo", "female").
gender("Elsy Hornback", "female").
gender("Gerardo Hornback", "male").
gender("Jimmy Cedillo", "male").
gender("Karla Hornback", "female").
gender("Kasey Cedillo", "male").
gender("Lorine Wasserman", "female").
gender("Lucienne Cedillo", "female").
gender("Luisa Hornback", "female").
gender("Murray Cedillo", "male").
gender("Ned Cedillo", "male").
gender("Oliver Abraham", "male").
gender("Reinaldo Hornback", "male").
gender("Ron Cedillo", "male").
gender("Shanda Wasserman", "female").
gender("Shirleen Abraham", "female").
gender("Stuart Abraham", "male").
gender("Taneka Abraham", "female").
gender("Yvette Cedillo", "female").
gender("Ali Schoonmaker", "male").
gender("Anibal Schoonmaker", "male").
gender("Annabelle Schoonmaker", "female").
gender("Blair Etheridge", "female").
gender("Cary Etheridge", "male").
gender("Effie Schoonmaker", "female").
gender("Enoch Palermo", "male").
gender("Esteban Schoonmaker", "male").
gender("Ester Palermo", "female").
gender("Francisco Palermo", "male").
gender("Hannah Palermo", "female").
gender("Joel Palermo", "male").
gender("Jona Carrell", "female").
gender("Liane Schoonmaker", "female").
gender("Madelyn Palermo", "female").
gender("Malik Loftus", "male").
gender("Monique Palermo", "female").
gender("Ofelia Carrell", "female").
gender("Rigoberto Carrell", "male").
gender("Robyn Schoonmaker", "female").
gender("Roman Palermo", "male").
gender("Rosanna Palermo", "female").
gender("Sylvia Palermo", "female").
gender("Tessie Loftus", "female").
gender("Zoraida Palermo", "female").
gender("Abraham Decosta", "male").
gender("Adolph Brannan", "male").
gender("Carson Kovach", "male").
gender("Casey Brannan", "male").
gender("Charlie Kovach", "male").
gender("Daniel Brannan", "male").
gender("Deborah Brannan", "female").
gender("Elissa Kovach", "female").
gender("Elwood Decosta", "male").
gender("Ester Kovach", "female").
gender("Everett Kovach", "male").
gender("Jacques Decosta", "male").
gender("Jules Levy", "male").
gender("Laura Kovach", "female").
gender("Laurel Decosta", "female").
gender("Laverna Kovach", "female").
gender("Lea Levy", "female").
gender("Marcel Brannan", "male").
gender("Margaret Kovach", "female").
gender("Margo Brannan", "female").
gender("Niesha Decosta", "female").
gender("Pasquale Levy", "male").
gender("Rosalinda Brannan", "female").
gender("Stuart Decosta", "male").
gender("Zoila Decosta", "female").
gender("Bruce Mason", "male").
gender("Bryant Bradberry", "male").
gender("Chelsie Bradberry", "female").
gender("Clarence Mason", "male").
gender("Clayton Shirk", "male").
gender("Craig Boutte", "male").
gender("Darin Shirk", "male").
gender("Elton Griffiths", "male").
gender("Freddy Shirk", "male").
gender("Hanh Boutte", "female").
gender("Hilton Griffiths", "male").
gender("Jame Shirk", "male").
gender("Johnathan Boutte", "male").
gender("Joslyn Mason", "female").
gender("Kevin Boutte", "male").
gender("Lauretta Mason", "female").
gender("Marlana Boutte", "female").
gender("Maurine Shirk", "female").
gender("Mercedes Shirk", "female").
gender("Monique Griffiths", "female").
gender("Nada Shirk", "female").
gender("Olivia Griffiths", "female").
gender("Roger Griffiths", "male").
gender("Spencer Griffiths", "male").
gender("Zoila Mason", "female").

second_aunt(X, Y) :-
    great_grandparent(X, A),
    sister(A, Y).

great_granddaughter(X, Y) :-
    great_grandchild(X, Y),
    female(Y).

:- dynamic save_all_clauses_to_file/1.

save_all_clauses_to_file(A) :-
    open(A, write, B),
    set_output(B),
    listing,
    close(B).

great_grandson(X, Y) :-
    great_grandchild(X, Y),
    male(Y).

:- dynamic pyrun/2.

pyrun(A, B) :-
    read_term_from_atom(A, C, [variable_names(B)]),
    call(C).

great_grandfather(X, Y) :-
    great_grandparent(X, Y),
    male(Y).

:- dynamic file_search_path/2.
:- multifile file_search_path/2.

file_search_path(library, A) :-
    user:library_directory(A).
file_search_path(swi, A) :-
    system:current_prolog_flag(home, A).
file_search_path(swi, A) :-
    system:current_prolog_flag(shared_home, A).
file_search_path(library, app_config(lib)).
file_search_path(library, swi(library)).
file_search_path(library, swi(library/clp)).
file_search_path(library, A) :-
    system:'$ext_library_directory'(A).
file_search_path(path, A) :-
    system:
    (   getenv('PATH', B),
        current_prolog_flag(path_sep, C),
        atomic_list_concat(D, C, B),
        '$member'(A, D)
    ).
file_search_path(user_app_data, A) :-
    system:'$xdg_prolog_directory'(data, A).
file_search_path(common_app_data, A) :-
    system:'$xdg_prolog_directory'(common_data, A).
file_search_path(user_app_config, A) :-
    system:'$xdg_prolog_directory'(config, A).
file_search_path(common_app_config, A) :-
    system:'$xdg_prolog_directory'(common_config, A).
file_search_path(app_data, user_app_data('.')).
file_search_path(app_data, common_app_data('.')).
file_search_path(app_config, user_app_config('.')).
file_search_path(app_config, common_app_config('.')).
file_search_path(app_preferences, user_app_config('.')).
file_search_path(user_profile, app_preferences('.')).
file_search_path(app, swi(app)).
file_search_path(app, app_data(app)).
file_search_path(working_directory, A) :-
    system:working_directory(A, A).
file_search_path(autoload, swi(library)).
file_search_path(autoload, pce(prolog/lib)).
file_search_path(autoload, app_config(lib)).
file_search_path(autoload, Dir) :-
    '$autoload':'$ext_library_directory'(Dir).
file_search_path(pack, app_data(pack)).
file_search_path(library, PackLib) :-
    '$pack':pack_dir(_Name, prolog, PackLib).
file_search_path(foreign, PackLib) :-
    '$pack':pack_dir(_Name, foreign, PackLib).
file_search_path(app, AppDir) :-
    '$pack':pack_dir(_Name, app, AppDir).

:- dynamic resource/3.
:- multifile resource/3.


great_grandchild(X, Y) :-
    great_grandparent(Y, X).

great_grandparent(X, Y) :-
    grandparent(X, Z),
    parent(Z, Y).

great_grandmother(X, Y) :-
    great_grandparent(X, Y),
    female(Y).

:- dynamic goal_expansion/2.
:- multifile goal_expansion/2.


:- dynamic hobby/2.

hobby("Aida Wang", "meditation").
hobby("Alison Smock", "meteorology").
hobby("Alvaro Smock", "biology").
hobby("Aubrey Smock", "meteorology").
hobby("Brian Beltran", "dolls").
hobby("Daisy Beltran", "photography").
hobby("Deane Smock", "shogi").
hobby("Dino Beltran", "dominoes").
hobby("Dominique Smock", "tether car").
hobby("Gene Smock", "architecture").
hobby("Isabell Smock", "geocaching").
hobby("Jeannine Wexler", "trainspotting").
hobby("Johnetta Wang", "bus spotting").
hobby("Lannie Smock", "research").
hobby("Leeann Hackworth", "geography").
hobby("Lenore Hackworth", "microbiology").
hobby("Myrle Smock", "canoeing").
hobby("Orlando Beltran", "learning").
hobby("Ricardo Hackworth", "dairy farming").
hobby("Ryan Wang", "fossil hunting").
hobby("Saul Wexler", "sociology").
hobby("Shelli Beltran", "finance").
hobby("Valentina Wexler", "meditation").
hobby("Vicki Hackworth", "wikipedia editing").
hobby("Williams Smock", "radio-controlled car racing").
hobby("Alberto Saari", "social studies").
hobby("Alycia Cormier", "judo").
hobby("Andy Clemons", "flying disc").
hobby("Bert Deluna", "cricket").
hobby("Christoper Cormier", "weightlifting").
hobby("Clifford Cormier", "meditation").
hobby("Deborah Cormier", "ballroom dancing").
hobby("Dion Cormier", "microscopy").
hobby("Earle Cormier", "reading").
hobby("Ella Saari", "laser tag").
hobby("Foster Cormier", "hiking/backpacking").
hobby("Geri Deluna", "audiophile").
hobby("Hunter Saari", "tennis polo").
hobby("Jeana Clemons", "photography").
hobby("Julia Cormier", "backgammon").
hobby("Leann Cormier", "microscopy").
hobby("Leda Cormier", "herping").
hobby("Ming Cormier", "philately").
hobby("Patsy Cormier", "birdwatching").
hobby("Shawnta Saari", "shogi").
hobby("Sherry Cormier", "magnet fishing").
hobby("Sol Cormier", "table tennis").
hobby("Therese Cormier", "scuba diving").
hobby("Trevor Saari", "biology").
hobby("Virgie Saari", "sea glass collecting").
hobby("Amanda Mcnew", "research").
hobby("Amberly Mcnew", "gongoozling").
hobby("Caleb Haber", "benchmarking").
hobby("Cole Mcnew", "sea glass collecting").
hobby("Don Mcnew", "bowling").
hobby("Dudley Wise", "audiophile").
hobby("Ernesto Mcnew", "tea bag collecting").
hobby("Garry Mcnew", "model aircraft").
hobby("Goldie Henderson", "herping").
hobby("Hayden Mcnew", "figure skating").
hobby("Haywood Mcnew", "fossil hunting").
hobby("Jacinta Wise", "airsoft").
hobby("Jeanelle Mcnew", "whale watching").
hobby("Jung Henderson", "pinball").
hobby("Kris Haber", "research").
hobby("Lorelei Mcnew", "flying model planes").
hobby("Marcelino Mcnew", "ant farming").
hobby("Marko Henderson", "volleyball").
hobby("Maxwell Henderson", "gongoozling").
hobby("Merrill Mcnew", "vehicle restoration").
hobby("Milton Henderson", "car riding").
hobby("Noelia Henderson", "mycology").
hobby("Rae Mcnew", "table football").
hobby("Roxy Mcnew", "photography").
hobby("Stefan Henderson", "metal detecting").
hobby("Aletha Nicolas", "archery").
hobby("Anthony Nicolas", "reading").
hobby("Barney Langley", "shortwave listening").
hobby("Bradford Nicolas", "snowmobiling").
hobby("Carrol Nicolas", "research").
hobby("Cherry Nicolas", "religious studies").
hobby("Connie Nicolas", "cooking").
hobby("Dwayne Langley", "kart racing").
hobby("Edythe Nicolas", "darts").
hobby("Eldon Nicolas", "herping").
hobby("Errol Brook", "backgammon").
hobby("Eula Crain", "herping").
hobby("Lera Brook", "ant farming").
hobby("Lucas Crain", "ephemera collecting").
hobby("Marilyn Nicolas", "bus spotting").
hobby("Phylis Nicolas", "research").
hobby("Preston Francois", "croquet").
hobby("Rosalinda Francois", "leaves").
hobby("Rubye Crain", "antiquities").
hobby("Rufus Brook", "field hockey").
hobby("Sha Langley", "leaves").
hobby("Theodore Crain", "auto audiophilia").
hobby("Thurman Crain", "magic").
hobby("Ulysses Nicolas", "people-watching").
hobby("Yoshiko Crain", "social studies").
hobby("Zulema Crain", "mineral collecting").
hobby("Carey Mckenna", "fusilately").
hobby("Chuck Lizotte", "surfing").
hobby("Dwain Lizotte", "magic").
hobby("Hanh Mohan", "story writing").
hobby("Harold Wilkie", "curling").
hobby("Hoa Skaggs", "museum visiting").
hobby("Jarrod Mohan", "benchmarking").
hobby("Jeannine Skaggs", "meteorology").
hobby("Kirk Petry", "entrepreneurship").
hobby("Lila Petry", "deltiology").
hobby("Lucas Mckenna", "badminton").
hobby("Maranda Lizotte", "flag football").
hobby("Margot Skaggs", "shooting").
hobby("Minerva Wilkie", "rock tumbling").
hobby("Nathanial Lizotte", "beekeeping").
hobby("Odis Lizotte", "ephemera collecting").
hobby("Ora Lizotte", "medical science").
hobby("Reyna Petry", "microscopy").
hobby("Rolland Mckenna", "leaves").
hobby("Rosendo Skaggs", "philately").
hobby("Rosina Lizotte", "research").
hobby("Shirley Skaggs", "horseshoes").
hobby("Weldon Skaggs", "insect collecting").
hobby("Windy Mckenna", "fencing").
hobby("Yoko Wilkie", "insect collecting").
hobby("Ashely Kee", "book collecting").
hobby("Benton Earnest", "business").
hobby("Calvin Woodman", "fishkeeping").
hobby("Cherise Earnest", "dolls").
hobby("Dane Kee", "fitness").
hobby("Duncan Pannell", "paintball").
hobby("Edmond Schreiner", "vintage clothing").
hobby("Eduardo Earnest", "shuffleboard").
hobby("Edythe Earnest", "sports memorabilia").
hobby("Geri Woodman", "kart racing").
hobby("Hazel Earnest", "trapshooting").
hobby("Ian Pannell", "table tennis").
hobby("Ivory Pannell", "rock climbing").
hobby("Johnnie Pannell", "gymnastics").
hobby("Kristi Schreiner", "auto audiophilia").
hobby("Lanny Pannell", "myrmecology").
hobby("Maria Earnest", "flower collecting and pressing").
hobby("Mickey Earnest", "baton twirling").
hobby("Mona Pannell", "metal detecting").
hobby("Quincy Pannell", "radio-controlled model playing").
hobby("Randell Pannell", "fossicking").
hobby("Reggie Earnest", "shopping").
hobby("Roland Earnest", "satellite watching").
hobby("Ron Woodman", "carrier pigeons").
hobby("Samantha Earnest", "publishing").
hobby("Tamala Pannell", "learning").
hobby("Adalberto Cedillo", "fishing").
hobby("Alberta Abraham", "mini golf").
hobby("Aurelio Wasserman", "beekeeping").
hobby("Bee Cedillo", "sailing").
hobby("Dillon Abraham", "cycling").
hobby("Domonique Cedillo", "hobby horsing").
hobby("Elissa Cedillo", "dog walking").
hobby("Elsy Hornback", "life science").
hobby("Gerardo Hornback", "leaves").
hobby("Jimmy Cedillo", "volleyball").
hobby("Karla Hornback", "railway studies").
hobby("Kasey Cedillo", "butterfly watching").
hobby("Lorine Wasserman", "magnet fishing").
hobby("Lucienne Cedillo", "insect collecting").
hobby("Luisa Hornback", "films").
hobby("Murray Cedillo", "race walking").
hobby("Ned Cedillo", "dairy farming").
hobby("Oliver Abraham", "wikipedia editing").
hobby("Reinaldo Hornback", "kart racing").
hobby("Ron Cedillo", "people-watching").
hobby("Shanda Wasserman", "whale watching").
hobby("Shirleen Abraham", "shooting sports").
hobby("Stuart Abraham", "debate").
hobby("Taneka Abraham", "table tennis").
hobby("Yvette Cedillo", "archaeology").
hobby("Ali Schoonmaker", "lotology").
hobby("Anibal Schoonmaker", "stone collecting").
hobby("Annabelle Schoonmaker", "birdwatching").
hobby("Blair Etheridge", "rock balancing").
hobby("Cary Etheridge", "karting").
hobby("Effie Schoonmaker", "disc golf").
hobby("Enoch Palermo", "shortwave listening").
hobby("Esteban Schoonmaker", "audiophile").
hobby("Ester Palermo", "bus spotting").
hobby("Francisco Palermo", "shortwave listening").
hobby("Hannah Palermo", "fishkeeping").
hobby("Joel Palermo", "tea bag collecting").
hobby("Jona Carrell", "phillumeny").
hobby("Liane Schoonmaker", "stamp collecting").
hobby("Madelyn Palermo", "volleyball").
hobby("Malik Loftus", "learning").
hobby("Monique Palermo", "shooting").
hobby("Ofelia Carrell", "audiophile").
hobby("Rigoberto Carrell", "knife collecting").
hobby("Robyn Schoonmaker", "learning").
hobby("Roman Palermo", "letterboxing").
hobby("Rosanna Palermo", "beekeeping").
hobby("Sylvia Palermo", "bridge").
hobby("Tessie Loftus", "perfume").
hobby("Zoraida Palermo", "films").
hobby("Abraham Decosta", "lacrosse").
hobby("Adolph Brannan", "metal detecting").
hobby("Carson Kovach", "speedcubing").
hobby("Casey Brannan", "scutelliphily").
hobby("Charlie Kovach", "psychology").
hobby("Daniel Brannan", "chess").
hobby("Deborah Brannan", "radio-controlled model playing").
hobby("Elissa Kovach", "birdwatching").
hobby("Elwood Decosta", "antiquities").
hobby("Ester Kovach", "vehicle restoration").
hobby("Everett Kovach", "judo").
hobby("Jacques Decosta", "sea glass collecting").
hobby("Jules Levy", "neuroscience").
hobby("Laura Kovach", "whale watching").
hobby("Laurel Decosta", "antiquities").
hobby("Laverna Kovach", "croquet").
hobby("Lea Levy", "martial arts").
hobby("Marcel Brannan", "microscopy").
hobby("Margaret Kovach", "flower collecting and pressing").
hobby("Margo Brannan", "publishing").
hobby("Niesha Decosta", "beekeeping").
hobby("Pasquale Levy", "table tennis").
hobby("Rosalinda Brannan", "cornhole").
hobby("Stuart Decosta", "horseshoes").
hobby("Zoila Decosta", "flying disc").
hobby("Bruce Mason", "ant farming").
hobby("Bryant Bradberry", "architecture").
hobby("Chelsie Bradberry", "ant farming").
hobby("Clarence Mason", "cycling").
hobby("Clayton Shirk", "tennis polo").
hobby("Craig Boutte", "fencing").
hobby("Darin Shirk", "vegetable farming").
hobby("Elton Griffiths", "vr gaming").
hobby("Freddy Shirk", "sports memorabilia").
hobby("Hanh Boutte", "martial arts").
hobby("Hilton Griffiths", "mini golf").
hobby("Jame Shirk", "shortwave listening").
hobby("Johnathan Boutte", "amusement park visiting").
hobby("Joslyn Mason", "aerospace").
hobby("Kevin Boutte", "rowing").
hobby("Lauretta Mason", "book collecting").
hobby("Marlana Boutte", "pickleball").
hobby("Maurine Shirk", "finance").
hobby("Mercedes Shirk", "field hockey").
hobby("Monique Griffiths", "birdwatching").
hobby("Nada Shirk", "beach volleyball").
hobby("Olivia Griffiths", "geocaching").
hobby("Roger Griffiths", "mineral collecting").
hobby("Spencer Griffiths", "psychology").
hobby("Zoila Mason", "audiophile").

granddaughter(X, Y) :-
    grandchild(X, Y),
    female(Y).

grandson(X, Y) :-
    grandchild(X, Y),
    male(Y).

:- dynamic job/2.

job("Aida Wang", "personal assistant").
job("Alison Smock", "health promotion specialist").
job("Alvaro Smock", "osteopath").
job("Aubrey Smock", "broadcast engineer").
job("Brian Beltran", "oncologist").
job("Daisy Beltran", "warehouse manager").
job("Deane Smock", "associate professor").
job("Dino Beltran", "sports therapist").
job("Dominique Smock", "retail manager").
job("Gene Smock", "immunologist").
job("Isabell Smock", "education administrator").
job("Jeannine Wexler", "early years teacher").
job("Johnetta Wang", "biomedical scientist").
job("Lannie Smock", "music tutor").
job("Leeann Hackworth", "clinical cytogeneticist").
job("Lenore Hackworth", "ecologist").
job("Myrle Smock", "barrister's clerk").
job("Orlando Beltran", "petroleum engineer").
job("Ricardo Hackworth", "clinical research associate").
job("Ryan Wang", "chief of staff").
job("Saul Wexler", "occupational therapist").
job("Shelli Beltran", "actuary").
job("Valentina Wexler", "police officer").
job("Vicki Hackworth", "sound technician").
job("Williams Smock", "theatre manager").
job("Alberto Saari", "clinical biochemist").
job("Alycia Cormier", "public relations officer").
job("Andy Clemons", "music therapist").
job("Bert Deluna", "librarian").
job("Christoper Cormier", "building surveyor").
job("Clifford Cormier", "fitness centre manager").
job("Deborah Cormier", "oceanographer").
job("Dion Cormier", "historic buildings inspector").
job("Earle Cormier", "chief marketing officer").
job("Ella Saari", "waste management officer").
job("Foster Cormier", "medical sales representative").
job("Geri Deluna", "community pharmacist").
job("Hunter Saari", "pension scheme manager").
job("Jeana Clemons", "armed forces logistics officer").
job("Julia Cormier", "environmental education officer").
job("Leann Cormier", "medical illustrator").
job("Leda Cormier", "museum conservator").
job("Ming Cormier", "optometrist").
job("Patsy Cormier", "further education lecturer").
job("Shawnta Saari", "dancer").
job("Sherry Cormier", "water engineer").
job("Sol Cormier", "intelligence analyst").
job("Therese Cormier", "fashion designer").
job("Trevor Saari", "doctor").
job("Virgie Saari", "chartered accountant").
job("Amanda Mcnew", "speech and language therapist").
job("Amberly Mcnew", "clinical embryologist").
job("Caleb Haber", "community development worker").
job("Cole Mcnew", "games developer").
job("Don Mcnew", "accommodation manager").
job("Dudley Wise", "conservation officer").
job("Ernesto Mcnew", "forensic scientist").
job("Garry Mcnew", "pharmacologist").
job("Goldie Henderson", "dance movement psychotherapist").
job("Hayden Mcnew", "paediatric nurse").
job("Haywood Mcnew", "research officer").
job("Jacinta Wise", "production designer").
job("Jeanelle Mcnew", "community development worker").
job("Jung Henderson", "clinical molecular geneticist").
job("Kris Haber", "set designer").
job("Lorelei Mcnew", "town planner").
job("Marcelino Mcnew", "print production planner").
job("Marko Henderson", "equality and diversity officer").
job("Maxwell Henderson", "chartered loss adjuster").
job("Merrill Mcnew", "sales promotion account executive").
job("Milton Henderson", "banker").
job("Noelia Henderson", "systems developer").
job("Rae Mcnew", "chief financial officer").
job("Roxy Mcnew", "regulatory affairs officer").
job("Stefan Henderson", "architect").
job("Aletha Nicolas", "health and safety inspector").
job("Anthony Nicolas", "medical secretary").
job("Barney Langley", "careers adviser").
job("Bradford Nicolas", "civil service administrator").
job("Carrol Nicolas", "optometrist").
job("Cherry Nicolas", "print production planner").
job("Connie Nicolas", "arboriculturist").
job("Dwayne Langley", "adult nurse").
job("Edythe Nicolas", "commercial horticulturist").
job("Eldon Nicolas", "conference centre manager").
job("Errol Brook", "journalist").
job("Eula Crain", "wellsite geologist").
job("Lera Brook", "community education officer").
job("Lucas Crain", "investment analyst").
job("Marilyn Nicolas", "trading standards officer").
job("Phylis Nicolas", "colour technologist").
job("Preston Francois", "immigration officer").
job("Rosalinda Francois", "human resources officer").
job("Rubye Crain", "agricultural consultant").
job("Rufus Brook", "fashion designer").
job("Sha Langley", "actuary").
job("Theodore Crain", "industrial designer").
job("Thurman Crain", "maintenance engineer").
job("Ulysses Nicolas", "data scientist").
job("Yoshiko Crain", "health physicist").
job("Zulema Crain", "hospital doctor").
job("Carey Mckenna", "radiographer").
job("Chuck Lizotte", "midwife").
job("Dwain Lizotte", "music therapist").
job("Hanh Mohan", "medical secretary").
job("Harold Wilkie", "hospital pharmacist").
job("Hoa Skaggs", "chemist").
job("Jarrod Mohan", "editor").
job("Jeannine Skaggs", "technical brewer").
job("Kirk Petry", "hospital pharmacist").
job("Lila Petry", "learning disability nurse").
job("Lucas Mckenna", "financial manager").
job("Maranda Lizotte", "chief executive officer").
job("Margot Skaggs", "programme researcher").
job("Minerva Wilkie", "printmaker").
job("Nathanial Lizotte", "sports coach").
job("Odis Lizotte", "trading standards officer").
job("Ora Lizotte", "physiological scientist").
job("Reyna Petry", "immunologist").
job("Rolland Mckenna", "advice worker").
job("Rosendo Skaggs", "ambulance person").
job("Rosina Lizotte", "tourism officer").
job("Shirley Skaggs", "solicitor").
job("Weldon Skaggs", "insurance account manager").
job("Windy Mckenna", "police officer").
job("Yoko Wilkie", "quantity surveyor").
job("Ashely Kee", "building services engineer").
job("Benton Earnest", "futures trader").
job("Calvin Woodman", "prison officer").
job("Cherise Earnest", "web designer").
job("Dane Kee", "therapeutic radiographer").
job("Duncan Pannell", "planning and development surveyor").
job("Edmond Schreiner", "neurosurgeon").
job("Eduardo Earnest", "sports administrator").
job("Edythe Earnest", "quarry manager").
job("Geri Woodman", "homeopath").
job("Hazel Earnest", "psychiatrist").
job("Ian Pannell", "wellsite geologist").
job("Ivory Pannell", "historic buildings inspector").
job("Johnnie Pannell", "rural practice surveyor").
job("Kristi Schreiner", "meteorologist").
job("Lanny Pannell", "farm manager").
job("Maria Earnest", "minerals surveyor").
job("Mickey Earnest", "textile designer").
job("Mona Pannell", "teaching laboratory technician").
job("Quincy Pannell", "meteorologist").
job("Randell Pannell", "insurance broker").
job("Reggie Earnest", "early years teacher").
job("Roland Earnest", "curator").
job("Ron Woodman", "furniture designer").
job("Samantha Earnest", "risk analyst").
job("Tamala Pannell", "museum exhibitions officer").
job("Adalberto Cedillo", "pilot").
job("Alberta Abraham", "human resources officer").
job("Aurelio Wasserman", "public relations officer").
job("Bee Cedillo", "solicitor").
job("Dillon Abraham", "broadcast engineer").
job("Domonique Cedillo", "chiropractor").
job("Elissa Cedillo", "statistician").
job("Elsy Hornback", "musician").
job("Gerardo Hornback", "economist").
job("Jimmy Cedillo", "company secretary").
job("Karla Hornback", "editorial assistant").
job("Kasey Cedillo", "transport planner").
job("Lorine Wasserman", "customer service manager").
job("Lucienne Cedillo", "camera operator").
job("Luisa Hornback", "psychotherapist").
job("Murray Cedillo", "scientific laboratory technician").
job("Ned Cedillo", "travel agency manager").
job("Oliver Abraham", "geologist").
job("Reinaldo Hornback", "soil scientist").
job("Ron Cedillo", "optometrist").
job("Shanda Wasserman", "banker").
job("Shirleen Abraham", "media buyer").
job("Stuart Abraham", "careers adviser").
job("Taneka Abraham", "garment technologist").
job("Yvette Cedillo", "advertising art director").
job("Ali Schoonmaker", "market researcher").
job("Anibal Schoonmaker", "IT consultant").
job("Annabelle Schoonmaker", "probation officer").
job("Blair Etheridge", "marketing executive").
job("Cary Etheridge", "investment banker").
job("Effie Schoonmaker", "product development scientist").
job("Enoch Palermo", "museum curator").
job("Esteban Schoonmaker", "sales professional").
job("Ester Palermo", "charity officer").
job("Francisco Palermo", "charity fundraiser").
job("Hannah Palermo", "insurance account manager").
job("Joel Palermo", "chartered certified accountant").
job("Jona Carrell", "environmental education officer").
job("Liane Schoonmaker", "chemist").
job("Madelyn Palermo", "research officer").
job("Malik Loftus", "dispensing optician").
job("Monique Palermo", "operations geologist").
job("Ofelia Carrell", "chartered loss adjuster").
job("Rigoberto Carrell", "bookseller").
job("Robyn Schoonmaker", "arts administrator").
job("Roman Palermo", "mining engineer").
job("Rosanna Palermo", "museum exhibitions officer").
job("Sylvia Palermo", "forensic scientist").
job("Tessie Loftus", "chief technology officer").
job("Zoraida Palermo", "fine artist").
job("Abraham Decosta", "pharmacologist").
job("Adolph Brannan", "training and development officer").
job("Carson Kovach", "operational investment banker").
job("Casey Brannan", "advertising copywriter").
job("Charlie Kovach", "probation officer").
job("Daniel Brannan", "bookseller").
job("Deborah Brannan", "public relations account executive").
job("Elissa Kovach", "academic librarian").
job("Elwood Decosta", "editorial assistant").
job("Ester Kovach", "product designer").
job("Everett Kovach", "accountant").
job("Jacques Decosta", "comptroller").
job("Jules Levy", "naval architect").
job("Laura Kovach", "corporate investment banker").
job("Laurel Decosta", "midwife").
job("Laverna Kovach", "claims inspector").
job("Lea Levy", "telecommunications researcher").
job("Marcel Brannan", "chartered public finance accountant").
job("Margaret Kovach", "advertising art director").
job("Margo Brannan", "clinical cytogeneticist").
job("Niesha Decosta", "immunologist").
job("Pasquale Levy", "economist").
job("Rosalinda Brannan", "adult guidance worker").
job("Stuart Decosta", "radio producer").
job("Zoila Decosta", "database administrator").
job("Bruce Mason", "paramedic").
job("Bryant Bradberry", "air traffic controller").
job("Chelsie Bradberry", "call centre manager").
job("Clarence Mason", "network engineer").
job("Clayton Shirk", "astronomer").
job("Craig Boutte", "astronomer").
job("Darin Shirk", "tax adviser").
job("Elton Griffiths", "hospital doctor").
job("Freddy Shirk", "research officer").
job("Hanh Boutte", "learning disability nurse").
job("Hilton Griffiths", "electronics engineer").
job("Jame Shirk", "financial adviser").
job("Johnathan Boutte", "print production planner").
job("Joslyn Mason", "chief executive officer").
job("Kevin Boutte", "contracting civil engineer").
job("Lauretta Mason", "oceanographer").
job("Marlana Boutte", "trading standards officer").
job("Maurine Shirk", "call centre manager").
job("Mercedes Shirk", "forensic scientist").
job("Monique Griffiths", "financial adviser").
job("Nada Shirk", "geographical information systems officer").
job("Olivia Griffiths", "planning and development surveyor").
job("Roger Griffiths", "outdoor activities manager").
job("Spencer Griffiths", "financial adviser").
job("Zoila Mason", "civil service administrator").

great_uncle(X, Y) :-
    grandparent(X, A),
    brother(A, Y).

:- dynamic message_hook/3.
:- multifile message_hook/3.


:- dynamic expand_query/4.
:- multifile expand_query/4.


:- multifile prolog_clause_name/2.


grandchild(X, Y) :-
    grandparent(Y, X).

:- dynamic dob/2.

dob("Aida Wang", "0295-05-30").
dob("Alison Smock", "0239-10-28").
dob("Alvaro Smock", "0177-07-12").
dob("Aubrey Smock", "0200-10-27").
dob("Brian Beltran", "0237-07-27").
dob("Daisy Beltran", "0241-09-21").
dob("Deane Smock", "0204-03-12").
dob("Dino Beltran", "0268-08-09").
dob("Dominique Smock", "0207-09-08").
dob("Gene Smock", "0208-08-16").
dob("Isabell Smock", "0211-01-18").
dob("Jeannine Wexler", "0299-06-11").
dob("Johnetta Wang", "0324-07-03").
dob("Lannie Smock", "0177-08-24").
dob("Leeann Hackworth", "0321-10-24").
dob("Lenore Hackworth", "0325-11-20").
dob("Myrle Smock", "0269-03-21").
dob("Orlando Beltran", "0263-10-24").
dob("Ricardo Hackworth", "0293-02-24").
dob("Ryan Wang", "0292-03-17").
dob("Saul Wexler", "0301-10-24").
dob("Shelli Beltran", "0268-03-07").
dob("Valentina Wexler", "0326-06-13").
dob("Vicki Hackworth", "0295-05-30").
dob("Williams Smock", "0236-04-04").
dob("Alberto Saari", "0289-06-06").
dob("Alycia Cormier", "0183-01-13").
dob("Andy Clemons", "0203-08-06").
dob("Bert Deluna", "0155-04-02").
dob("Christoper Cormier", "0181-01-08").
dob("Clifford Cormier", "0258-09-07").
dob("Deborah Cormier", "0262-06-04").
dob("Dion Cormier", "0233-08-20").
dob("Earle Cormier", "0228-12-24").
dob("Ella Saari", "0289-12-11").
dob("Foster Cormier", "0204-12-10").
dob("Geri Deluna", "0156-05-03").
dob("Hunter Saari", "0231-01-11").
dob("Jeana Clemons", "0203-12-20").
dob("Julia Cormier", "0228-12-06").
dob("Leann Cormier", "0283-09-15").
dob("Leda Cormier", "0204-08-23").
dob("Ming Cormier", "0231-01-26").
dob("Patsy Cormier", "0150-04-21").
dob("Shawnta Saari", "0263-07-16").
dob("Sherry Cormier", "0231-03-14").
dob("Sol Cormier", "0153-07-18").
dob("Therese Cormier", "0254-07-10").
dob("Trevor Saari", "0261-02-26").
dob("Virgie Saari", "0229-10-28").
dob("Amanda Mcnew", "0311-02-11").
dob("Amberly Mcnew", "0369-04-29").
dob("Caleb Haber", "0226-05-12").
dob("Cole Mcnew", "0308-06-30").
dob("Don Mcnew", "0280-09-16").
dob("Dudley Wise", "0313-03-18").
dob("Ernesto Mcnew", "0336-09-16").
dob("Garry Mcnew", "0333-09-23").
dob("Goldie Henderson", "0279-09-05").
dob("Hayden Mcnew", "0335-10-03").
dob("Haywood Mcnew", "0340-12-18").
dob("Jacinta Wise", "0313-04-10").
dob("Jeanelle Mcnew", "0305-06-19").
dob("Jung Henderson", "0225-04-26").
dob("Kris Haber", "0226-05-19").
dob("Lorelei Mcnew", "0279-09-05").
dob("Marcelino Mcnew", "0311-12-14").
dob("Marko Henderson", "0225-01-07").
dob("Maxwell Henderson", "0251-06-10").
dob("Merrill Mcnew", "0310-10-20").
dob("Milton Henderson", "0252-12-19").
dob("Noelia Henderson", "0250-04-09").
dob("Rae Mcnew", "0343-09-09").
dob("Roxy Mcnew", "0308-04-09").
dob("Stefan Henderson", "0249-01-06").
dob("Aletha Nicolas", "0274-07-08").
dob("Anthony Nicolas", "0272-06-08").
dob("Barney Langley", "0296-11-08").
dob("Bradford Nicolas", "0276-06-18").
dob("Carrol Nicolas", "0302-06-14").
dob("Cherry Nicolas", "0245-08-28").
dob("Connie Nicolas", "0301-02-09").
dob("Dwayne Langley", "0322-07-02").
dob("Edythe Nicolas", "0273-10-10").
dob("Eldon Nicolas", "0298-11-15").
dob("Errol Brook", "0321-08-06").
dob("Eula Crain", "0272-12-21").
dob("Lera Brook", "0294-01-23").
dob("Lucas Crain", "0272-01-09").
dob("Marilyn Nicolas", "0298-11-15").
dob("Phylis Nicolas", "0274-06-06").
dob("Preston Francois", "0267-11-18").
dob("Rosalinda Francois", "0268-01-19").
dob("Rubye Crain", "0302-01-19").
dob("Rufus Brook", "0293-11-12").
dob("Sha Langley", "0295-10-01").
dob("Theodore Crain", "0244-06-10").
dob("Thurman Crain", "0271-03-06").
dob("Ulysses Nicolas", "0245-06-16").
dob("Yoshiko Crain", "0247-02-23").
dob("Zulema Crain", "0279-12-05").
dob("Carey Mckenna", "0270-10-18").
dob("Chuck Lizotte", "0294-09-02").
dob("Dwain Lizotte", "0269-09-19").
dob("Hanh Mohan", "0293-04-14").
dob("Harold Wilkie", "0298-08-04").
dob("Hoa Skaggs", "0332-08-05").
dob("Jarrod Mohan", "0296-07-06").
dob("Jeannine Skaggs", "0303-04-19").
dob("Kirk Petry", "0265-12-24").
dob("Lila Petry", "0295-02-15").
dob("Lucas Mckenna", "0296-07-04").
dob("Maranda Lizotte", "0294-09-02").
dob("Margot Skaggs", "0328-02-10").
dob("Minerva Wilkie", "0324-04-23").
dob("Nathanial Lizotte", "0297-06-03").
dob("Odis Lizotte", "0240-02-05").
dob("Ora Lizotte", "0238-10-27").
dob("Reyna Petry", "0264-01-28").
dob("Rolland Mckenna", "0302-01-12").
dob("Rosendo Skaggs", "0329-04-09").
dob("Rosina Lizotte", "0266-10-24").
dob("Shirley Skaggs", "0356-03-30").
dob("Weldon Skaggs", "0306-02-25").
dob("Windy Mckenna", "0267-06-05").
dob("Yoko Wilkie", "0300-02-20").
dob("Ashely Kee", "0230-04-26").
dob("Benton Earnest", "0316-05-28").
dob("Calvin Woodman", "0348-05-23").
dob("Cherise Earnest", "0341-10-15").
dob("Dane Kee", "0232-07-25").
dob("Duncan Pannell", "0234-12-03").
dob("Edmond Schreiner", "0205-10-24").
dob("Eduardo Earnest", "0347-03-03").
dob("Edythe Earnest", "0349-05-12").
dob("Geri Woodman", "0315-01-26").
dob("Hazel Earnest", "0258-05-28").
dob("Ian Pannell", "0291-11-08").
dob("Ivory Pannell", "0257-12-23").
dob("Johnnie Pannell", "0289-11-01").
dob("Kristi Schreiner", "0203-03-20").
dob("Lanny Pannell", "0261-11-17").
dob("Maria Earnest", "0285-09-04").
dob("Mickey Earnest", "0258-03-16").
dob("Mona Pannell", "0231-08-24").
dob("Quincy Pannell", "0320-03-05").
dob("Randell Pannell", "0207-06-09").
dob("Reggie Earnest", "0348-06-30").
dob("Roland Earnest", "0285-01-09").
dob("Ron Woodman", "0316-12-15").
dob("Samantha Earnest", "0318-07-16").
dob("Tamala Pannell", "0208-02-03").
dob("Adalberto Cedillo", "0300-05-18").
dob("Alberta Abraham", "0241-01-22").
dob("Aurelio Wasserman", "0250-05-01").
dob("Bee Cedillo", "0252-01-02").
dob("Dillon Abraham", "0244-12-22").
dob("Domonique Cedillo", "0271-10-05").
dob("Elissa Cedillo", "0295-04-26").
dob("Elsy Hornback", "0222-07-07").
dob("Gerardo Hornback", "0192-01-19").
dob("Jimmy Cedillo", "0332-12-16").
dob("Karla Hornback", "0190-10-06").
dob("Kasey Cedillo", "0273-02-08").
dob("Lorine Wasserman", "0250-09-12").
dob("Lucienne Cedillo", "0301-03-22").
dob("Luisa Hornback", "0213-12-12").
dob("Murray Cedillo", "0330-03-22").
dob("Ned Cedillo", "0249-07-28").
dob("Oliver Abraham", "0213-12-20").
dob("Reinaldo Hornback", "0221-09-19").
dob("Ron Cedillo", "0303-03-21").
dob("Shanda Wasserman", "0276-02-21").
dob("Shirleen Abraham", "0248-01-02").
dob("Stuart Abraham", "0239-05-21").
dob("Taneka Abraham", "0213-08-11").
dob("Yvette Cedillo", "0324-03-05").
dob("Ali Schoonmaker", "0234-07-25").
dob("Anibal Schoonmaker", "0263-08-17").
dob("Annabelle Schoonmaker", "0260-10-17").
dob("Blair Etheridge", "0288-08-04").
dob("Cary Etheridge", "0287-07-19").
dob("Effie Schoonmaker", "0259-07-27").
dob("Enoch Palermo", "0311-09-01").
dob("Esteban Schoonmaker", "0259-12-15").
dob("Ester Palermo", "0337-06-12").
dob("Francisco Palermo", "0340-08-15").
dob("Hannah Palermo", "0339-01-11").
dob("Joel Palermo", "0366-02-03").
dob("Jona Carrell", "0263-06-16").
dob("Liane Schoonmaker", "0262-07-13").
dob("Madelyn Palermo", "0368-06-16").
dob("Malik Loftus", "0309-01-05").
dob("Monique Palermo", "0341-01-09").
dob("Ofelia Carrell", "0286-06-15").
dob("Rigoberto Carrell", "0263-02-06").
dob("Robyn Schoonmaker", "0234-12-15").
dob("Roman Palermo", "0366-12-18").
dob("Rosanna Palermo", "0337-08-25").
dob("Sylvia Palermo", "0313-09-16").
dob("Tessie Loftus", "0313-01-17").
dob("Zoraida Palermo", "0371-01-07").
dob("Abraham Decosta", "0217-07-23").
dob("Adolph Brannan", "0224-12-03").
dob("Carson Kovach", "0284-07-07").
dob("Casey Brannan", "0160-12-14").
dob("Charlie Kovach", "0277-07-02").
dob("Daniel Brannan", "0254-01-20").
dob("Deborah Brannan", "0160-02-03").
dob("Elissa Kovach", "0279-06-27").
dob("Elwood Decosta", "0189-04-06").
dob("Ester Kovach", "0277-05-15").
dob("Everett Kovach", "0251-07-20").
dob("Jacques Decosta", "0183-08-20").
dob("Jules Levy", "0258-01-19").
dob("Laura Kovach", "0305-04-28").
dob("Laurel Decosta", "0186-12-01").
dob("Laverna Kovach", "0282-09-16").
dob("Lea Levy", "0256-04-20").
dob("Marcel Brannan", "0195-07-20").
dob("Margaret Kovach", "0252-01-08").
dob("Margo Brannan", "0192-09-26").
dob("Niesha Decosta", "0188-11-25").
dob("Pasquale Levy", "0289-04-03").
dob("Rosalinda Brannan", "0227-05-14").
dob("Stuart Decosta", "0162-09-10").
dob("Zoila Decosta", "0159-09-14").
dob("Bruce Mason", "0286-10-11").
dob("Bryant Bradberry", "0189-07-04").
dob("Chelsie Bradberry", "0191-10-28").
dob("Clarence Mason", "0252-09-27").
dob("Clayton Shirk", "0240-04-24").
dob("Craig Boutte", "0318-06-06").
dob("Darin Shirk", "0264-05-03").
dob("Elton Griffiths", "0264-12-04").
dob("Freddy Shirk", "0287-04-28").
dob("Hanh Boutte", "0261-03-02").
dob("Hilton Griffiths", "0314-02-19").
dob("Jame Shirk", "0216-03-27").
dob("Johnathan Boutte", "0292-04-16").
dob("Joslyn Mason", "0249-10-17").
dob("Kevin Boutte", "0264-08-18").
dob("Lauretta Mason", "0289-07-10").
dob("Marlana Boutte", "0293-08-27").
dob("Maurine Shirk", "0217-01-03").
dob("Mercedes Shirk", "0262-04-11").
dob("Monique Griffiths", "0287-04-22").
dob("Nada Shirk", "0237-06-02").
dob("Olivia Griffiths", "0266-03-04").
dob("Roger Griffiths", "0313-04-21").
dob("Spencer Griffiths", "0288-01-14").
dob("Zoila Mason", "0325-07-05").

:- thread_local thread_message_hook/3.
:- dynamic thread_message_hook/3.
:- volatile thread_message_hook/3.

%   No thread has clauses for thread_message_hook/3

:- dynamic type/2.

type("Aida Wang", person).
type("Alison Smock", person).
type("Alvaro Smock", person).
type("Aubrey Smock", person).
type("Brian Beltran", person).
type("Daisy Beltran", person).
type("Deane Smock", person).
type("Dino Beltran", person).
type("Dominique Smock", person).
type("Gene Smock", person).
type("Isabell Smock", person).
type("Jeannine Wexler", person).
type("Johnetta Wang", person).
type("Lannie Smock", person).
type("Leeann Hackworth", person).
type("Lenore Hackworth", person).
type("Myrle Smock", person).
type("Orlando Beltran", person).
type("Ricardo Hackworth", person).
type("Ryan Wang", person).
type("Saul Wexler", person).
type("Shelli Beltran", person).
type("Valentina Wexler", person).
type("Vicki Hackworth", person).
type("Williams Smock", person).
type("Alberto Saari", person).
type("Alycia Cormier", person).
type("Andy Clemons", person).
type("Bert Deluna", person).
type("Christoper Cormier", person).
type("Clifford Cormier", person).
type("Deborah Cormier", person).
type("Dion Cormier", person).
type("Earle Cormier", person).
type("Ella Saari", person).
type("Foster Cormier", person).
type("Geri Deluna", person).
type("Hunter Saari", person).
type("Jeana Clemons", person).
type("Julia Cormier", person).
type("Leann Cormier", person).
type("Leda Cormier", person).
type("Ming Cormier", person).
type("Patsy Cormier", person).
type("Shawnta Saari", person).
type("Sherry Cormier", person).
type("Sol Cormier", person).
type("Therese Cormier", person).
type("Trevor Saari", person).
type("Virgie Saari", person).
type("Amanda Mcnew", person).
type("Amberly Mcnew", person).
type("Caleb Haber", person).
type("Cole Mcnew", person).
type("Don Mcnew", person).
type("Dudley Wise", person).
type("Ernesto Mcnew", person).
type("Garry Mcnew", person).
type("Goldie Henderson", person).
type("Hayden Mcnew", person).
type("Haywood Mcnew", person).
type("Jacinta Wise", person).
type("Jeanelle Mcnew", person).
type("Jung Henderson", person).
type("Kris Haber", person).
type("Lorelei Mcnew", person).
type("Marcelino Mcnew", person).
type("Marko Henderson", person).
type("Maxwell Henderson", person).
type("Merrill Mcnew", person).
type("Milton Henderson", person).
type("Noelia Henderson", person).
type("Rae Mcnew", person).
type("Roxy Mcnew", person).
type("Stefan Henderson", person).
type("Aletha Nicolas", person).
type("Anthony Nicolas", person).
type("Barney Langley", person).
type("Bradford Nicolas", person).
type("Carrol Nicolas", person).
type("Cherry Nicolas", person).
type("Connie Nicolas", person).
type("Dwayne Langley", person).
type("Edythe Nicolas", person).
type("Eldon Nicolas", person).
type("Errol Brook", person).
type("Eula Crain", person).
type("Lera Brook", person).
type("Lucas Crain", person).
type("Marilyn Nicolas", person).
type("Phylis Nicolas", person).
type("Preston Francois", person).
type("Rosalinda Francois", person).
type("Rubye Crain", person).
type("Rufus Brook", person).
type("Sha Langley", person).
type("Theodore Crain", person).
type("Thurman Crain", person).
type("Ulysses Nicolas", person).
type("Yoshiko Crain", person).
type("Zulema Crain", person).
type("Carey Mckenna", person).
type("Chuck Lizotte", person).
type("Dwain Lizotte", person).
type("Hanh Mohan", person).
type("Harold Wilkie", person).
type("Hoa Skaggs", person).
type("Jarrod Mohan", person).
type("Jeannine Skaggs", person).
type("Kirk Petry", person).
type("Lila Petry", person).
type("Lucas Mckenna", person).
type("Maranda Lizotte", person).
type("Margot Skaggs", person).
type("Minerva Wilkie", person).
type("Nathanial Lizotte", person).
type("Odis Lizotte", person).
type("Ora Lizotte", person).
type("Reyna Petry", person).
type("Rolland Mckenna", person).
type("Rosendo Skaggs", person).
type("Rosina Lizotte", person).
type("Shirley Skaggs", person).
type("Weldon Skaggs", person).
type("Windy Mckenna", person).
type("Yoko Wilkie", person).
type("Ashely Kee", person).
type("Benton Earnest", person).
type("Calvin Woodman", person).
type("Cherise Earnest", person).
type("Dane Kee", person).
type("Duncan Pannell", person).
type("Edmond Schreiner", person).
type("Eduardo Earnest", person).
type("Edythe Earnest", person).
type("Geri Woodman", person).
type("Hazel Earnest", person).
type("Ian Pannell", person).
type("Ivory Pannell", person).
type("Johnnie Pannell", person).
type("Kristi Schreiner", person).
type("Lanny Pannell", person).
type("Maria Earnest", person).
type("Mickey Earnest", person).
type("Mona Pannell", person).
type("Quincy Pannell", person).
type("Randell Pannell", person).
type("Reggie Earnest", person).
type("Roland Earnest", person).
type("Ron Woodman", person).
type("Samantha Earnest", person).
type("Tamala Pannell", person).
type("Adalberto Cedillo", person).
type("Alberta Abraham", person).
type("Aurelio Wasserman", person).
type("Bee Cedillo", person).
type("Dillon Abraham", person).
type("Domonique Cedillo", person).
type("Elissa Cedillo", person).
type("Elsy Hornback", person).
type("Gerardo Hornback", person).
type("Jimmy Cedillo", person).
type("Karla Hornback", person).
type("Kasey Cedillo", person).
type("Lorine Wasserman", person).
type("Lucienne Cedillo", person).
type("Luisa Hornback", person).
type("Murray Cedillo", person).
type("Ned Cedillo", person).
type("Oliver Abraham", person).
type("Reinaldo Hornback", person).
type("Ron Cedillo", person).
type("Shanda Wasserman", person).
type("Shirleen Abraham", person).
type("Stuart Abraham", person).
type("Taneka Abraham", person).
type("Yvette Cedillo", person).
type("Ali Schoonmaker", person).
type("Anibal Schoonmaker", person).
type("Annabelle Schoonmaker", person).
type("Blair Etheridge", person).
type("Cary Etheridge", person).
type("Effie Schoonmaker", person).
type("Enoch Palermo", person).
type("Esteban Schoonmaker", person).
type("Ester Palermo", person).
type("Francisco Palermo", person).
type("Hannah Palermo", person).
type("Joel Palermo", person).
type("Jona Carrell", person).
type("Liane Schoonmaker", person).
type("Madelyn Palermo", person).
type("Malik Loftus", person).
type("Monique Palermo", person).
type("Ofelia Carrell", person).
type("Rigoberto Carrell", person).
type("Robyn Schoonmaker", person).
type("Roman Palermo", person).
type("Rosanna Palermo", person).
type("Sylvia Palermo", person).
type("Tessie Loftus", person).
type("Zoraida Palermo", person).
type("Abraham Decosta", person).
type("Adolph Brannan", person).
type("Carson Kovach", person).
type("Casey Brannan", person).
type("Charlie Kovach", person).
type("Daniel Brannan", person).
type("Deborah Brannan", person).
type("Elissa Kovach", person).
type("Elwood Decosta", person).
type("Ester Kovach", person).
type("Everett Kovach", person).
type("Jacques Decosta", person).
type("Jules Levy", person).
type("Laura Kovach", person).
type("Laurel Decosta", person).
type("Laverna Kovach", person).
type("Lea Levy", person).
type("Marcel Brannan", person).
type("Margaret Kovach", person).
type("Margo Brannan", person).
type("Niesha Decosta", person).
type("Pasquale Levy", person).
type("Rosalinda Brannan", person).
type("Stuart Decosta", person).
type("Zoila Decosta", person).
type("Bruce Mason", person).
type("Bryant Bradberry", person).
type("Chelsie Bradberry", person).
type("Clarence Mason", person).
type("Clayton Shirk", person).
type("Craig Boutte", person).
type("Darin Shirk", person).
type("Elton Griffiths", person).
type("Freddy Shirk", person).
type("Hanh Boutte", person).
type("Hilton Griffiths", person).
type("Jame Shirk", person).
type("Johnathan Boutte", person).
type("Joslyn Mason", person).
type("Kevin Boutte", person).
type("Lauretta Mason", person).
type("Marlana Boutte", person).
type("Maurine Shirk", person).
type("Mercedes Shirk", person).
type("Monique Griffiths", person).
type("Nada Shirk", person).
type("Olivia Griffiths", person).
type("Roger Griffiths", person).
type("Spencer Griffiths", person).
type("Zoila Mason", person).

grandfather(X, Y) :-
    grandparent(X, Y),
    male(Y).

:- dynamic attribute/1.

attribute("personal assistant").
attribute("meditation").
attribute("health promotion specialist").
attribute("meteorology").
attribute("osteopath").
attribute("biology").
attribute("broadcast engineer").
attribute("meteorology").
attribute("oncologist").
attribute("dolls").
attribute("warehouse manager").
attribute("photography").
attribute("associate professor").
attribute("shogi").
attribute("sports therapist").
attribute("dominoes").
attribute("retail manager").
attribute("tether car").
attribute("immunologist").
attribute("architecture").
attribute("education administrator").
attribute("geocaching").
attribute("early years teacher").
attribute("trainspotting").
attribute("biomedical scientist").
attribute("bus spotting").
attribute("music tutor").
attribute("research").
attribute("clinical cytogeneticist").
attribute("geography").
attribute("ecologist").
attribute("microbiology").
attribute("barrister's clerk").
attribute("canoeing").
attribute("petroleum engineer").
attribute("learning").
attribute("clinical research associate").
attribute("dairy farming").
attribute("chief of staff").
attribute("fossil hunting").
attribute("occupational therapist").
attribute("sociology").
attribute("actuary").
attribute("finance").
attribute("police officer").
attribute("meditation").
attribute("sound technician").
attribute("wikipedia editing").
attribute("theatre manager").
attribute("radio-controlled car racing").
attribute("clinical biochemist").
attribute("social studies").
attribute("public relations officer").
attribute("judo").
attribute("music therapist").
attribute("flying disc").
attribute("librarian").
attribute("cricket").
attribute("building surveyor").
attribute("weightlifting").
attribute("fitness centre manager").
attribute("meditation").
attribute("oceanographer").
attribute("ballroom dancing").
attribute("historic buildings inspector").
attribute("microscopy").
attribute("chief marketing officer").
attribute("reading").
attribute("waste management officer").
attribute("laser tag").
attribute("medical sales representative").
attribute("hiking/backpacking").
attribute("community pharmacist").
attribute("audiophile").
attribute("pension scheme manager").
attribute("tennis polo").
attribute("armed forces logistics officer").
attribute("photography").
attribute("environmental education officer").
attribute("backgammon").
attribute("medical illustrator").
attribute("microscopy").
attribute("museum conservator").
attribute("herping").
attribute("optometrist").
attribute("philately").
attribute("further education lecturer").
attribute("birdwatching").
attribute("dancer").
attribute("shogi").
attribute("water engineer").
attribute("magnet fishing").
attribute("intelligence analyst").
attribute("table tennis").
attribute("fashion designer").
attribute("scuba diving").
attribute("doctor").
attribute("biology").
attribute("chartered accountant").
attribute("sea glass collecting").
attribute("speech and language therapist").
attribute("research").
attribute("clinical embryologist").
attribute("gongoozling").
attribute("community development worker").
attribute("benchmarking").
attribute("games developer").
attribute("sea glass collecting").
attribute("accommodation manager").
attribute("bowling").
attribute("conservation officer").
attribute("audiophile").
attribute("forensic scientist").
attribute("tea bag collecting").
attribute("pharmacologist").
attribute("model aircraft").
attribute("dance movement psychotherapist").
attribute("herping").
attribute("paediatric nurse").
attribute("figure skating").
attribute("research officer").
attribute("fossil hunting").
attribute("production designer").
attribute("airsoft").
attribute("community development worker").
attribute("whale watching").
attribute("clinical molecular geneticist").
attribute("pinball").
attribute("set designer").
attribute("research").
attribute("town planner").
attribute("flying model planes").
attribute("print production planner").
attribute("ant farming").
attribute("equality and diversity officer").
attribute("volleyball").
attribute("chartered loss adjuster").
attribute("gongoozling").
attribute("sales promotion account executive").
attribute("vehicle restoration").
attribute("banker").
attribute("car riding").
attribute("systems developer").
attribute("mycology").
attribute("chief financial officer").
attribute("table football").
attribute("regulatory affairs officer").
attribute("photography").
attribute("architect").
attribute("metal detecting").
attribute("health and safety inspector").
attribute("archery").
attribute("medical secretary").
attribute("reading").
attribute("careers adviser").
attribute("shortwave listening").
attribute("civil service administrator").
attribute("snowmobiling").
attribute("optometrist").
attribute("research").
attribute("print production planner").
attribute("religious studies").
attribute("arboriculturist").
attribute("cooking").
attribute("adult nurse").
attribute("kart racing").
attribute("commercial horticulturist").
attribute("darts").
attribute("conference centre manager").
attribute("herping").
attribute("journalist").
attribute("backgammon").
attribute("wellsite geologist").
attribute("herping").
attribute("community education officer").
attribute("ant farming").
attribute("investment analyst").
attribute("ephemera collecting").
attribute("trading standards officer").
attribute("bus spotting").
attribute("colour technologist").
attribute("research").
attribute("immigration officer").
attribute("croquet").
attribute("human resources officer").
attribute("leaves").
attribute("agricultural consultant").
attribute("antiquities").
attribute("fashion designer").
attribute("field hockey").
attribute("actuary").
attribute("leaves").
attribute("industrial designer").
attribute("auto audiophilia").
attribute("maintenance engineer").
attribute("magic").
attribute("data scientist").
attribute("people-watching").
attribute("health physicist").
attribute("social studies").
attribute("hospital doctor").
attribute("mineral collecting").
attribute("radiographer").
attribute("fusilately").
attribute("midwife").
attribute("surfing").
attribute("music therapist").
attribute("magic").
attribute("medical secretary").
attribute("story writing").
attribute("hospital pharmacist").
attribute("curling").
attribute("chemist").
attribute("museum visiting").
attribute("editor").
attribute("benchmarking").
attribute("technical brewer").
attribute("meteorology").
attribute("hospital pharmacist").
attribute("entrepreneurship").
attribute("learning disability nurse").
attribute("deltiology").
attribute("financial manager").
attribute("badminton").
attribute("chief executive officer").
attribute("flag football").
attribute("programme researcher").
attribute("shooting").
attribute("printmaker").
attribute("rock tumbling").
attribute("sports coach").
attribute("beekeeping").
attribute("trading standards officer").
attribute("ephemera collecting").
attribute("physiological scientist").
attribute("medical science").
attribute("immunologist").
attribute("microscopy").
attribute("advice worker").
attribute("leaves").
attribute("ambulance person").
attribute("philately").
attribute("tourism officer").
attribute("research").
attribute("solicitor").
attribute("horseshoes").
attribute("insurance account manager").
attribute("insect collecting").
attribute("police officer").
attribute("fencing").
attribute("quantity surveyor").
attribute("insect collecting").
attribute("building services engineer").
attribute("book collecting").
attribute("futures trader").
attribute("business").
attribute("prison officer").
attribute("fishkeeping").
attribute("web designer").
attribute("dolls").
attribute("therapeutic radiographer").
attribute("fitness").
attribute("planning and development surveyor").
attribute("paintball").
attribute("neurosurgeon").
attribute("vintage clothing").
attribute("sports administrator").
attribute("shuffleboard").
attribute("quarry manager").
attribute("sports memorabilia").
attribute("homeopath").
attribute("kart racing").
attribute("psychiatrist").
attribute("trapshooting").
attribute("wellsite geologist").
attribute("table tennis").
attribute("historic buildings inspector").
attribute("rock climbing").
attribute("rural practice surveyor").
attribute("gymnastics").
attribute("meteorologist").
attribute("auto audiophilia").
attribute("farm manager").
attribute("myrmecology").
attribute("minerals surveyor").
attribute("flower collecting and pressing").
attribute("textile designer").
attribute("baton twirling").
attribute("teaching laboratory technician").
attribute("metal detecting").
attribute("meteorologist").
attribute("radio-controlled model playing").
attribute("insurance broker").
attribute("fossicking").
attribute("early years teacher").
attribute("shopping").
attribute("curator").
attribute("satellite watching").
attribute("furniture designer").
attribute("carrier pigeons").
attribute("risk analyst").
attribute("publishing").
attribute("museum exhibitions officer").
attribute("learning").
attribute("pilot").
attribute("fishing").
attribute("human resources officer").
attribute("mini golf").
attribute("public relations officer").
attribute("beekeeping").
attribute("solicitor").
attribute("sailing").
attribute("broadcast engineer").
attribute("cycling").
attribute("chiropractor").
attribute("hobby horsing").
attribute("statistician").
attribute("dog walking").
attribute("musician").
attribute("life science").
attribute("economist").
attribute("leaves").
attribute("company secretary").
attribute("volleyball").
attribute("editorial assistant").
attribute("railway studies").
attribute("transport planner").
attribute("butterfly watching").
attribute("customer service manager").
attribute("magnet fishing").
attribute("camera operator").
attribute("insect collecting").
attribute("psychotherapist").
attribute("films").
attribute("scientific laboratory technician").
attribute("race walking").
attribute("travel agency manager").
attribute("dairy farming").
attribute("geologist").
attribute("wikipedia editing").
attribute("soil scientist").
attribute("kart racing").
attribute("optometrist").
attribute("people-watching").
attribute("banker").
attribute("whale watching").
attribute("media buyer").
attribute("shooting sports").
attribute("careers adviser").
attribute("debate").
attribute("garment technologist").
attribute("table tennis").
attribute("advertising art director").
attribute("archaeology").
attribute("market researcher").
attribute("lotology").
attribute("IT consultant").
attribute("stone collecting").
attribute("probation officer").
attribute("birdwatching").
attribute("marketing executive").
attribute("rock balancing").
attribute("investment banker").
attribute("karting").
attribute("product development scientist").
attribute("disc golf").
attribute("museum curator").
attribute("shortwave listening").
attribute("sales professional").
attribute("audiophile").
attribute("charity officer").
attribute("bus spotting").
attribute("charity fundraiser").
attribute("shortwave listening").
attribute("insurance account manager").
attribute("fishkeeping").
attribute("chartered certified accountant").
attribute("tea bag collecting").
attribute("environmental education officer").
attribute("phillumeny").
attribute("chemist").
attribute("stamp collecting").
attribute("research officer").
attribute("volleyball").
attribute("dispensing optician").
attribute("learning").
attribute("operations geologist").
attribute("shooting").
attribute("chartered loss adjuster").
attribute("audiophile").
attribute("bookseller").
attribute("knife collecting").
attribute("arts administrator").
attribute("learning").
attribute("mining engineer").
attribute("letterboxing").
attribute("museum exhibitions officer").
attribute("beekeeping").
attribute("forensic scientist").
attribute("bridge").
attribute("chief technology officer").
attribute("perfume").
attribute("fine artist").
attribute("films").
attribute("pharmacologist").
attribute("lacrosse").
attribute("training and development officer").
attribute("metal detecting").
attribute("operational investment banker").
attribute("speedcubing").
attribute("advertising copywriter").
attribute("scutelliphily").
attribute("probation officer").
attribute("psychology").
attribute("bookseller").
attribute("chess").
attribute("public relations account executive").
attribute("radio-controlled model playing").
attribute("academic librarian").
attribute("birdwatching").
attribute("editorial assistant").
attribute("antiquities").
attribute("product designer").
attribute("vehicle restoration").
attribute("accountant").
attribute("judo").
attribute("comptroller").
attribute("sea glass collecting").
attribute("naval architect").
attribute("neuroscience").
attribute("corporate investment banker").
attribute("whale watching").
attribute("midwife").
attribute("antiquities").
attribute("claims inspector").
attribute("croquet").
attribute("telecommunications researcher").
attribute("martial arts").
attribute("chartered public finance accountant").
attribute("microscopy").
attribute("advertising art director").
attribute("flower collecting and pressing").
attribute("clinical cytogeneticist").
attribute("publishing").
attribute("immunologist").
attribute("beekeeping").
attribute("economist").
attribute("table tennis").
attribute("adult guidance worker").
attribute("cornhole").
attribute("radio producer").
attribute("horseshoes").
attribute("database administrator").
attribute("flying disc").
attribute("paramedic").
attribute("ant farming").
attribute("air traffic controller").
attribute("architecture").
attribute("call centre manager").
attribute("ant farming").
attribute("network engineer").
attribute("cycling").
attribute("astronomer").
attribute("tennis polo").
attribute("astronomer").
attribute("fencing").
attribute("tax adviser").
attribute("vegetable farming").
attribute("hospital doctor").
attribute("vr gaming").
attribute("research officer").
attribute("sports memorabilia").
attribute("learning disability nurse").
attribute("martial arts").
attribute("electronics engineer").
attribute("mini golf").
attribute("financial adviser").
attribute("shortwave listening").
attribute("print production planner").
attribute("amusement park visiting").
attribute("chief executive officer").
attribute("aerospace").
attribute("contracting civil engineer").
attribute("rowing").
attribute("oceanographer").
attribute("book collecting").
attribute("trading standards officer").
attribute("pickleball").
attribute("call centre manager").
attribute("finance").
attribute("forensic scientist").
attribute("field hockey").
attribute("financial adviser").
attribute("birdwatching").
attribute("geographical information systems officer").
attribute("beach volleyball").
attribute("planning and development surveyor").
attribute("geocaching").
attribute("outdoor activities manager").
attribute("mineral collecting").
attribute("financial adviser").
attribute("psychology").
attribute("civil service administrator").
attribute("audiophile").

great_aunt(X, Y) :-
    grandparent(X, A),
    sister(A, Y).

grandparent(X, Y) :-
    parent(X, Z),
    parent(Z, Y).

:- dynamic library_directory/1.
:- multifile library_directory/1.


grandmother(X, Y) :-
    grandparent(X, Y),
    female(Y).

:- dynamic friend_/2.

friend_("Aida Wang", "Garry Mcnew").
friend_("Aida Wang", "Harold Wilkie").
friend_("Aida Wang", "Ora Lizotte").
friend_("Aida Wang", "Gerardo Hornback").
friend_("Aida Wang", "Taneka Abraham").
friend_("Alison Smock", "Ulysses Nicolas").
friend_("Alison Smock", "Nathanial Lizotte").
friend_("Alison Smock", "Liane Schoonmaker").
friend_("Alison Smock", "Chelsie Bradberry").
friend_("Alvaro Smock", "Daisy Beltran").
friend_("Alvaro Smock", "Murray Cedillo").
friend_("Alvaro Smock", "Jacques Decosta").
friend_("Aubrey Smock", "Trevor Saari").
friend_("Aubrey Smock", "Karla Hornback").
friend_("Aubrey Smock", "Murray Cedillo").
friend_("Aubrey Smock", "Laverna Kovach").
friend_("Brian Beltran", "Maxwell Henderson").
friend_("Brian Beltran", "Ashely Kee").
friend_("Brian Beltran", "Pasquale Levy").
friend_("Daisy Beltran", "Jeanelle Mcnew").
friend_("Daisy Beltran", "Jung Henderson").
friend_("Daisy Beltran", "Roland Earnest").
friend_("Daisy Beltran", "Aurelio Wasserman").
friend_("Deane Smock", "Maxwell Henderson").
friend_("Deane Smock", "Gerardo Hornback").
friend_("Dino Beltran", "Carey Mckenna").
friend_("Dominique Smock", "Margo Brannan").
friend_("Gene Smock", "Goldie Henderson").
friend_("Gene Smock", "Liane Schoonmaker").
friend_("Gene Smock", "Hilton Griffiths").
friend_("Johnetta Wang", "Geri Deluna").
friend_("Johnetta Wang", "Kris Haber").
friend_("Johnetta Wang", "Shanda Wasserman").
friend_("Lannie Smock", "Marcelino Mcnew").
friend_("Lannie Smock", "Randell Pannell").
friend_("Lannie Smock", "Ned Cedillo").
friend_("Leeann Hackworth", "Williams Smock").
friend_("Leeann Hackworth", "Dwayne Langley").
friend_("Leeann Hackworth", "Ron Cedillo").
friend_("Leeann Hackworth", "Charlie Kovach").
friend_("Lenore Hackworth", "Alberto Saari").
friend_("Lenore Hackworth", "Bradford Nicolas").
friend_("Lenore Hackworth", "Eula Crain").
friend_("Lenore Hackworth", "Chuck Lizotte").
friend_("Lenore Hackworth", "Kasey Cedillo").
friend_("Myrle Smock", "Ricardo Hackworth").
friend_("Myrle Smock", "Dion Cormier").
friend_("Myrle Smock", "Rosina Lizotte").
friend_("Myrle Smock", "Charlie Kovach").
friend_("Myrle Smock", "Monique Griffiths").
friend_("Orlando Beltran", "Christoper Cormier").
friend_("Orlando Beltran", "Ned Cedillo").
friend_("Ricardo Hackworth", "Cole Mcnew").
friend_("Ricardo Hackworth", "Kirk Petry").
friend_("Ricardo Hackworth", "Margo Brannan").
friend_("Ricardo Hackworth", "Craig Boutte").
friend_("Ryan Wang", "Noelia Henderson").
friend_("Saul Wexler", "Jules Levy").
friend_("Shelli Beltran", "Geri Deluna").
friend_("Shelli Beltran", "Milton Henderson").
friend_("Shelli Beltran", "Edmond Schreiner").
friend_("Valentina Wexler", "Andy Clemons").
friend_("Valentina Wexler", "Mona Pannell").
friend_("Valentina Wexler", "Reggie Earnest").
friend_("Vicki Hackworth", "Cherry Nicolas").
friend_("Vicki Hackworth", "Ora Lizotte").
friend_("Vicki Hackworth", "Yvette Cedillo").
friend_("Williams Smock", "Geri Deluna").
friend_("Williams Smock", "Ian Pannell").
friend_("Williams Smock", "Hannah Palermo").
friend_("Williams Smock", "Monique Palermo").
friend_("Alberto Saari", "Leann Cormier").
friend_("Alberto Saari", "Trevor Saari").
friend_("Alberto Saari", "Liane Schoonmaker").
friend_("Alberto Saari", "Tessie Loftus").
friend_("Alberto Saari", "Craig Boutte").
friend_("Alycia Cormier", "Bruce Mason").
friend_("Andy Clemons", "Shawnta Saari").
friend_("Andy Clemons", "Rufus Brook").
friend_("Andy Clemons", "Lila Petry").
friend_("Bert Deluna", "Shawnta Saari").
friend_("Christoper Cormier", "Johnathan Boutte").
friend_("Clifford Cormier", "Quincy Pannell").
friend_("Earle Cormier", "Leda Cormier").
friend_("Earle Cormier", "Zoraida Palermo").
friend_("Earle Cormier", "Chelsie Bradberry").
friend_("Earle Cormier", "Monique Griffiths").
friend_("Ella Saari", "Sherry Cormier").
friend_("Ella Saari", "Rae Mcnew").
friend_("Ella Saari", "Cherry Nicolas").
friend_("Ella Saari", "Edythe Earnest").
friend_("Foster Cormier", "Marcelino Mcnew").
friend_("Foster Cormier", "Mickey Earnest").
friend_("Foster Cormier", "Samantha Earnest").
friend_("Geri Deluna", "Edythe Nicolas").
friend_("Geri Deluna", "Lucas Crain").
friend_("Geri Deluna", "Gerardo Hornback").
friend_("Geri Deluna", "Taneka Abraham").
friend_("Geri Deluna", "Rosalinda Brannan").
friend_("Hunter Saari", "Thurman Crain").
friend_("Hunter Saari", "Quincy Pannell").
friend_("Hunter Saari", "Madelyn Palermo").
friend_("Hunter Saari", "Roman Palermo").
friend_("Hunter Saari", "Zoila Mason").
friend_("Jeana Clemons", "Eduardo Earnest").
friend_("Julia Cormier", "Dwain Lizotte").
friend_("Julia Cormier", "Margo Brannan").
friend_("Leann Cormier", "Hanh Mohan").
friend_("Leda Cormier", "Marilyn Nicolas").
friend_("Leda Cormier", "Esteban Schoonmaker").
friend_("Leda Cormier", "Sylvia Palermo").
friend_("Ming Cormier", "Marko Henderson").
friend_("Ming Cormier", "Elsy Hornback").
friend_("Ming Cormier", "Yvette Cedillo").
friend_("Patsy Cormier", "Lila Petry").
friend_("Patsy Cormier", "Kristi Schreiner").
friend_("Patsy Cormier", "Mickey Earnest").
friend_("Patsy Cormier", "Spencer Griffiths").
friend_("Shawnta Saari", "Hazel Earnest").
friend_("Sherry Cormier", "Lanny Pannell").
friend_("Sherry Cormier", "Mickey Earnest").
friend_("Sherry Cormier", "Jules Levy").
friend_("Sherry Cormier", "Marlana Boutte").
friend_("Sol Cormier", "Jeanelle Mcnew").
friend_("Sol Cormier", "Calvin Woodman").
friend_("Sol Cormier", "Mona Pannell").
friend_("Sol Cormier", "Kasey Cedillo").
friend_("Therese Cormier", "Geri Woodman").
friend_("Therese Cormier", "Hazel Earnest").
friend_("Therese Cormier", "Mickey Earnest").
friend_("Therese Cormier", "Lorine Wasserman").
friend_("Trevor Saari", "Johnnie Pannell").
friend_("Trevor Saari", "Mercedes Shirk").
friend_("Trevor Saari", "Nada Shirk").
friend_("Amanda Mcnew", "Ernesto Mcnew").
friend_("Amanda Mcnew", "Robyn Schoonmaker").
friend_("Amanda Mcnew", "Roman Palermo").
friend_("Amanda Mcnew", "Clayton Shirk").
friend_("Amberly Mcnew", "Jung Henderson").
friend_("Amberly Mcnew", "Roland Earnest").
friend_("Caleb Haber", "Rae Mcnew").
friend_("Caleb Haber", "Ivory Pannell").
friend_("Caleb Haber", "Quincy Pannell").
friend_("Caleb Haber", "Yvette Cedillo").
friend_("Caleb Haber", "Adolph Brannan").
friend_("Cole Mcnew", "Ernesto Mcnew").
friend_("Cole Mcnew", "Laverna Kovach").
friend_("Don Mcnew", "Jung Henderson").
friend_("Dudley Wise", "Lorelei Mcnew").
friend_("Dudley Wise", "Rosalinda Francois").
friend_("Dudley Wise", "Reggie Earnest").
friend_("Dudley Wise", "Samantha Earnest").
friend_("Ernesto Mcnew", "Marcelino Mcnew").
friend_("Ernesto Mcnew", "Carey Mckenna").
friend_("Ernesto Mcnew", "Mona Pannell").
friend_("Ernesto Mcnew", "Taneka Abraham").
friend_("Ernesto Mcnew", "Ali Schoonmaker").
friend_("Garry Mcnew", "Phylis Nicolas").
friend_("Garry Mcnew", "Rosendo Skaggs").
friend_("Garry Mcnew", "Cherise Earnest").
friend_("Garry Mcnew", "Madelyn Palermo").
friend_("Garry Mcnew", "Lauretta Mason").
friend_("Hayden Mcnew", "Dane Kee").
friend_("Hayden Mcnew", "Jona Carrell").
friend_("Haywood Mcnew", "Benton Earnest").
friend_("Haywood Mcnew", "Lauretta Mason").
friend_("Jacinta Wise", "Kris Haber").
friend_("Jacinta Wise", "Eula Crain").
friend_("Jeanelle Mcnew", "Malik Loftus").
friend_("Jeanelle Mcnew", "Rosalinda Brannan").
friend_("Jeanelle Mcnew", "Johnathan Boutte").
friend_("Jung Henderson", "Alberta Abraham").
friend_("Jung Henderson", "Monique Palermo").
friend_("Marcelino Mcnew", "Nathanial Lizotte").
friend_("Marcelino Mcnew", "Carson Kovach").
friend_("Marcelino Mcnew", "Roger Griffiths").
friend_("Marko Henderson", "Sha Langley").
friend_("Marko Henderson", "Zulema Crain").
friend_("Maxwell Henderson", "Cherry Nicolas").
friend_("Maxwell Henderson", "Ulysses Nicolas").
friend_("Merrill Mcnew", "Hazel Earnest").
friend_("Merrill Mcnew", "Roland Earnest").
friend_("Milton Henderson", "Sha Langley").
friend_("Milton Henderson", "Lanny Pannell").
friend_("Milton Henderson", "Pasquale Levy").
friend_("Noelia Henderson", "Aurelio Wasserman").
friend_("Rae Mcnew", "Marilyn Nicolas").
friend_("Rae Mcnew", "Yoshiko Crain").
friend_("Rae Mcnew", "Domonique Cedillo").
friend_("Rae Mcnew", "Enoch Palermo").
friend_("Rae Mcnew", "Casey Brannan").
friend_("Rae Mcnew", "Johnathan Boutte").
friend_("Roxy Mcnew", "Zoraida Palermo").
friend_("Roxy Mcnew", "Nada Shirk").
friend_("Stefan Henderson", "Stuart Abraham").
friend_("Aletha Nicolas", "Elsy Hornback").
friend_("Carrol Nicolas", "Roland Earnest").
friend_("Carrol Nicolas", "Lorine Wasserman").
friend_("Carrol Nicolas", "Lea Levy").
friend_("Carrol Nicolas", "Nada Shirk").
friend_("Cherry Nicolas", "Hannah Palermo").
friend_("Connie Nicolas", "Monique Griffiths").
friend_("Dwayne Langley", "Thurman Crain").
friend_("Dwayne Langley", "Ester Palermo").
friend_("Dwayne Langley", "Jona Carrell").
friend_("Dwayne Langley", "Freddy Shirk").
friend_("Edythe Nicolas", "Rosina Lizotte").
friend_("Edythe Nicolas", "Maria Earnest").
friend_("Edythe Nicolas", "Kevin Boutte").
friend_("Edythe Nicolas", "Zoila Mason").
friend_("Eldon Nicolas", "Ora Lizotte").
friend_("Eldon Nicolas", "Anibal Schoonmaker").
friend_("Errol Brook", "Laverna Kovach").
friend_("Eula Crain", "Rufus Brook").
friend_("Eula Crain", "Hazel Earnest").
friend_("Eula Crain", "Elissa Cedillo").
friend_("Lera Brook", "Elissa Kovach").
friend_("Marilyn Nicolas", "Ali Schoonmaker").
friend_("Marilyn Nicolas", "Elwood Decosta").
friend_("Marilyn Nicolas", "Freddy Shirk").
friend_("Preston Francois", "Ester Kovach").
friend_("Preston Francois", "Laverna Kovach").
friend_("Rosalinda Francois", "Edmond Schreiner").
friend_("Rosalinda Francois", "Aurelio Wasserman").
friend_("Rosalinda Francois", "Craig Boutte").
friend_("Rosalinda Francois", "Lauretta Mason").
friend_("Rufus Brook", "Sha Langley").
friend_("Rufus Brook", "Kirk Petry").
friend_("Rufus Brook", "Eduardo Earnest").
friend_("Rufus Brook", "Dillon Abraham").
friend_("Rufus Brook", "Spencer Griffiths").
friend_("Theodore Crain", "Kevin Boutte").
friend_("Theodore Crain", "Monique Griffiths").
friend_("Thurman Crain", "Hanh Mohan").
friend_("Thurman Crain", "Reinaldo Hornback").
friend_("Ulysses Nicolas", "Adalberto Cedillo").
friend_("Ulysses Nicolas", "Luisa Hornback").
friend_("Ulysses Nicolas", "Annabelle Schoonmaker").
friend_("Ulysses Nicolas", "Monique Palermo").
friend_("Yoshiko Crain", "Edythe Earnest").
friend_("Yoshiko Crain", "Elwood Decosta").
friend_("Yoshiko Crain", "Craig Boutte").
friend_("Zulema Crain", "Hanh Mohan").
friend_("Zulema Crain", "Annabelle Schoonmaker").
friend_("Zulema Crain", "Jules Levy").
friend_("Carey Mckenna", "Dwain Lizotte").
friend_("Chuck Lizotte", "Harold Wilkie").
friend_("Chuck Lizotte", "Lila Petry").
friend_("Dwain Lizotte", "Weldon Skaggs").
friend_("Dwain Lizotte", "Ofelia Carrell").
friend_("Dwain Lizotte", "Hanh Boutte").
friend_("Hanh Mohan", "Rolland Mckenna").
friend_("Hanh Mohan", "Weldon Skaggs").
friend_("Hanh Mohan", "Effie Schoonmaker").
friend_("Hanh Mohan", "Daniel Brannan").
friend_("Harold Wilkie", "Margot Skaggs").
friend_("Harold Wilkie", "Tessie Loftus").
friend_("Harold Wilkie", "Joslyn Mason").
friend_("Hoa Skaggs", "Dane Kee").
friend_("Hoa Skaggs", "Craig Boutte").
friend_("Jeannine Skaggs", "Daniel Brannan").
friend_("Kirk Petry", "Rosendo Skaggs").
friend_("Kirk Petry", "Windy Mckenna").
friend_("Kirk Petry", "Reggie Earnest").
friend_("Kirk Petry", "Rosanna Palermo").
friend_("Kirk Petry", "Charlie Kovach").
friend_("Kirk Petry", "Jules Levy").
friend_("Kirk Petry", "Olivia Griffiths").
friend_("Lila Petry", "Elton Griffiths").
friend_("Lucas Mckenna", "Dane Kee").
friend_("Lucas Mckenna", "Edmond Schreiner").
friend_("Lucas Mckenna", "Reggie Earnest").
friend_("Maranda Lizotte", "Francisco Palermo").
friend_("Margot Skaggs", "Adalberto Cedillo").
friend_("Margot Skaggs", "Laurel Decosta").
friend_("Margot Skaggs", "Zoila Decosta").
friend_("Margot Skaggs", "Bruce Mason").
friend_("Nathanial Lizotte", "Quincy Pannell").
friend_("Ora Lizotte", "Randell Pannell").
friend_("Ora Lizotte", "Roman Palermo").
friend_("Reyna Petry", "Ester Palermo").
friend_("Reyna Petry", "Carson Kovach").
friend_("Reyna Petry", "Charlie Kovach").
friend_("Rolland Mckenna", "Cherise Earnest").
friend_("Rolland Mckenna", "Annabelle Schoonmaker").
friend_("Rolland Mckenna", "Hanh Boutte").
friend_("Rosendo Skaggs", "Margo Brannan").
friend_("Rosendo Skaggs", "Darin Shirk").
friend_("Shirley Skaggs", "Bryant Bradberry").
friend_("Weldon Skaggs", "Clayton Shirk").
friend_("Weldon Skaggs", "Jame Shirk").
friend_("Windy Mckenna", "Ron Woodman").
friend_("Windy Mckenna", "Elton Griffiths").
friend_("Yoko Wilkie", "Tamala Pannell").
friend_("Benton Earnest", "Geri Woodman").
friend_("Benton Earnest", "Tamala Pannell").
friend_("Benton Earnest", "Monique Palermo").
friend_("Benton Earnest", "Roman Palermo").
friend_("Calvin Woodman", "Elissa Cedillo").
friend_("Calvin Woodman", "Rosalinda Brannan").
friend_("Cherise Earnest", "Tamala Pannell").
friend_("Cherise Earnest", "Charlie Kovach").
friend_("Duncan Pannell", "Eduardo Earnest").
friend_("Duncan Pannell", "Quincy Pannell").
friend_("Duncan Pannell", "Roman Palermo").
friend_("Duncan Pannell", "Daniel Brannan").
friend_("Duncan Pannell", "Ester Kovach").
friend_("Edmond Schreiner", "Roger Griffiths").
friend_("Eduardo Earnest", "Samantha Earnest").
friend_("Eduardo Earnest", "Domonique Cedillo").
friend_("Eduardo Earnest", "Elissa Kovach").
friend_("Eduardo Earnest", "Johnathan Boutte").
friend_("Edythe Earnest", "Stuart Abraham").
friend_("Geri Woodman", "Joslyn Mason").
friend_("Ian Pannell", "Spencer Griffiths").
friend_("Ivory Pannell", "Mona Pannell").
friend_("Ivory Pannell", "Roman Palermo").
friend_("Ivory Pannell", "Maurine Shirk").
friend_("Johnnie Pannell", "Effie Schoonmaker").
friend_("Mickey Earnest", "Tamala Pannell").
friend_("Mickey Earnest", "Luisa Hornback").
friend_("Mickey Earnest", "Laurel Decosta").
friend_("Mona Pannell", "Yvette Cedillo").
friend_("Mona Pannell", "Zoraida Palermo").
friend_("Mona Pannell", "Elissa Kovach").
friend_("Quincy Pannell", "Shirleen Abraham").
friend_("Randell Pannell", "Carson Kovach").
friend_("Ron Woodman", "Lucienne Cedillo").
friend_("Ron Woodman", "Clarence Mason").
friend_("Samantha Earnest", "Taneka Abraham").
friend_("Alberta Abraham", "Annabelle Schoonmaker").
friend_("Aurelio Wasserman", "Marcel Brannan").
friend_("Aurelio Wasserman", "Zoila Mason").
friend_("Bee Cedillo", "Domonique Cedillo").
friend_("Domonique Cedillo", "Cary Etheridge").
friend_("Elsy Hornback", "Rosalinda Brannan").
friend_("Gerardo Hornback", "Ned Cedillo").
friend_("Gerardo Hornback", "Effie Schoonmaker").
friend_("Gerardo Hornback", "Elissa Kovach").
friend_("Gerardo Hornback", "Zoila Mason").
friend_("Kasey Cedillo", "Zoila Decosta").
friend_("Kasey Cedillo", "Mercedes Shirk").
friend_("Lorine Wasserman", "Bryant Bradberry").
friend_("Luisa Hornback", "Zoraida Palermo").
friend_("Ned Cedillo", "Reinaldo Hornback").
friend_("Ned Cedillo", "Pasquale Levy").
friend_("Shanda Wasserman", "Spencer Griffiths").
friend_("Stuart Abraham", "Yvette Cedillo").
friend_("Stuart Abraham", "Zoraida Palermo").
friend_("Yvette Cedillo", "Madelyn Palermo").
friend_("Ali Schoonmaker", "Darin Shirk").
friend_("Blair Etheridge", "Clarence Mason").
friend_("Cary Etheridge", "Ofelia Carrell").
friend_("Effie Schoonmaker", "Marlana Boutte").
friend_("Enoch Palermo", "Rosalinda Brannan").
friend_("Enoch Palermo", "Elton Griffiths").
friend_("Esteban Schoonmaker", "Abraham Decosta").
friend_("Esteban Schoonmaker", "Elissa Kovach").
friend_("Jona Carrell", "Sylvia Palermo").
friend_("Liane Schoonmaker", "Chelsie Bradberry").
friend_("Madelyn Palermo", "Rosalinda Brannan").
friend_("Madelyn Palermo", "Craig Boutte").
friend_("Rigoberto Carrell", "Bryant Bradberry").
friend_("Roman Palermo", "Spencer Griffiths").
friend_("Roman Palermo", "Zoila Mason").
friend_("Rosanna Palermo", "Jules Levy").
friend_("Sylvia Palermo", "Clayton Shirk").
friend_("Tessie Loftus", "Zoraida Palermo").
friend_("Tessie Loftus", "Spencer Griffiths").
friend_("Zoraida Palermo", "Monique Griffiths").
friend_("Abraham Decosta", "Jules Levy").
friend_("Adolph Brannan", "Jacques Decosta").
friend_("Adolph Brannan", "Jules Levy").
friend_("Elwood Decosta", "Zoila Mason").
friend_("Jules Levy", "Clarence Mason").
friend_("Marcel Brannan", "Rosalinda Brannan").
friend_("Margaret Kovach", "Craig Boutte").
friend_("Niesha Decosta", "Zoila Mason").
friend_("Pasquale Levy", "Clayton Shirk").
friend_("Stuart Decosta", "Clayton Shirk").
friend_("Nada Shirk", "Olivia Griffiths").
friend_("Olivia Griffiths", "Zoila Mason").

:- dynamic prolog_file_type/2.
:- multifile prolog_file_type/2.

prolog_file_type(pl, prolog).
prolog_file_type(prolog, prolog).
prolog_file_type(qlf, prolog).
prolog_file_type(pl, source).
prolog_file_type(prolog, source).
prolog_file_type(qlf, qlf).
prolog_file_type(A, executable) :-
    system:current_prolog_flag(shared_object_extension, A).
prolog_file_type(dylib, executable) :-
    system:current_prolog_flag(apple, true).

friend(X, Y) :-
    friend_(X, Y).
friend(X, Y) :-
    friend_(Y, X).

niece(X, Y) :-
    sibling(X, A),
    daughter(A, Y).

nephew(X, Y) :-
    sibling(X, A),
    son(A, Y).

brother_in_law(X, Y) :-
    married(X, A),
    brother(A, Y).
