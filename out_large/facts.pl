
son_in_law(X, Y) :-
    child(X, A),
    husband(A, Y).

son(X, Y) :-
    child(X, Y),
    male(Y).

female(X) :-
    gender(X, "female").

:- dynamic prolog_load_file/2.
:- multifile prolog_load_file/2.


daughter(X, Y) :-
    child(X, Y),
    female(Y).

father_in_law(X, Y) :-
    married(X, A),
    father(A, Y).

:- multifile prolog_list_goal/1.


:- dynamic portray/1.
:- multifile portray/1.


mother_in_law(X, Y) :-
    married(X, A),
    mother(A, Y).

father(X, Y) :-
    parent(X, Y),
    male(Y).

:- dynamic expand_answer/2.
:- multifile expand_answer/2.


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

male(X) :-
    gender(X, "male").

sister(X, Y) :-
    sibling(X, Y),
    female(Y).

male_cousin(X, Y) :-
    cousin(X, Y),
    male(Y).

nonbinary(X) :-
    gender(X, "nonbinary").

:- dynamic exception/3.
:- multifile exception/3.


female_cousin(X, Y) :-
    cousin(X, Y),
    female(Y).

sibling(X, Y) :-
    parent(X, A),
    parent(Y, A),
    X\=Y.

:- dynamic resource/2.
:- multifile resource/2.


:- dynamic term_expansion/2.
:- multifile term_expansion/2.


:- dynamic parent/2.

parent("Amy Wilke", "Jackie Vandenberg").
parent("Amy Wilke", "Valentin Vandenberg").
parent("Anna Vandenberg", "Eli Vandenberg").
parent("Anna Vandenberg", "Tashina Vandenberg").
parent("Belva Murphey", "Amy Wilke").
parent("Belva Murphey", "Stacey Wilke").
parent("Charley Vandenberg", "Jackie Vandenberg").
parent("Charley Vandenberg", "Valentin Vandenberg").
parent("Clara Mcgough", "Myrl Mcgough").
parent("Clara Mcgough", "Randall Mcgough").
parent("Delsie Mcgough", "Myrl Mcgough").
parent("Delsie Mcgough", "Randall Mcgough").
parent("Eli Vandenberg", "Jackie Vandenberg").
parent("Eli Vandenberg", "Valentin Vandenberg").
parent("Luke Wilke", "Amy Wilke").
parent("Luke Wilke", "Stacey Wilke").
parent("Marion Wilke", "Amy Wilke").
parent("Marion Wilke", "Stacey Wilke").
parent("Myrl Mcgough", "Alvaro Murphey").
parent("Myrl Mcgough", "Belva Murphey").
parent("Ophelia Mcgough", "Chrissy Mcgough").
parent("Ophelia Mcgough", "Elroy Mcgough").
parent("Randall Mcgough", "Chrissy Mcgough").
parent("Randall Mcgough", "Elroy Mcgough").
parent("Thelma Vandenberg", "Jackie Vandenberg").
parent("Thelma Vandenberg", "Valentin Vandenberg").
parent("Amos Oberg", "Kirsten Oberg").
parent("Amos Oberg", "Lyman Oberg").
parent("Bryce Oberg", "Abel Oberg").
parent("Bryce Oberg", "Renate Oberg").
parent("Clyde Oberg", "Brigida Oberg").
parent("Clyde Oberg", "Richard Oberg").
parent("Demarcus Narvaez", "Colby Narvaez").
parent("Demarcus Narvaez", "Luisa Narvaez").
parent("Luisa Narvaez", "Cherlyn Oberg").
parent("Luisa Narvaez", "Monte Oberg").
parent("Lyman Oberg", "Brigida Oberg").
parent("Lyman Oberg", "Richard Oberg").
parent("Mason Oberg", "Kirsten Oberg").
parent("Mason Oberg", "Lyman Oberg").
parent("Monte Oberg", "Brigida Oberg").
parent("Monte Oberg", "Richard Oberg").
parent("Owen Narvaez", "Demarcus Narvaez").
parent("Owen Narvaez", "Rhoda Narvaez").
parent("Richard Oberg", "Abel Oberg").
parent("Richard Oberg", "Renate Oberg").
parent("Sarah Oberg", "Cherlyn Oberg").
parent("Sarah Oberg", "Monte Oberg").
parent("Twila Oberg", "Clyde Oberg").
parent("Twila Oberg", "Marlo Oberg").
parent("Celestine Remillard", "Dani Remillard").
parent("Celestine Remillard", "Hunter Remillard").
parent("Chrissy Remillard", "Jaime Remillard").
parent("Chrissy Remillard", "Morgan Remillard").
parent("Dorinda Chrisman", "Louann Chrisman").
parent("Dorinda Chrisman", "Thomas Chrisman").
parent("Hunter Remillard", "Jaime Remillard").
parent("Hunter Remillard", "Morgan Remillard").
parent("Jaime Remillard", "Jon Remillard").
parent("Jaime Remillard", "Sherrie Remillard").
parent("Jude Remillard", "Jon Remillard").
parent("Jude Remillard", "Sherrie Remillard").
parent("Kori Remillard", "Jude Remillard").
parent("Kori Remillard", "Tianna Remillard").
parent("Louann Chrisman", "Dani Remillard").
parent("Louann Chrisman", "Hunter Remillard").
parent("Mai Remillard", "Justine Remillard").
parent("Mai Remillard", "Willie Remillard").
parent("Margie Remillard", "Jaime Remillard").
parent("Margie Remillard", "Morgan Remillard").
parent("Sherrie Remillard", "Aurelia Dishman").
parent("Sherrie Remillard", "King Dishman").
parent("Wanita Remillard", "Jon Remillard").
parent("Wanita Remillard", "Sherrie Remillard").
parent("Willie Remillard", "Dani Remillard").
parent("Willie Remillard", "Hunter Remillard").

