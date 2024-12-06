
:- dynamic term_expansion/2.
:- multifile term_expansion/2.


great_grandchild(X, Y) :-
    great_grandparent(Y, X).

:- dynamic attribute/1.

attribute(contractor).
attribute(meditation).
attribute('teacher, adult education').
attribute(meteorology).
attribute('biomedical scientist').
attribute(biology).
attribute('freight forwarder').
attribute(meteorology).
attribute('commercial/residential surveyor').
attribute(dolls).
attribute('research scientist (life sciences)').
attribute(photography).
attribute('production assistant, television').
attribute(shogi).
attribute('public house manager').
attribute(dominoes).
attribute('museum education officer').
attribute('tether car').
attribute('engineer, manufacturing systems').
attribute(architecture).
attribute('chief marketing officer').
attribute(geocaching).
attribute('ranger/warden').
attribute(trainspotting).
attribute('air cabin crew').
attribute('bus spotting').
attribute('newspaper journalist').
attribute(research).
attribute('police officer').
attribute(geography).
attribute(translator).
attribute(microbiology).
attribute('accountant, chartered').
attribute(canoeing).
attribute('product designer').
attribute(learning).
attribute('geographical information systems officer').
attribute('dairy farming').
attribute('estate manager/land agent').
attribute('fossil hunting').
attribute('therapist, art').
attribute(sociology).
attribute('civil engineer, consulting').
attribute(finance).
attribute('investment banker, corporate').
attribute(meditation).
attribute('airline pilot').
attribute('wikipedia editing').
attribute('advertising copywriter').
attribute('radio-controlled car racing').
attribute('agricultural engineer').
attribute('social studies').

great_granddaughter(X, Y) :-
    great_grandchild(X, Y),
    female(Y).

great_grandmother(X, Y) :-
    great_grandparent(X, Y),
    female(Y).

great_grandfather(X, Y) :-
    great_grandparent(X, Y),
    male(Y).

:- dynamic library_directory/1.
:- multifile library_directory/1.


grandson(X, Y) :-
    grandchild(X, Y),
    male(Y).

great_grandparent(X, Y) :-
    grandparent(X, Z),
    parent(Z, Y).

:- dynamic term_expansion/4.
:- multifile term_expansion/4.


grandchild(X, Y) :-
    grandparent(Y, X).

:- dynamic goal_expansion/4.
:- multifile goal_expansion/4.


granddaughter(X, Y) :-
    grandchild(X, Y),
    female(Y).

great_aunt(X, Y) :-
    grandparent(X, A),
    sister(A, Y).

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

great_uncle(X, Y) :-
    grandparent(X, A),
    brother(A, Y).

grandmother(X, Y) :-
    grandparent(X, Y),
    female(Y).

:- multifile prolog_list_goal/1.


grandfather(X, Y) :-
    grandparent(X, Y),
    male(Y).

:- dynamic hobby/2.

hobby(alfonso, meditation).
hobby(alton, meteorology).
hobby(antionette, biology).
hobby(colby, meteorology).
hobby(daisy, dolls).
hobby(deangelo, photography).
hobby(deanna, shogi).
hobby(derick, dominoes).
hobby(dixie, 'tether car').
hobby(dominick, architecture).
hobby(ellis, geocaching).
hobby(ila, trainspotting).
hobby(johnna, 'bus spotting').
hobby(kanesha, research).
hobby(kari, geography).
hobby(lyndia, microbiology).
hobby(maggie, canoeing).
hobby(matt, learning).
hobby(meghann, 'dairy farming').
hobby(miki, 'fossil hunting').
hobby(reyna, sociology).
hobby(rosalee, finance).
hobby(scotty, meditation).
hobby(tanner, 'wikipedia editing').
hobby(thomasine, 'radio-controlled car racing').
hobby(vicente, 'social studies').

nephew(X, Y) :-
    sibling(X, A),
    son(A, Y).

grandparent(X, Y) :-
    parent(X, Z),
    parent(Z, Y).

:- dynamic job/2.

job(alfonso, contractor).
job(alton, 'teacher, adult education').
job(antionette, 'biomedical scientist').
job(colby, 'freight forwarder').
job(daisy, 'commercial/residential surveyor').
job(deangelo, 'research scientist (life sciences)').
job(deanna, 'production assistant, television').
job(derick, 'public house manager').
job(dixie, 'museum education officer').
job(dominick, 'engineer, manufacturing systems').
job(ellis, 'chief marketing officer').
job(ila, 'ranger/warden').
job(johnna, 'air cabin crew').
job(kanesha, 'newspaper journalist').
job(kari, 'police officer').
job(lyndia, translator).
job(maggie, 'accountant, chartered').
job(matt, 'product designer').
job(meghann, 'geographical information systems officer').
job(miki, 'estate manager/land agent').
job(reyna, 'therapist, art').
job(rosalee, 'civil engineer, consulting').
job(scotty, 'investment banker, corporate').
job(tanner, 'airline pilot').
job(thomasine, 'advertising copywriter').
job(vicente, 'agricultural engineer').

