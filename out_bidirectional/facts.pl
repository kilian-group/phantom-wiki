
sister_in_law(X, Y) :-
    married(X, A),
    sister(A, Y).

wife(X, Y) :-
    married(X, Y),
    female(Y).

male(X) :-
    gender(X, "male").

:- dynamic son_inverse/2.

son_inverse(A, B) :-
    son(B, A).

:- dynamic second_uncle_inverse/2.

second_uncle_inverse(A, B) :-
    second_uncle(B, A).

:- dynamic prolog_load_file/2.
:- multifile prolog_load_file/2.


husband(X, Y) :-
    married(X, Y),
    male(Y).

daughter_in_law(X, Y) :-
    child(X, A),
    wife(A, Y).

:- dynamic daughter_inverse/2.

daughter_inverse(A, B) :-
    daughter(B, A).

nonbinary(X) :-
    gender(X, "nonbinary").

:- dynamic second_aunt_inverse/2.

second_aunt_inverse(A, B) :-
    second_aunt(B, A).

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


:- dynamic wife_inverse/2.

wife_inverse(A, B) :-
    wife(B, A).

:- dynamic male_second_cousin_inverse/2.

male_second_cousin_inverse(A, B) :-
    male_second_cousin(B, A).

daughter(X, Y) :-
    child(X, Y),
    female(Y).

father_in_law(X, Y) :-
    married(X, A),
    father(A, Y).

:- dynamic expand_answer/2.
:- multifile expand_answer/2.


:- dynamic husband_inverse/2.

husband_inverse(A, B) :-
    husband(B, A).

:- dynamic female_second_cousin_inverse/2.

female_second_cousin_inverse(A, B) :-
    female_second_cousin(B, A).

mother_in_law(X, Y) :-
    married(X, A),
    mother(A, Y).

father(X, Y) :-
    parent(X, Y),
    male(Y).

:- dynamic aunt_inverse/2.

aunt_inverse(A, B) :-
    aunt(B, A).

child(X, Y) :-
    parent(Y, X).

male_first_cousin_once_removed(X, Y) :-
    cousin(X, A),
    son(A, Y),
    X\=Y.

:- dynamic uncle_inverse/2.

uncle_inverse(A, B) :-
    uncle(B, A).

female_first_cousin_once_removed(X, Y) :-
    cousin(X, A),
    daughter(A, Y),
    X\=Y.

brother(X, Y) :-
    sibling(X, Y),
    male(Y).

:- dynamic niece_inverse/2.

niece_inverse(A, B) :-
    niece(B, A).

mother(X, Y) :-
    parent(X, Y),
    female(Y).

male_second_cousin(X, Y) :-
    parent(X, A),
    parent(Y, B),
    cousin(A, B),
    male(Y),
    X\=Y.

:- dynamic nephew_inverse/2.

nephew_inverse(A, B) :-
    nephew(B, A).

:- dynamic grandparent_inverse/2.

grandparent_inverse(A, B) :-
    grandparent(B, A).

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


:- multifile prolog_predicate_name/2.


:- dynamic grandmother_inverse/2.

grandmother_inverse(A, B) :-
    grandmother(B, A).

:- dynamic term_expansion/2.
:- multifile term_expansion/2.


sister(X, Y) :-
    sibling(X, Y),
    female(Y).

male_cousin(X, Y) :-
    cousin(X, Y),
    male(Y).

:- dynamic grandfather_inverse/2.

grandfather_inverse(A, B) :-
    grandfather(B, A).

female_cousin(X, Y) :-
    cousin(X, Y),
    female(Y).

sibling(X, Y) :-
    parent(X, A),
    parent(Y, A),
    X\=Y.

:- dynamic goal_expansion/4.
:- multifile goal_expansion/4.


:- dynamic grandchild_inverse/2.

grandchild_inverse(A, B) :-
    grandchild(B, A).

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

cousin(X, Y) :-
    parent(X, A),
    parent(Y, B),
    sibling(A, B),
    X\=Y.