cousin(X, Y) :-
    parent(X, A),
    parent(Y, B),
    sibling(A, B),
    X\=Y.

:- dynamic goal_expansion/4.
:- multifile goal_expansion/4.


uncle(X, Y) :-
    parent(X, A),
    brother(A, Y).

:- dynamic term_expansion/4.
:- multifile term_expansion/4.


aunt(X, Y) :-
    parent(X, A),
    sister(A, Y).

second_uncle(X, Y) :-
    great_grandparent(X, A),
    brother(A, Y).

:- dynamic gender/2.

gender("Alvaro Murphey", "male").
gender("Amy Wilke", "female").
gender("Anna Vandenberg", "female").
gender("Belva Murphey", "female").
gender("Charley Vandenberg", "male").
gender("Chrissy Mcgough", "female").
gender("Clara Mcgough", "female").
gender("Delsie Mcgough", "female").
gender("Eli Vandenberg", "male").
gender("Elroy Mcgough", "male").
gender("Jackie Vandenberg", "female").
gender("Luke Wilke", "male").
gender("Marion Wilke", "male").
gender("Myrl Mcgough", "female").
gender("Ophelia Mcgough", "female").
gender("Randall Mcgough", "male").
gender("Stacey Wilke", "male").
gender("Tashina Vandenberg", "female").
gender("Thelma Vandenberg", "female").
gender("Valentin Vandenberg", "male").
gender("Abel Oberg", "male").
gender("Amos Oberg", "male").
gender("Brigida Oberg", "female").
gender("Bryce Oberg", "male").
gender("Cherlyn Oberg", "female").
gender("Clyde Oberg", "male").
gender("Colby Narvaez", "male").
gender("Demarcus Narvaez", "male").
gender("Kirsten Oberg", "female").
gender("Luisa Narvaez", "female").
gender("Lyman Oberg", "male").
gender("Marlo Oberg", "female").
gender("Mason Oberg", "male").
gender("Monte Oberg", "male").
gender("Owen Narvaez", "male").
gender("Renate Oberg", "female").
gender("Rhoda Narvaez", "female").
gender("Richard Oberg", "male").
gender("Sarah Oberg", "female").
gender("Twila Oberg", "female").
gender("Aurelia Dishman", "female").
gender("Celestine Remillard", "female").
gender("Chrissy Remillard", "female").
gender("Dani Remillard", "female").
gender("Dorinda Chrisman", "female").
gender("Hunter Remillard", "male").
gender("Jaime Remillard", "male").
gender("Jon Remillard", "male").
gender("Jude Remillard", "male").
gender("Justine Remillard", "female").
gender("King Dishman", "male").
gender("Kori Remillard", "female").
gender("Louann Chrisman", "female").
gender("Mai Remillard", "female").
gender("Margie Remillard", "female").
gender("Morgan Remillard", "female").
gender("Sherrie Remillard", "female").
gender("Thomas Chrisman", "male").
gender("Tianna Remillard", "female").
gender("Wanita Remillard", "female").
gender("Willie Remillard", "male").

second_aunt(X, Y) :-
    great_grandparent(X, A),
    sister(A, Y).

great_grandson(X, Y) :-
    great_grandchild(X, Y),
    male(Y).

:- multifile prolog_predicate_name/2.


:- multifile message_property/2.


:- dynamic pyrun/2.