:- dynamic expand_query/4.
:- multifile expand_query/4.


:- dynamic dob/2.

dob(alfonso, '0240-12-31').
dob(alton, '0263-06-10').
dob(antionette, '0239-10-28').
dob(colby, '0244-04-07').
dob(daisy, '0237-11-04').
dob(deangelo, '0239-07-26').
dob(deanna, '0270-07-11').
dob(derick, '0212-09-01').
dob(dixie, '0270-01-28').
dob(dominick, '0236-06-02').
dob(ellis, '0272-04-21').
dob(ila, '0241-07-17').
dob(johnna, '0264-08-02').
dob(kanesha, '0212-07-22').
dob(kari, '0238-10-28').
dob(lyndia, '0178-04-18').
dob(maggie, '0148-03-17').
dob(matt, '0205-10-16').
dob(meghann, '0230-04-06').
dob(miki, '0256-10-26').
dob(reyna, '0261-08-01').
dob(rosalee, '0260-09-04').
dob(scotty, '0149-12-17').
dob(tanner, '0231-07-16').
dob(thomasine, '0204-09-13').
dob(vicente, '0178-01-25').

husband(X, Y) :-
    married(X, Y),
    male(Y).

:- multifile message_property/2.


niece(X, Y) :-
    sibling(X, A),
    daughter(A, Y).

:- dynamic type/2.

type(alfonso, person).
type(alton, person).
type(antionette, person).
type(colby, person).
type(daisy, person).
type(deangelo, person).
type(deanna, person).
type(derick, person).
type(dixie, person).
type(dominick, person).
type(ellis, person).
type(ila, person).
type(johnna, person).
type(kanesha, person).
type(kari, person).
type(lyndia, person).
type(maggie, person).
type(matt, person).
type(meghann, person).
type(miki, person).
type(reyna, person).
type(rosalee, person).
type(scotty, person).
type(tanner, person).
type(thomasine, person).
type(vicente, person).

daughter(X, Y) :-
    child(X, Y),
    female(Y).

:- dynamic expand_answer/2.
:- multifile expand_answer/2.


wife(X, Y) :-
    married(X, Y),
    female(Y).

male(X) :-
    gender(X, male).

:- dynamic friend_/2.

friend_(alfonso, alton).
friend_(alfonso, colby).
friend_(alfonso, derick).
friend_(alfonso, miki).
friend_(alton, colby).
friend_(alton, derick).
friend_(alton, kari).
friend_(alton, miki).
friend_(antionette, daisy).
friend_(antionette, dominick).
friend_(antionette, matt).
friend_(antionette, tanner).
friend_(antionette, thomasine).
friend_(colby, derick).
friend_(colby, kari).
friend_(colby, miki).
friend_(daisy, dominick).
friend_(daisy, matt).
friend_(daisy, tanner).
friend_(daisy, thomasine).
friend_(deangelo, dominick).
friend_(deangelo, ila).
friend_(deangelo, maggie).
friend_(deangelo, meghann).
friend_(deangelo, reyna).
friend_(deangelo, rosalee).
friend_(deanna, dixie).
friend_(deanna, ellis).
friend_(deanna, kanesha).
friend_(deanna, lyndia).
friend_(derick, kari).
friend_(derick, miki).
friend_(dixie, ellis).
friend_(dixie, kanesha).
friend_(dixie, lyndia).
friend_(dominick, ila).
friend_(dominick, maggie).
friend_(dominick, matt).
friend_(dominick, meghann).
friend_(dominick, reyna).
friend_(dominick, rosalee).
friend_(dominick, tanner).
friend_(dominick, thomasine).
friend_(ellis, kanesha).
friend_(ellis, lyndia).
friend_(ila, maggie).
friend_(ila, meghann).
friend_(ila, reyna).
friend_(ila, rosalee).
friend_(johnna, scotty).
friend_(kanesha, lyndia).
friend_(kanesha, scotty).
friend_(kanesha, vicente).
friend_(kari, miki).
friend_(lyndia, vicente).
friend_(maggie, meghann).
friend_(maggie, reyna).
friend_(maggie, rosalee).
friend_(matt, tanner).
friend_(matt, thomasine).
friend_(meghann, reyna).
friend_(meghann, rosalee).
friend_(reyna, rosalee).
friend_(tanner, thomasine).

child(X, Y) :-
    parent(Y, X).

son(X, Y) :-
    child(X, Y),
    male(Y).

