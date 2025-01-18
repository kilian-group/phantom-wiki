
:- dynamic term_expansion/2.
:- multifile term_expansion/2.


great_grandfather(X, Y) :-
    great_grandparent(X, Y),
    male(Y).

great_grandchild(X, Y) :-
    great_grandparent(Y, X).

great_grandparent(X, Y) :-
    grandparent(X, Z),
    parent(Z, Y).

:- dynamic library_directory/1.
:- multifile library_directory/1.


great_grandmother(X, Y) :-
    great_grandparent(X, Y),
    female(Y).

:- dynamic goal_expansion/4.
:- multifile goal_expansion/4.


:- dynamic hobby/2.

hobby("Adele Ervin", "meditation").
hobby("Alton Cater", "meteorology").
hobby("Aubrey Leibowitz", "biology").
hobby("Boris Ervin", "meteorology").
hobby("Bruce Cater", "dolls").
hobby("Delpha Donohue", "photography").
hobby("Derick Backus", "shogi").
hobby("Dirk Donohue", "dominoes").
hobby("Ella Cater", "tether car").
hobby("Gerry Donohue", "architecture").
hobby("Gustavo Leibowitz", "geocaching").
hobby("Jewel Backus", "trainspotting").
hobby("Karen Ervin", "bus spotting").
hobby("Lisha Leibowitz", "research").
hobby("Margarite Ussery", "geography").
hobby("Mason Donohue", "microbiology").
hobby("Pedro Donohue", "canoeing").
hobby("Rigoberto Bode", "learning").
hobby("Staci Donohue", "dairy farming").
hobby("Therese Donohue", "fossil hunting").
hobby("Tiffany Bode", "sociology").
hobby("Ty Donohue", "finance").
hobby("Tyler Ussery", "meditation").
hobby("Veronica Donohue", "wikipedia editing").
hobby("Vita Cater", "radio-controlled car racing").
hobby("Wes Backus", "social studies").
hobby("Wilfredo Cater", "judo").

granddaughter(X, Y) :-
    grandchild(X, Y),
    female(Y).

grandson(X, Y) :-
    grandchild(X, Y),
    male(Y).

:- dynamic job/2.

job("Adele Ervin", "personal assistant").
job("Alton Cater", "health promotion specialist").
job("Aubrey Leibowitz", "osteopath").
job("Boris Ervin", "broadcast engineer").
job("Bruce Cater", "oncologist").
job("Delpha Donohue", "warehouse manager").
job("Derick Backus", "associate professor").
job("Dirk Donohue", "sports therapist").
job("Ella Cater", "retail manager").
job("Gerry Donohue", "immunologist").
job("Gustavo Leibowitz", "education administrator").
job("Jewel Backus", "early years teacher").
job("Karen Ervin", "biomedical scientist").
job("Lisha Leibowitz", "music tutor").
job("Margarite Ussery", "clinical cytogeneticist").
job("Mason Donohue", "ecologist").
job("Pedro Donohue", "barrister's clerk").
job("Rigoberto Bode", "petroleum engineer").
job("Staci Donohue", "clinical research associate").
job("Therese Donohue", "chief of staff").
job("Tiffany Bode", "occupational therapist").
job("Ty Donohue", "actuary").
job("Tyler Ussery", "police officer").
job("Veronica Donohue", "sound technician").
job("Vita Cater", "theatre manager").
job("Wes Backus", "clinical biochemist").
job("Wilfredo Cater", "public relations officer").

great_uncle(X, Y) :-
    grandparent(X, A),
    brother(A, Y).

:- dynamic save_all_clauses_to_file/1.

save_all_clauses_to_file(A) :-
    open(A, write, B),
    set_output(B),
    listing,
    close(B).

:- dynamic term_expansion/4.
:- multifile term_expansion/4.


grandchild(X, Y) :-
    grandparent(Y, X).

:- dynamic dob/2.