pyrun(A, B) :-
    read_term_from_atom(A, C, [variable_names(B)]),
    call(C).

great_granddaughter(X, Y) :-
    great_grandchild(X, Y),
    female(Y).

great_grandchild(X, Y) :-
    great_grandparent(Y, X).

:- multifile prolog_clause_name/2.


daughter_in_law(X, Y) :-
    child(X, A),
    wife(A, Y).

great_grandfather(X, Y) :-
    great_grandparent(X, Y),
    male(Y).

sister_in_law(X, Y) :-
    married(X, A),
    sister(A, Y).

great_grandmother(X, Y) :-
    great_grandparent(X, Y),
    female(Y).

brother_in_law(X, Y) :-
    married(X, A),
    brother(A, Y).

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


great_grandparent(X, Y) :-
    grandparent(X, Z),
    parent(Z, Y).

friend(X, Y) :-
    friend_(X, Y).
friend(X, Y) :-
    friend_(Y, X).

grandson(X, Y) :-
    grandchild(X, Y),
    male(Y).

:- dynamic friend_/2.

friend_("Alvaro Murphey", "Anna Vandenberg").
friend_("Alvaro Murphey", "Ophelia Mcgough").
friend_("Alvaro Murphey", "Brigida Oberg").
friend_("Alvaro Murphey", "Sarah Oberg").
friend_("Alvaro Murphey", "Morgan Remillard").
friend_("Alvaro Murphey", "Wanita Remillard").
friend_("Amy Wilke", "Clyde Oberg").
friend_("Amy Wilke", "Marlo Oberg").
friend_("Amy Wilke", "Owen Narvaez").
friend_("Amy Wilke", "Aurelia Dishman").
friend_("Amy Wilke", "Tianna Remillard").
friend_("Anna Vandenberg", "Delsie Mcgough").
friend_("Anna Vandenberg", "Ophelia Mcgough").
friend_("Anna Vandenberg", "Kirsten Oberg").
friend_("Anna Vandenberg", "Morgan Remillard").
friend_("Anna Vandenberg", "Sherrie Remillard").
friend_("Belva Murphey", "Ophelia Mcgough").
friend_("Belva Murphey", "Stacey Wilke").
friend_("Belva Murphey", "Hunter Remillard").
friend_("Belva Murphey", "Jaime Remillard").
friend_("Belva Murphey", "Morgan Remillard").
friend_("Belva Murphey", "Thomas Chrisman").
friend_("Charley Vandenberg", "Elroy Mcgough").
friend_("Charley Vandenberg", "Luke Wilke").
friend_("Charley Vandenberg", "Tashina Vandenberg").
friend_("Charley Vandenberg", "Cherlyn Oberg").
friend_("Charley Vandenberg", "Colby Narvaez").
friend_("Charley Vandenberg", "Twila Oberg").
friend_("Charley Vandenberg", "King Dishman").
friend_("Charley Vandenberg", "Morgan Remillard").
friend_("Chrissy Mcgough", "Tashina Vandenberg").
friend_("Chrissy Mcgough", "Kirsten Oberg").
friend_("Chrissy Mcgough", "Mason Oberg").
friend_("Chrissy Mcgough", "Sherrie Remillard").
friend_("Clara Mcgough", "Marion Wilke").
friend_("Clara Mcgough", "Demarcus Narvaez").
friend_("Clara Mcgough", "Lyman Oberg").
friend_("Clara Mcgough", "Marlo Oberg").
friend_("Clara Mcgough", "Monte Oberg").
friend_("Clara Mcgough", "Thomas Chrisman").
friend_("Delsie Mcgough", "Jackie Vandenberg").
friend_("Delsie Mcgough", "Cherlyn Oberg").
friend_("Delsie Mcgough", "Aurelia Dishman").
friend_("Eli Vandenberg", "Elroy Mcgough").
friend_("Eli Vandenberg", "Kori Remillard").
friend_("Eli Vandenberg", "Thomas Chrisman").
friend_("Elroy Mcgough", "Colby Narvaez").
friend_("Elroy Mcgough", "Rhoda Narvaez").
friend_("Elroy Mcgough", "Dorinda Chrisman").
friend_("Elroy Mcgough", "Mai Remillard").
friend_("Elroy Mcgough", "Sherrie Remillard").
friend_("Jackie Vandenberg", "Thelma Vandenberg").
friend_("Jackie Vandenberg", "Brigida Oberg").
friend_("Jackie Vandenberg", "Clyde Oberg").
friend_("Jackie Vandenberg", "Colby Narvaez").
friend_("Jackie Vandenberg", "Chrissy Remillard").
friend_("Jackie Vandenberg", "Louann Chrisman").
friend_("Luke Wilke", "Randall Mcgough").
friend_("Luke Wilke", "Abel Oberg").
friend_("Luke Wilke", "King Dishman").
friend_("Marion Wilke", "Tashina Vandenberg").
friend_("Marion Wilke", "Hunter Remillard").
friend_("Marion Wilke", "King Dishman").
friend_("Marion Wilke", "Willie Remillard").
friend_("Myrl Mcgough", "Monte Oberg").
friend_("Myrl Mcgough", "Twila Oberg").
friend_("Ophelia Mcgough", "Thelma Vandenberg").
friend_("Ophelia Mcgough", "Cherlyn Oberg").
friend_("Ophelia Mcgough", "Clyde Oberg").
friend_("Ophelia Mcgough", "Owen Narvaez").
friend_("Ophelia Mcgough", "Jaime Remillard").
friend_("Ophelia Mcgough", "Justine Remillard").
friend_("Ophelia Mcgough", "Margie Remillard").
friend_("Ophelia Mcgough", "Wanita Remillard").
friend_("Randall Mcgough", "Cherlyn Oberg").
friend_("Randall Mcgough", "Sarah Oberg").
friend_("Randall Mcgough", "Aurelia Dishman").
friend_("Stacey Wilke", "Demarcus Narvaez").
friend_("Stacey Wilke", "Aurelia Dishman").
friend_("Stacey Wilke", "Chrissy Remillard").
friend_("Stacey Wilke", "Kori Remillard").
friend_("Tashina Vandenberg", "Richard Oberg").
friend_("Tashina Vandenberg", "Aurelia Dishman").
friend_("Thelma Vandenberg", "Cherlyn Oberg").
friend_("Thelma Vandenberg", "Clyde Oberg").
friend_("Thelma Vandenberg", "Rhoda Narvaez").
friend_("Thelma Vandenberg", "Louann Chrisman").
friend_("Thelma Vandenberg", "Margie Remillard").
friend_("Valentin Vandenberg", "Amos Oberg").
friend_("Valentin Vandenberg", "Owen Narvaez").
friend_("Valentin Vandenberg", "Chrissy Remillard").
friend_("Valentin Vandenberg", "Dorinda Chrisman").
friend_("Valentin Vandenberg", "Louann Chrisman").
friend_("Abel Oberg", "Amos Oberg").
friend_("Abel Oberg", "Jude Remillard").
friend_("Amos Oberg", "Bryce Oberg").
friend_("Amos Oberg", "Clyde Oberg").
friend_("Amos Oberg", "Marlo Oberg").
friend_("Amos Oberg", "Morgan Remillard").
friend_("Amos Oberg", "Tianna Remillard").
friend_("Brigida Oberg", "Renate Oberg").
friend_("Brigida Oberg", "Jaime Remillard").
friend_("Brigida Oberg", "Kori Remillard").
friend_("Brigida Oberg", "Tianna Remillard").
friend_("Bryce Oberg", "Louann Chrisman").
friend_("Bryce Oberg", "Tianna Remillard").
friend_("Cherlyn Oberg", "Richard Oberg").
friend_("Cherlyn Oberg", "Sherrie Remillard").
friend_("Cherlyn Oberg", "Wanita Remillard").
friend_("Clyde Oberg", "Morgan Remillard").
friend_("Clyde Oberg", "Tianna Remillard").
friend_("Colby Narvaez", "Jaime Remillard").
friend_("Colby Narvaez", "Louann Chrisman").
friend_("Demarcus Narvaez", "Richard Oberg").
friend_("Demarcus Narvaez", "Jon Remillard").
friend_("Demarcus Narvaez", "Kori Remillard").
friend_("Demarcus Narvaez", "Morgan Remillard").
friend_("Demarcus Narvaez", "Wanita Remillard").
friend_("Kirsten Oberg", "Chrissy Remillard").
friend_("Kirsten Oberg", "Jon Remillard").
friend_("Kirsten Oberg", "Mai Remillard").
friend_("Luisa Narvaez", "Lyman Oberg").
friend_("Luisa Narvaez", "Rhoda Narvaez").
friend_("Luisa Narvaez", "Sarah Oberg").
friend_("Lyman Oberg", "Owen Narvaez").
friend_("Lyman Oberg", "Rhoda Narvaez").
friend_("Marlo Oberg", "Twila Oberg").
friend_("Marlo Oberg", "Willie Remillard").
friend_("Mason Oberg", "Aurelia Dishman").
friend_("Mason Oberg", "Sherrie Remillard").
friend_("Owen Narvaez", "Rhoda Narvaez").
friend_("Owen Narvaez", "Dani Remillard").
friend_("Owen Narvaez", "Justine Remillard").
friend_("Renate Oberg", "Sarah Oberg").
friend_("Renate Oberg", "Thomas Chrisman").
friend_("Rhoda Narvaez", "Jaime Remillard").
friend_("Rhoda Narvaez", "King Dishman").
friend_("Richard Oberg", "Kori Remillard").
friend_("Richard Oberg", "Louann Chrisman").
friend_("Richard Oberg", "Sherrie Remillard").
friend_("Twila Oberg", "Morgan Remillard").
friend_("Aurelia Dishman", "Celestine Remillard").
friend_("Aurelia Dishman", "Margie Remillard").
friend_("Aurelia Dishman", "Tianna Remillard").
friend_("Aurelia Dishman", "Willie Remillard").
friend_("Dani Remillard", "Dorinda Chrisman").
friend_("Dani Remillard", "Justine Remillard").
friend_("Dani Remillard", "Tianna Remillard").
friend_("Dani Remillard", "Willie Remillard").
friend_("Dorinda Chrisman", "Morgan Remillard").
friend_("Dorinda Chrisman", "Thomas Chrisman").
friend_("Hunter Remillard", "Morgan Remillard").
friend_("Hunter Remillard", "Sherrie Remillard").
friend_("Jaime Remillard", "Jon Remillard").
friend_("Jaime Remillard", "Jude Remillard").
friend_("Jaime Remillard", "King Dishman").
friend_("Jaime Remillard", "Sherrie Remillard").
friend_("Jon Remillard", "Mai Remillard").
friend_("Jon Remillard", "Thomas Chrisman").
friend_("Jude Remillard", "Morgan Remillard").
friend_("Justine Remillard", "King Dishman").
friend_("Justine Remillard", "Kori Remillard").
friend_("Louann Chrisman", "Sherrie Remillard").
friend_("Sherrie Remillard", "Willie Remillard").