:- dynamic term_expansion/4.
:- multifile term_expansion/4.


:- dynamic granddaughter_inverse/2.

granddaughter_inverse(A, B) :-
    granddaughter(B, A).

uncle(X, Y) :-
    parent(X, A),
    brother(A, Y).

:- dynamic grandson_inverse/2.

grandson_inverse(A, B) :-
    grandson(B, A).

aunt(X, Y) :-
    parent(X, A),
    sister(A, Y).

:- dynamic father_in_law_inverse/2.

father_in_law_inverse(A, B) :-
    father_in_law(B, A).

second_uncle(X, Y) :-
    great_grandparent(X, A),
    brother(A, Y).

:- dynamic mother_in_law_inverse/2.

mother_in_law_inverse(A, B) :-
    mother_in_law(B, A).

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

second_aunt(X, Y) :-
    great_grandparent(X, A),
    sister(A, Y).

:- multifile prolog_clause_name/2.


:- dynamic child_inverse/2.

child_inverse(A, B) :-
    child(B, A).

great_granddaughter(X, Y) :-
    great_grandchild(X, Y),
    female(Y).

:- dynamic save_all_clauses_to_file/1.

save_all_clauses_to_file(A) :-
    open(A, write, B),
    set_output(B),
    listing,
    close(B).

:- dynamic brother_in_law_inverse/2.

brother_in_law_inverse(A, B) :-
    brother_in_law(B, A).

great_grandson(X, Y) :-
    great_grandchild(X, Y),
    male(Y).

:- dynamic father_inverse/2.

father_inverse(A, B) :-
    father(B, A).

:- dynamic sister_in_law_inverse/2.

sister_in_law_inverse(A, B) :-
    sister_in_law(B, A).

:- dynamic pyrun/2.

pyrun(A, B) :-
    read_term_from_atom(A, C, [variable_names(B)]),
    call(C).

:- dynamic mother_inverse/2.

mother_inverse(A, B) :-
    mother(B, A).

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


:- dynamic son_in_law_inverse/2.

son_in_law_inverse(A, B) :-
    son_in_law(B, A).

great_grandchild(X, Y) :-
    great_grandparent(Y, X).

:- dynamic brother_inverse/2.

brother_inverse(A, B) :-
    brother(B, A).

:- dynamic daughter_in_law_inverse/2.

daughter_in_law_inverse(A, B) :-
    daughter_in_law(B, A).

:- dynamic sister_inverse/2.

sister_inverse(A, B) :-
    sister(B, A).

great_grandparent(X, Y) :-
    grandparent(X, Z),
    parent(Z, Y).

:- dynamic great_aunt_inverse/2.

great_aunt_inverse(A, B) :-
    great_aunt(B, A).

great_grandmother(X, Y) :-
    great_grandparent(X, Y),
    female(Y).

:- dynamic parent_inverse/2.

parent_inverse(A, B) :-
    parent(B, A).

:- dynamic goal_expansion/2.
:- multifile goal_expansion/2.


:- dynamic great_uncle_inverse/2.

great_uncle_inverse(A, B) :-
    great_uncle(B, A).

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

granddaughter(X, Y) :-
    grandchild(X, Y),
    female(Y).

:- dynamic great_grandparent_inverse/2.

great_grandparent_inverse(A, B) :-
    great_grandparent(B, A).

grandson(X, Y) :-
    grandchild(X, Y),
    male(Y).

:- dynamic great_grandmother_inverse/2.

great_grandmother_inverse(A, B) :-
    great_grandmother(B, A).

:- dynamic great_grandfather_inverse/2.

great_grandfather_inverse(A, B) :-
    great_grandfather(B, A).

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

great_uncle(X, Y) :-
    grandparent(X, A),
    brother(A, Y).

:- dynamic message_hook/3.
:- multifile message_hook/3.


:- dynamic expand_query/4.
:- multifile expand_query/4.


:- dynamic great_grandchild_inverse/2.