friend(X, Y) :-
    friend_(X, Y).
friend(X, Y) :-
    friend_(Y, X).

female(X) :-
    gender(X, female).

:- dynamic exception/3.
:- multifile exception/3.


male_first_cousin_once_removed(X, Y) :-
    cousin(X, A),
    son(A, Y),
    X\=Y.

mother(X, Y) :-
    parent(X, Y),
    female(Y).

:- thread_local thread_message_hook/3.
:- dynamic thread_message_hook/3.
:- volatile thread_message_hook/3.


father(X, Y) :-
    parent(X, Y),
    male(Y).

female_first_cousin_once_removed(X, Y) :-
    cousin(X, A),
    daughter(A, Y),
    X\=Y.

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

:- multifile prolog_predicate_name/2.


male_second_cousin(X, Y) :-
    parent(X, A),
    parent(Y, B),
    cousin(A, B),
    male(Y),
    X\=Y.

sister(Y, X) :-
    sibling(X, Y),
    female(X).

:- dynamic nonbinary/1.

nonbinary(X) :-
    gender(X, nonbinary).

:- dynamic message_hook/3.
:- multifile message_hook/3.


brother(X, Y) :-
    sibling(X, Y),
    male(Y).

female_second_cousin(X, Y) :-
    parent(X, A),
    parent(Y, B),
    cousin(A, B),
    female(Y),
    X\=Y.

male_cousin(X, Y) :-
    cousin(X, Y),
    male(Y).

:- dynamic parent/2.

parent(alfonso, derick).
parent(alfonso, kanesha).
parent(alton, antionette).
parent(alton, deangelo).
parent(antionette, derick).
parent(antionette, kanesha).
parent(colby, derick).
parent(colby, kanesha).
parent(daisy, matt).
parent(daisy, thomasine).
parent(deanna, daisy).
parent(deanna, dominick).
parent(dixie, antionette).
parent(dixie, deangelo).
parent(dominick, derick).
parent(dominick, kanesha).
parent(ellis, alfonso).
parent(ellis, ila).
parent(johnna, antionette).
parent(johnna, deangelo).
parent(kari, derick).
parent(kari, kanesha).
parent(lyndia, maggie).
parent(lyndia, scotty).
parent(matt, lyndia).
parent(matt, vicente).
parent(meghann, matt).
parent(meghann, thomasine).
parent(miki, meghann).
parent(miki, tanner).
parent(reyna, daisy).
parent(reyna, dominick).
parent(rosalee, daisy).
parent(rosalee, dominick).

:- dynamic resource/2.
:- multifile resource/2.


:- dynamic portray/1.
:- multifile portray/1.


:- dynamic goal_expansion/2.
:- multifile goal_expansion/2.


married(X, Y) :-
    parent(Child, X),
    parent(Child, Y),
    X\=Y.

female_cousin(X, Y) :-
    cousin(X, Y),
    female(Y).

:- dynamic prolog_load_file/2.
:- multifile prolog_load_file/2.


cousin(X, Y) :-
    parent(X, A),
    parent(Y, B),
    sibling(A, B),
    X\=Y.

sibling(X, Y) :-
    parent(X, A),
    parent(Y, A),
    X\=Y.

uncle(X, Y) :-
    parent(X, A),
    brother(A, Y).

:- dynamic resource/3.
:- multifile resource/3.


:- multifile prolog_clause_name/2.


aunt(X, Y) :-
    parent(X, A),
    sister(A, Y).

:- dynamic gender/2.

gender(alfonso, male).
gender(alton, male).
gender(antionette, female).
gender(colby, male).
gender(daisy, female).
gender(deangelo, male).
gender(deanna, female).
gender(derick, male).
gender(dixie, female).
gender(dominick, male).
gender(ellis, male).
gender(ila, female).
gender(johnna, female).
gender(kanesha, female).
gender(kari, female).
gender(lyndia, female).
gender(maggie, female).
gender(matt, male).
gender(meghann, female).
gender(miki, female).
gender(reyna, female).
gender(rosalee, female).
gender(scotty, male).
gender(tanner, male).
gender(thomasine, female).
gender(vicente, male).

:- dynamic save_all_clauses_to_file/1.

save_all_clauses_to_file(A) :-
    open(A, write, B),
    set_output(B),
    listing,
    close(B).

second_uncle(X, Y) :-
    great_grandparent(X, A),
    brother(A, Y).

second_aunt(X, Y) :-
    great_grandparent(X, A),
    sister(A, Y).

:- dynamic pyrun/2.

pyrun(A, B) :-
    read_term_from_atom(A, C, [variable_names(B)]),
    call(C).

great_grandson(X, Y) :-
    great_grandchild(X, Y),
    male(Y).