granddaughter(X, Y) :-
    grandchild(X, Y),
    female(Y).

:- dynamic goal_expansion/2.
:- multifile goal_expansion/2.


grandchild(X, Y) :-
    grandparent(Y, X).

:- dynamic attribute/1.

attribute("general practice doctor").
attribute("sports science").
attribute("network engineer").
attribute("softball").
attribute("fine artist").
attribute("research").
attribute("psychiatric nurse").
attribute("science and technology studies").
attribute("newspaper journalist").
attribute("book collecting").
attribute("geoscientist").
attribute("stone collecting").
attribute("clinical research associate").
attribute("kart racing").
attribute("animal nutritionist").
attribute("lacrosse").
attribute("civil service fast streamer").
attribute("auto audiophilia").
attribute("gaffer").
attribute("photography").
attribute("production engineer").
attribute("insect collecting").
attribute("firefighter").
attribute("video game collecting").
attribute("biomedical engineer").
attribute("whale watching").
attribute("diagnostic radiographer").
attribute("research").
attribute("architect").
attribute("leaves").
attribute("careers information officer").
attribute("fishkeeping").
attribute("health promotion specialist").
attribute("philosophy").
attribute("astronomer").
attribute("base jumping").
attribute("trading standards officer").
attribute("herping").
attribute("leisure centre manager").
attribute("magic").
attribute("charity fundraiser").
attribute("slot car").
attribute("ceramics designer").
attribute("rugby league football").
attribute("environmental manager").
attribute("publishing").
attribute("local government officer").
attribute("shortwave listening").
attribute("computer games developer").
attribute("knife throwing").
attribute("barrister's clerk").
attribute("benchmarking").
attribute("IT trainer").
attribute("figure skating").
attribute("associate professor").
attribute("audiophile").
attribute("data scientist").
attribute("flower collecting and pressing").
attribute("horticultural consultant").
attribute("handball").
attribute("leisure centre manager").
attribute("scouting").
attribute("multimedia programmer").
attribute("vr gaming").
attribute("speech and language therapist").
attribute("fishkeeping").
attribute("chemist").
attribute("herbalism").
attribute("psychotherapist").
attribute("mycology").
attribute("optometrist").
attribute("benchmarking").
attribute("data processing manager").
attribute("ant farming").
attribute("music tutor").
attribute("surfing").
attribute("conservation officer").
attribute("bridge").
attribute("government social research officer").
attribute("mineral collecting").
attribute("nurse").
attribute("karting").
attribute("midwife").
attribute("stuffed toy collecting").
attribute("veterinary surgeon").
attribute("horsemanship").
attribute("research scientist").
attribute("history").
attribute("hospital doctor").
attribute("herping").
attribute("paediatric nurse").
attribute("research").
attribute("software engineer").
attribute("people-watching").
attribute("professor emeritus").
attribute("foraging").
attribute("secretary").
attribute("record collecting").
attribute("broadcast journalist").
attribute("climbing").
attribute("diagnostic radiographer").
attribute("benchmarking").
attribute("scientist").
attribute("aircraft spotting").
attribute("chartered loss adjuster").
attribute("gongoozling").
attribute("diplomatic services operational officer").
attribute("butterfly watching").
attribute("film editor").
attribute("reading").
attribute("interpreter").
attribute("radio-controlled model playing").
attribute("exhibitions officer").
attribute("leaves").
attribute("forensic psychologist").
attribute("metal detecting").
attribute("facilities manager").
attribute("biology").
attribute("radiographer").
attribute("button collecting").
attribute("press photographer").
attribute("reading").