dob("Adele Ervin", "0259-06-10").
dob("Alton Cater", "0236-04-04").
dob("Aubrey Leibowitz", "0256-09-07").
dob("Boris Ervin", "0232-11-24").
dob("Bruce Cater", "0209-05-24").
dob("Delpha Donohue", "0171-04-12").
dob("Derick Backus", "0295-10-18").
dob("Dirk Donohue", "0167-06-08").
dob("Ella Cater", "0239-10-28").
dob("Gerry Donohue", "0192-01-16").
dob("Gustavo Leibowitz", "0280-04-21").
dob("Jewel Backus", "0268-03-07").
dob("Karen Ervin", "0231-09-29").
dob("Lisha Leibowitz", "0256-07-31").
dob("Margarite Ussery", "0205-09-12").
dob("Mason Donohue", "0143-10-16").
dob("Pedro Donohue", "0172-08-18").
dob("Rigoberto Bode", "0146-09-21").
dob("Staci Donohue", "0162-07-16").
dob("Therese Donohue", "0141-09-13").
dob("Tiffany Bode", "0145-02-06").
dob("Ty Donohue", "0170-06-04").
dob("Tyler Ussery", "0206-04-13").
dob("Veronica Donohue", "0174-07-16").
dob("Vita Cater", "0205-04-19").
dob("Wes Backus", "0268-09-01").
dob("Wilfredo Cater", "0263-03-03").

:- dynamic file_search_path/2.
:- multifile file_search_path/2.

file_search_path(library, Dir) :-
    library_directory(Dir).
file_search_path(swi, A) :-
    system:current_prolog_flag(home, A).
file_search_path(swi, A) :-
    system:current_prolog_flag(shared_home, A).
file_search_path(library, app_config(lib)).
file_search_path(library, swi(library)).
file_search_path(library, swi(library/clp)).
file_search_path(library, A) :-
    system:'$ext_library_directory'(A).
file_search_path(foreign, swi(A)) :-
    system:
    (   current_prolog_flag(apple_universal_binary, true),
        A='lib/fat-darwin'
    ).
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

:- multifile prolog_list_goal/1.


:- dynamic type/2.

type("Adele Ervin", person).
type("Alton Cater", person).
type("Aubrey Leibowitz", person).
type("Boris Ervin", person).
type("Bruce Cater", person).
type("Delpha Donohue", person).
type("Derick Backus", person).
type("Dirk Donohue", person).
type("Ella Cater", person).
type("Gerry Donohue", person).
type("Gustavo Leibowitz", person).
type("Jewel Backus", person).
type("Karen Ervin", person).
type("Lisha Leibowitz", person).
type("Margarite Ussery", person).
type("Mason Donohue", person).
type("Pedro Donohue", person).
type("Rigoberto Bode", person).
type("Staci Donohue", person).
type("Therese Donohue", person).
type("Tiffany Bode", person).
type("Ty Donohue", person).
type("Tyler Ussery", person).
type("Veronica Donohue", person).
type("Vita Cater", person).
type("Wes Backus", person).
type("Wilfredo Cater", person).

grandfather(X, Y) :-
    grandparent(X, Y),
    male(Y).

:- dynamic expand_query/4.
:- multifile expand_query/4.


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

great_aunt(X, Y) :-
    grandparent(X, A),
    sister(A, Y).

grandparent(X, Y) :-
    parent(X, Z),
    parent(Z, Y).

grandmother(X, Y) :-
    grandparent(X, Y),
    female(Y).

:- dynamic friend_/2.