great_grandchild_inverse(A, B) :-
    great_grandchild(B, A).

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

:- dynamic great_granddaughter_inverse/2.

great_granddaughter_inverse(A, B) :-
    great_granddaughter(B, A).

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

:- dynamic great_grandson_inverse/2.

great_grandson_inverse(A, B) :-
    great_grandson(B, A).

great_aunt(X, Y) :-
    grandparent(X, A),
    sister(A, Y).

:- dynamic female_cousin_inverse/2.

female_cousin_inverse(A, B) :-
    female_cousin(B, A).

grandparent(X, Y) :-
    parent(X, Z),
    parent(Z, Y).

:- dynamic male_cousin_inverse/2.

male_cousin_inverse(A, B) :-
    male_cousin(B, A).

:- dynamic library_directory/1.
:- multifile library_directory/1.


grandmother(X, Y) :-
    grandparent(X, Y),
    female(Y).

:- dynamic friend_/2.

friend_("Aida Wang", "Alvaro Smock").
friend_("Aida Wang", "Dominique Smock").
friend_("Aida Wang", "Johnetta Wang").
friend_("Aida Wang", "Shelli Beltran").
friend_("Alison Smock", "Deane Smock").
friend_("Alison Smock", "Gene Smock").
friend_("Alison Smock", "Saul Wexler").
friend_("Alison Smock", "Valentina Wexler").
friend_("Alvaro Smock", "Valentina Wexler").
friend_("Alvaro Smock", "Vicki Hackworth").
friend_("Aubrey Smock", "Dominique Smock").
friend_("Aubrey Smock", "Lannie Smock").
friend_("Daisy Beltran", "Orlando Beltran").
friend_("Daisy Beltran", "Saul Wexler").
friend_("Deane Smock", "Gene Smock").
friend_("Deane Smock", "Isabell Smock").
friend_("Deane Smock", "Shelli Beltran").
friend_("Dino Beltran", "Leeann Hackworth").
friend_("Dino Beltran", "Ricardo Hackworth").
friend_("Dino Beltran", "Saul Wexler").
friend_("Dominique Smock", "Lannie Smock").
friend_("Dominique Smock", "Leeann Hackworth").
friend_("Dominique Smock", "Ricardo Hackworth").
friend_("Gene Smock", "Jeannine Wexler").
friend_("Gene Smock", "Ricardo Hackworth").
friend_("Gene Smock", "Shelli Beltran").
friend_("Isabell Smock", "Jeannine Wexler").
friend_("Isabell Smock", "Lenore Hackworth").
friend_("Jeannine Wexler", "Vicki Hackworth").
friend_("Johnetta Wang", "Saul Wexler").
friend_("Johnetta Wang", "Shelli Beltran").
friend_("Lannie Smock", "Leeann Hackworth").
friend_("Lannie Smock", "Lenore Hackworth").
friend_("Lannie Smock", "Saul Wexler").
friend_("Lannie Smock", "Vicki Hackworth").
friend_("Leeann Hackworth", "Shelli Beltran").
friend_("Lenore Hackworth", "Saul Wexler").
friend_("Myrle Smock", "Ricardo Hackworth").
friend_("Orlando Beltran", "Valentina Wexler").
friend_("Ryan Wang", "Shelli Beltran").

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

:- dynamic female_first_cousin_once_removed_inverse/2.

female_first_cousin_once_removed_inverse(A, B) :-
    female_first_cousin_once_removed(B, A).

friend(X, Y) :-
    friend_(X, Y).
friend(X, Y) :-
    friend_(Y, X).

niece(X, Y) :-
    sibling(X, A),
    daughter(A, Y).

:- dynamic male_first_cousin_once_removed_inverse/2.

male_first_cousin_once_removed_inverse(A, B) :-
    male_first_cousin_once_removed(B, A).

nephew(X, Y) :-
    sibling(X, A),
    son(A, Y).

brother_in_law(X, Y) :-
    married(X, A),
    brother(A, Y).