great_uncle(X, Y) :-
    grandparent(X, A),
    brother(A, Y).

:- dynamic type/2.

type("Alvaro Murphey", person).
type("Amy Wilke", person).
type("Anna Vandenberg", person).
type("Belva Murphey", person).
type("Charley Vandenberg", person).
type("Chrissy Mcgough", person).
type("Clara Mcgough", person).
type("Delsie Mcgough", person).
type("Eli Vandenberg", person).
type("Elroy Mcgough", person).
type("Jackie Vandenberg", person).
type("Luke Wilke", person).
type("Marion Wilke", person).
type("Myrl Mcgough", person).
type("Ophelia Mcgough", person).
type("Randall Mcgough", person).
type("Stacey Wilke", person).
type("Tashina Vandenberg", person).
type("Thelma Vandenberg", person).
type("Valentin Vandenberg", person).
type("Abel Oberg", person).
type("Amos Oberg", person).
type("Brigida Oberg", person).
type("Bryce Oberg", person).
type("Cherlyn Oberg", person).
type("Clyde Oberg", person).
type("Colby Narvaez", person).
type("Demarcus Narvaez", person).
type("Kirsten Oberg", person).
type("Luisa Narvaez", person).
type("Lyman Oberg", person).
type("Marlo Oberg", person).
type("Mason Oberg", person).
type("Monte Oberg", person).
type("Owen Narvaez", person).
type("Renate Oberg", person).
type("Rhoda Narvaez", person).
type("Richard Oberg", person).
type("Sarah Oberg", person).
type("Twila Oberg", person).
type("Aurelia Dishman", person).
type("Celestine Remillard", person).
type("Chrissy Remillard", person).
type("Dani Remillard", person).
type("Dorinda Chrisman", person).
type("Hunter Remillard", person).
type("Jaime Remillard", person).
type("Jon Remillard", person).
type("Jude Remillard", person).
type("Justine Remillard", person).
type("King Dishman", person).
type("Kori Remillard", person).
type("Louann Chrisman", person).
type("Mai Remillard", person).
type("Margie Remillard", person).
type("Morgan Remillard", person).
type("Sherrie Remillard", person).
type("Thomas Chrisman", person).
type("Tianna Remillard", person).
type("Wanita Remillard", person).
type("Willie Remillard", person).