friend_("Adele Ervin", "Alton Cater").
friend_("Adele Ervin", "Boris Ervin").
friend_("Adele Ervin", "Dirk Donohue").
friend_("Adele Ervin", "Therese Donohue").
friend_("Adele Ervin", "Wilfredo Cater").
friend_("Alton Cater", "Boris Ervin").
friend_("Alton Cater", "Dirk Donohue").
friend_("Alton Cater", "Margarite Ussery").
friend_("Alton Cater", "Therese Donohue").
friend_("Alton Cater", "Wilfredo Cater").
friend_("Aubrey Leibowitz", "Bruce Cater").
friend_("Aubrey Leibowitz", "Gerry Donohue").
friend_("Aubrey Leibowitz", "Rigoberto Bode").
friend_("Aubrey Leibowitz", "Veronica Donohue").
friend_("Aubrey Leibowitz", "Vita Cater").
friend_("Boris Ervin", "Dirk Donohue").
friend_("Boris Ervin", "Margarite Ussery").
friend_("Boris Ervin", "Therese Donohue").
friend_("Boris Ervin", "Wilfredo Cater").
friend_("Bruce Cater", "Gerry Donohue").
friend_("Bruce Cater", "Rigoberto Bode").
friend_("Bruce Cater", "Veronica Donohue").
friend_("Bruce Cater", "Vita Cater").
friend_("Delpha Donohue", "Gerry Donohue").
friend_("Delpha Donohue", "Jewel Backus").
friend_("Delpha Donohue", "Pedro Donohue").
friend_("Delpha Donohue", "Staci Donohue").
friend_("Delpha Donohue", "Tiffany Bode").
friend_("Delpha Donohue", "Ty Donohue").
friend_("Derick Backus", "Ella Cater").
friend_("Derick Backus", "Gustavo Leibowitz").
friend_("Derick Backus", "Lisha Leibowitz").
friend_("Derick Backus", "Mason Donohue").
friend_("Dirk Donohue", "Margarite Ussery").
friend_("Dirk Donohue", "Therese Donohue").
friend_("Dirk Donohue", "Wilfredo Cater").
friend_("Ella Cater", "Gustavo Leibowitz").
friend_("Ella Cater", "Lisha Leibowitz").
friend_("Ella Cater", "Mason Donohue").
friend_("Gerry Donohue", "Jewel Backus").
friend_("Gerry Donohue", "Pedro Donohue").
friend_("Gerry Donohue", "Rigoberto Bode").
friend_("Gerry Donohue", "Staci Donohue").
friend_("Gerry Donohue", "Tiffany Bode").
friend_("Gerry Donohue", "Ty Donohue").
friend_("Gerry Donohue", "Veronica Donohue").
friend_("Gerry Donohue", "Vita Cater").
friend_("Gustavo Leibowitz", "Lisha Leibowitz").
friend_("Gustavo Leibowitz", "Mason Donohue").
friend_("Jewel Backus", "Pedro Donohue").
friend_("Jewel Backus", "Staci Donohue").
friend_("Jewel Backus", "Tiffany Bode").
friend_("Jewel Backus", "Ty Donohue").
friend_("Karen Ervin", "Tyler Ussery").
friend_("Lisha Leibowitz", "Mason Donohue").
friend_("Lisha Leibowitz", "Tyler Ussery").
friend_("Lisha Leibowitz", "Wes Backus").
friend_("Margarite Ussery", "Therese Donohue").
friend_("Margarite Ussery", "Wilfredo Cater").
friend_("Mason Donohue", "Wes Backus").
friend_("Pedro Donohue", "Staci Donohue").
friend_("Pedro Donohue", "Tiffany Bode").
friend_("Pedro Donohue", "Ty Donohue").
friend_("Rigoberto Bode", "Veronica Donohue").
friend_("Rigoberto Bode", "Vita Cater").
friend_("Staci Donohue", "Tiffany Bode").
friend_("Staci Donohue", "Ty Donohue").
friend_("Therese Donohue", "Wilfredo Cater").
friend_("Tiffany Bode", "Ty Donohue").
friend_("Veronica Donohue", "Vita Cater").

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

:- multifile message_property/2.


sister_in_law(X, Y) :-
    married(X, A),
    sister(A, Y).

wife(X, Y) :-
    married(X, Y),
    female(Y).

husband(X, Y) :-
    married(X, Y),
    male(Y).

daughter_in_law(X, Y) :-
    child(X, A),
    wife(A, Y).

son_in_law(X, Y) :-
    child(X, A),
    husband(A, Y).

son(X, Y) :-
    child(X, Y),
    male(Y).

female(X) :-
    gender(X, "female").

daughter(X, Y) :-
    child(X, Y),
    female(Y).

father_in_law(X, Y) :-
    married(X, A),
    father(A, Y).

mother_in_law(X, Y) :-
    married(X, A),
    mother(A, Y).

father(X, Y) :-
    parent(X, Y),
    male(Y).

:- multifile prolog_predicate_name/2.


child(X, Y) :-
    parent(Y, X).

male_first_cousin_once_removed(X, Y) :-
    cousin(X, A),
    son(A, Y),
    X\=Y.

:- multifile prolog_clause_name/2.


:- dynamic expand_answer/2.
:- multifile expand_answer/2.


:- dynamic exception/3.
:- multifile exception/3.


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

:- dynamic message_hook/3.
:- multifile message_hook/3.


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

male(X) :-
    gender(X, "male").

:- dynamic prolog_file_type/2.
:- multifile prolog_file_type/2.

prolog_file_type(pl, prolog).
prolog_file_type(prolog, prolog).
prolog_file_type(qlf, prolog).
prolog_file_type(qlf, qlf).
prolog_file_type(A, executable) :-
    system:current_prolog_flag(shared_object_extension, A).
prolog_file_type(dylib, executable) :-
    system:current_prolog_flag(apple, true).

sister(Y, X) :-
    sibling(X, Y),
    female(X).