:- dynamic dob/2.

dob("Alvaro Murphey", "0287-02-19").
dob("Amy Wilke", "0255-06-20").
dob("Anna Vandenberg", "0281-04-07").
dob("Belva Murphey", "0283-07-02").
dob("Charley Vandenberg", "0260-11-29").
dob("Chrissy Mcgough", "0289-07-11").
dob("Clara Mcgough", "0342-04-12").
dob("Delsie Mcgough", "0348-09-23").
dob("Eli Vandenberg", "0257-03-19").
dob("Elroy Mcgough", "0290-03-23").
dob("Jackie Vandenberg", "0229-11-20").
dob("Luke Wilke", "0279-08-11").
dob("Marion Wilke", "0277-08-23").
dob("Myrl Mcgough", "0317-02-01").
dob("Ophelia Mcgough", "0319-06-24").
dob("Randall Mcgough", "0317-09-07").
dob("Stacey Wilke", "0255-02-12").
dob("Tashina Vandenberg", "0255-11-11").
dob("Thelma Vandenberg", "0253-04-23").
dob("Valentin Vandenberg", "0230-09-10").
dob("Abel Oberg", "0250-05-14").
dob("Amos Oberg", "0336-02-04").
dob("Brigida Oberg", "0275-01-22").
dob("Bryce Oberg", "0274-08-26").
dob("Cherlyn Oberg", "0302-06-08").
dob("Clyde Oberg", "0302-09-30").
dob("Colby Narvaez", "0331-03-22").
dob("Demarcus Narvaez", "0358-04-15").
dob("Kirsten Oberg", "0302-08-17").
dob("Luisa Narvaez", "0331-11-11").
dob("Lyman Oberg", "0305-04-10").
dob("Marlo Oberg", "0301-09-01").
dob("Mason Oberg", "0333-10-28").
dob("Monte Oberg", "0301-01-28").
dob("Owen Narvaez", "0387-12-26").
dob("Renate Oberg", "0250-03-15").
dob("Rhoda Narvaez", "0362-09-25").
dob("Richard Oberg", "0277-09-28").
dob("Sarah Oberg", "0328-04-20").
dob("Twila Oberg", "0329-06-22").
dob("Aurelia Dishman", "0247-09-06").
dob("Celestine Remillard", "0353-09-20").
dob("Chrissy Remillard", "0324-06-28").
dob("Dani Remillard", "0318-04-07").
dob("Dorinda Chrisman", "0377-10-29").
dob("Hunter Remillard", "0321-09-02").
dob("Jaime Remillard", "0293-09-03").
dob("Jon Remillard", "0272-10-16").
dob("Jude Remillard", "0298-02-17").
dob("Justine Remillard", "0351-10-03").
dob("King Dishman", "0247-09-28").
dob("Kori Remillard", "0325-09-08").
dob("Louann Chrisman", "0349-07-04").
dob("Mai Remillard", "0382-10-12").
dob("Margie Remillard", "0320-07-24").
dob("Morgan Remillard", "0289-11-21").
dob("Sherrie Remillard", "0271-04-26").
dob("Thomas Chrisman", "0348-02-02").
dob("Tianna Remillard", "0298-07-09").
dob("Wanita Remillard", "0299-11-29").
dob("Willie Remillard", "0351-02-21").

great_aunt(X, Y) :-
    grandparent(X, A),
    sister(A, Y).

:- dynamic message_hook/3.
:- multifile message_hook/3.


:- dynamic job/2.

job("Alvaro Murphey", "general practice doctor").
job("Amy Wilke", "network engineer").
job("Anna Vandenberg", "fine artist").
job("Belva Murphey", "psychiatric nurse").
job("Charley Vandenberg", "newspaper journalist").
job("Chrissy Mcgough", "geoscientist").
job("Clara Mcgough", "clinical research associate").
job("Delsie Mcgough", "animal nutritionist").
job("Eli Vandenberg", "civil service fast streamer").
job("Elroy Mcgough", "gaffer").
job("Jackie Vandenberg", "production engineer").
job("Luke Wilke", "firefighter").
job("Marion Wilke", "biomedical engineer").
job("Myrl Mcgough", "diagnostic radiographer").
job("Ophelia Mcgough", "architect").
job("Randall Mcgough", "careers information officer").
job("Stacey Wilke", "health promotion specialist").
job("Tashina Vandenberg", "astronomer").
job("Thelma Vandenberg", "trading standards officer").
job("Valentin Vandenberg", "leisure centre manager").
job("Abel Oberg", "charity fundraiser").
job("Amos Oberg", "ceramics designer").
job("Brigida Oberg", "environmental manager").
job("Bryce Oberg", "local government officer").
job("Cherlyn Oberg", "computer games developer").
job("Clyde Oberg", "barrister's clerk").
job("Colby Narvaez", "IT trainer").
job("Demarcus Narvaez", "associate professor").
job("Kirsten Oberg", "data scientist").
job("Luisa Narvaez", "horticultural consultant").
job("Lyman Oberg", "leisure centre manager").
job("Marlo Oberg", "multimedia programmer").
job("Mason Oberg", "speech and language therapist").
job("Monte Oberg", "chemist").
job("Owen Narvaez", "psychotherapist").
job("Renate Oberg", "optometrist").
job("Rhoda Narvaez", "data processing manager").
job("Richard Oberg", "music tutor").
job("Sarah Oberg", "conservation officer").
job("Twila Oberg", "government social research officer").
job("Aurelia Dishman", "nurse").
job("Celestine Remillard", "midwife").
job("Chrissy Remillard", "veterinary surgeon").
job("Dani Remillard", "research scientist").
job("Dorinda Chrisman", "hospital doctor").
job("Hunter Remillard", "paediatric nurse").
job("Jaime Remillard", "software engineer").
job("Jon Remillard", "professor emeritus").
job("Jude Remillard", "secretary").
job("Justine Remillard", "broadcast journalist").
job("King Dishman", "diagnostic radiographer").
job("Kori Remillard", "scientist").
job("Louann Chrisman", "chartered loss adjuster").
job("Mai Remillard", "diplomatic services operational officer").
job("Margie Remillard", "film editor").
job("Morgan Remillard", "interpreter").
job("Sherrie Remillard", "exhibitions officer").
job("Thomas Chrisman", "forensic psychologist").
job("Tianna Remillard", "facilities manager").
job("Wanita Remillard", "radiographer").
job("Willie Remillard", "press photographer").