male_cousin(X, Y) :-
    cousin(X, Y),
    male(Y).

:- dynamic nonbinary/1.

nonbinary(X) :-
    gender(X, "nonbinary").

female_cousin(X, Y) :-
    cousin(X, Y),
    female(Y).

sibling(X, Y) :-
    parent(X, A),
    parent(Y, A),
    X\=Y.

:- dynamic resource/2.
:- multifile resource/2.


:- dynamic portray/1.
:- multifile portray/1.


:- dynamic prolog_load_file/2.
:- multifile prolog_load_file/2.


:- dynamic goal_expansion/2.
:- multifile goal_expansion/2.


:- dynamic parent/2.

parent("Adele Ervin", "Boris Ervin").
parent("Adele Ervin", "Karen Ervin").
parent("Alton Cater", "Bruce Cater").
parent("Alton Cater", "Vita Cater").
parent("Delpha Donohue", "Rigoberto Bode").
parent("Delpha Donohue", "Tiffany Bode").
parent("Derick Backus", "Jewel Backus").
parent("Derick Backus", "Wes Backus").
parent("Dirk Donohue", "Mason Donohue").
parent("Dirk Donohue", "Therese Donohue").
parent("Ella Cater", "Margarite Ussery").
parent("Ella Cater", "Tyler Ussery").
parent("Gerry Donohue", "Dirk Donohue").
parent("Gerry Donohue", "Staci Donohue").
parent("Gustavo Leibowitz", "Aubrey Leibowitz").
parent("Gustavo Leibowitz", "Lisha Leibowitz").
parent("Jewel Backus", "Alton Cater").
parent("Jewel Backus", "Ella Cater").
parent("Karen Ervin", "Bruce Cater").
parent("Karen Ervin", "Vita Cater").
parent("Lisha Leibowitz", "Boris Ervin").
parent("Lisha Leibowitz", "Karen Ervin").
parent("Pedro Donohue", "Mason Donohue").
parent("Pedro Donohue", "Therese Donohue").
parent("Ty Donohue", "Mason Donohue").
parent("Ty Donohue", "Therese Donohue").
parent("Veronica Donohue", "Mason Donohue").
parent("Veronica Donohue", "Therese Donohue").
parent("Vita Cater", "Delpha Donohue").
parent("Vita Cater", "Pedro Donohue").
parent("Wilfredo Cater", "Alton Cater").
parent("Wilfredo Cater", "Ella Cater").

cousin(X, Y) :-
    parent(X, A),
    parent(Y, B),
    sibling(A, B),
    X\=Y.

uncle(X, Y) :-
    parent(X, A),
    brother(A, Y).

:- thread_local thread_message_hook/3.
:- dynamic thread_message_hook/3.
:- volatile thread_message_hook/3.


aunt(X, Y) :-
    parent(X, A),
    sister(A, Y).

:- dynamic resource/3.
:- multifile resource/3.


second_uncle(X, Y) :-
    great_grandparent(X, A),
    brother(A, Y).

:- dynamic gender/2.

gender("Adele Ervin", "female").
gender("Alton Cater", "male").
gender("Aubrey Leibowitz", "male").
gender("Boris Ervin", "male").
gender("Bruce Cater", "male").
gender("Delpha Donohue", "female").
gender("Derick Backus", "male").
gender("Dirk Donohue", "male").
gender("Ella Cater", "female").
gender("Gerry Donohue", "male").
gender("Gustavo Leibowitz", "male").
gender("Jewel Backus", "female").
gender("Karen Ervin", "female").
gender("Lisha Leibowitz", "female").
gender("Margarite Ussery", "female").
gender("Mason Donohue", "male").
gender("Pedro Donohue", "male").
gender("Rigoberto Bode", "male").
gender("Staci Donohue", "female").
gender("Therese Donohue", "female").
gender("Tiffany Bode", "female").
gender("Ty Donohue", "male").
gender("Tyler Ussery", "male").
gender("Veronica Donohue", "female").
gender("Vita Cater", "female").
gender("Wes Backus", "male").
gender("Wilfredo Cater", "male").

second_aunt(X, Y) :-
    great_grandparent(X, A),
    sister(A, Y).

great_grandson(X, Y) :-
    great_grandchild(X, Y),
    male(Y).

:- dynamic pyrun/2.

pyrun(A, B) :-
    read_term_from_atom(A, C, [variable_names(B)]),
    call(C).

great_granddaughter(X, Y) :-
    great_grandchild(X, Y),
    female(Y).