:- dynamic expand_query/4.
:- multifile expand_query/4.


grandfather(X, Y) :-
    grandparent(X, Y),
    male(Y).

:- dynamic save_all_clauses_to_file/1.

save_all_clauses_to_file(A) :-
    open(A, write, B),
    set_output(B),
    listing,
    close(B).

grandmother(X, Y) :-
    grandparent(X, Y),
    female(Y).

:- thread_local thread_message_hook/3.
:- dynamic thread_message_hook/3.
:- volatile thread_message_hook/3.

%   No thread has clauses for thread_message_hook/3

:- dynamic hobby/2.

hobby("Alvaro Murphey", "sports science").
hobby("Amy Wilke", "softball").
hobby("Anna Vandenberg", "research").
hobby("Belva Murphey", "science and technology studies").
hobby("Charley Vandenberg", "book collecting").
hobby("Chrissy Mcgough", "stone collecting").
hobby("Clara Mcgough", "kart racing").
hobby("Delsie Mcgough", "lacrosse").
hobby("Eli Vandenberg", "auto audiophilia").
hobby("Elroy Mcgough", "photography").
hobby("Jackie Vandenberg", "insect collecting").
hobby("Luke Wilke", "video game collecting").
hobby("Marion Wilke", "whale watching").
hobby("Myrl Mcgough", "research").
hobby("Ophelia Mcgough", "leaves").
hobby("Randall Mcgough", "fishkeeping").
hobby("Stacey Wilke", "philosophy").
hobby("Tashina Vandenberg", "base jumping").
hobby("Thelma Vandenberg", "herping").
hobby("Valentin Vandenberg", "magic").
hobby("Abel Oberg", "slot car").
hobby("Amos Oberg", "rugby league football").
hobby("Brigida Oberg", "publishing").
hobby("Bryce Oberg", "shortwave listening").
hobby("Cherlyn Oberg", "knife throwing").
hobby("Clyde Oberg", "benchmarking").
hobby("Colby Narvaez", "figure skating").
hobby("Demarcus Narvaez", "audiophile").
hobby("Kirsten Oberg", "flower collecting and pressing").
hobby("Luisa Narvaez", "handball").
hobby("Lyman Oberg", "scouting").
hobby("Marlo Oberg", "vr gaming").
hobby("Mason Oberg", "fishkeeping").
hobby("Monte Oberg", "herbalism").
hobby("Owen Narvaez", "mycology").
hobby("Renate Oberg", "benchmarking").
hobby("Rhoda Narvaez", "ant farming").
hobby("Richard Oberg", "surfing").
hobby("Sarah Oberg", "bridge").
hobby("Twila Oberg", "mineral collecting").
hobby("Aurelia Dishman", "karting").
hobby("Celestine Remillard", "stuffed toy collecting").
hobby("Chrissy Remillard", "horsemanship").
hobby("Dani Remillard", "history").
hobby("Dorinda Chrisman", "herping").
hobby("Hunter Remillard", "research").
hobby("Jaime Remillard", "people-watching").
hobby("Jon Remillard", "foraging").
hobby("Jude Remillard", "record collecting").
hobby("Justine Remillard", "climbing").
hobby("King Dishman", "benchmarking").
hobby("Kori Remillard", "aircraft spotting").
hobby("Louann Chrisman", "gongoozling").
hobby("Mai Remillard", "butterfly watching").
hobby("Margie Remillard", "reading").
hobby("Morgan Remillard", "radio-controlled model playing").
hobby("Sherrie Remillard", "leaves").
hobby("Thomas Chrisman", "metal detecting").
hobby("Tianna Remillard", "biology").
hobby("Wanita Remillard", "button collecting").
hobby("Willie Remillard", "reading").

grandparent(X, Y) :-
    parent(X, Z),
    parent(Z, Y).

nephew(X, Y) :-
    sibling(X, A),
    son(A, Y).

niece(X, Y) :-
    sibling(X, A),
    daughter(A, Y).

:- dynamic library_directory/1.
:- multifile library_directory/1.


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

husband(X, Y) :-
    married(X, Y),
    male(Y).

wife(X, Y) :-
    married(X, Y),
    female(Y).
