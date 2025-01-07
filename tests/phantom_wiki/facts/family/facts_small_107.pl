
:- dynamic term_expansion/2.
:- multifile term_expansion/2.


great_grandchild(X, Y) :-
    great_grandparent(Y, X).

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

:- dynamic hobby/2.

hobby('Adele Ervin', meditation).
hobby('Alton Cater', meteorology).
hobby('Aubrey Leibowitz', biology).
hobby('Boris Ervin', meteorology).
hobby('Bruce Cater', dolls).
hobby('Delpha Donohue', photography).
hobby('Derick Backus', shogi).
hobby('Dirk Donohue', dominoes).
hobby('Ella Cater', 'tether car').
hobby('Gerry Donohue', architecture).
hobby('Gustavo Leibowitz', geocaching).
hobby('Jewel Backus', trainspotting).
hobby('Karen Ervin', 'bus spotting').
hobby('Lisha Leibowitz', research).
hobby('Margarite Ussery', geography).
hobby('Mason Donohue', microbiology).
hobby('Pedro Donohue', canoeing).
hobby('Rigoberto Bode', learning).
hobby('Staci Donohue', 'dairy farming').
hobby('Therese Donohue', 'fossil hunting').
hobby('Tiffany Bode', sociology).
hobby('Ty Donohue', finance).
hobby('Tyler Ussery', meditation).
hobby('Veronica Donohue', 'wikipedia editing').
hobby('Vita Cater', 'radio-controlled car racing').
hobby('Wes Backus', 'social studies').
hobby('Wilfredo Cater', judo).

:- dynamic term_expansion/4.
:- multifile term_expansion/4.


grandchild(X, Y) :-
    grandparent(Y, X).

:- dynamic goal_expansion/4.
:- multifile goal_expansion/4.


granddaughter(X, Y) :-
    grandchild(X, Y),
    female(Y).

:- dynamic job/2.

job('Adele Ervin', contractor).
job('Alton Cater', 'teacher, adult education').
job('Aubrey Leibowitz', 'biomedical scientist').
job('Boris Ervin', 'freight forwarder').
job('Bruce Cater', 'commercial/residential surveyor').
job('Delpha Donohue', 'research scientist (life sciences)').
job('Derick Backus', 'production assistant, television').
job('Dirk Donohue', 'public house manager').
job('Ella Cater', 'museum education officer').
job('Gerry Donohue', 'engineer, manufacturing systems').
job('Gustavo Leibowitz', 'chief marketing officer').
job('Jewel Backus', 'ranger/warden').
job('Karen Ervin', 'air cabin crew').
job('Lisha Leibowitz', 'newspaper journalist').
job('Margarite Ussery', 'police officer').
job('Mason Donohue', translator).
job('Pedro Donohue', 'accountant, chartered').
job('Rigoberto Bode', 'product designer').
job('Staci Donohue', 'geographical information systems officer').
job('Therese Donohue', 'estate manager/land agent').
job('Tiffany Bode', 'therapist, art').
job('Ty Donohue', 'civil engineer, consulting').
job('Tyler Ussery', 'investment banker, corporate').
job('Veronica Donohue', 'airline pilot').
job('Vita Cater', 'advertising copywriter').
job('Wes Backus', 'agricultural engineer').
job('Wilfredo Cater', 'special educational needs teacher').

:- dynamic save_all_clauses_to_file/1.

save_all_clauses_to_file(A) :-
    open(A, write, B),
    set_output(B),
    listing,
    close(B).

:- dynamic dob/2.

dob('Adele Ervin', '0259-06-10').
dob('Alton Cater', '0236-04-04').
dob('Aubrey Leibowitz', '0256-09-07').
dob('Boris Ervin', '0232-11-24').
dob('Bruce Cater', '0209-05-24').
dob('Delpha Donohue', '0171-04-12').
dob('Derick Backus', '0295-10-18').
dob('Dirk Donohue', '0167-06-08').
dob('Ella Cater', '0239-10-28').
dob('Gerry Donohue', '0192-01-16').
dob('Gustavo Leibowitz', '0280-04-21').
dob('Jewel Backus', '0268-03-07').
dob('Karen Ervin', '0231-09-29').
dob('Lisha Leibowitz', '0256-07-31').
dob('Margarite Ussery', '0205-09-12').
dob('Mason Donohue', '0143-10-16').
dob('Pedro Donohue', '0172-08-18').
dob('Rigoberto Bode', '0146-09-21').
dob('Staci Donohue', '0162-07-16').
dob('Therese Donohue', '0141-09-13').
dob('Tiffany Bode', '0145-02-06').
dob('Ty Donohue', '0170-06-04').
dob('Tyler Ussery', '0206-04-13').
dob('Veronica Donohue', '0174-07-16').
dob('Vita Cater', '0205-04-19').
dob('Wes Backus', '0268-09-01').
dob('Wilfredo Cater', '0263-03-03').

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

:- dynamic type/2.

type('Adele Ervin', person).
type('Alton Cater', person).
type('Aubrey Leibowitz', person).
type('Boris Ervin', person).
type('Bruce Cater', person).
type('Delpha Donohue', person).
type('Derick Backus', person).
type('Dirk Donohue', person).
type('Ella Cater', person).
type('Gerry Donohue', person).
type('Gustavo Leibowitz', person).
type('Jewel Backus', person).
type('Karen Ervin', person).
type('Lisha Leibowitz', person).
type('Margarite Ussery', person).
type('Mason Donohue', person).
type('Pedro Donohue', person).
type('Rigoberto Bode', person).
type('Staci Donohue', person).
type('Therese Donohue', person).
type('Tiffany Bode', person).
type('Ty Donohue', person).
type('Tyler Ussery', person).
type('Veronica Donohue', person).
type('Vita Cater', person).
type('Wes Backus', person).
type('Wilfredo Cater', person).

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
attribute('special educational needs teacher').
attribute(judo).

grandmother(X, Y) :-
    grandparent(X, Y),
    female(Y).

:- multifile prolog_list_goal/1.


grandfather(X, Y) :-
    grandparent(X, Y),
    male(Y).

:- dynamic friend_/2.

friend_('Adele Ervin', 'Alton Cater').
friend_('Adele Ervin', 'Boris Ervin').
friend_('Adele Ervin', 'Dirk Donohue').
friend_('Adele Ervin', 'Therese Donohue').
friend_('Adele Ervin', 'Wilfredo Cater').
friend_('Alton Cater', 'Boris Ervin').
friend_('Alton Cater', 'Dirk Donohue').
friend_('Alton Cater', 'Margarite Ussery').
friend_('Alton Cater', 'Therese Donohue').
friend_('Alton Cater', 'Wilfredo Cater').
friend_('Aubrey Leibowitz', 'Bruce Cater').
friend_('Aubrey Leibowitz', 'Gerry Donohue').
friend_('Aubrey Leibowitz', 'Rigoberto Bode').
friend_('Aubrey Leibowitz', 'Veronica Donohue').
friend_('Aubrey Leibowitz', 'Vita Cater').
friend_('Boris Ervin', 'Dirk Donohue').
friend_('Boris Ervin', 'Margarite Ussery').
friend_('Boris Ervin', 'Therese Donohue').
friend_('Boris Ervin', 'Wilfredo Cater').
friend_('Bruce Cater', 'Gerry Donohue').
friend_('Bruce Cater', 'Rigoberto Bode').
friend_('Bruce Cater', 'Veronica Donohue').
friend_('Bruce Cater', 'Vita Cater').
friend_('Delpha Donohue', 'Gerry Donohue').
friend_('Delpha Donohue', 'Jewel Backus').
friend_('Delpha Donohue', 'Pedro Donohue').
friend_('Delpha Donohue', 'Staci Donohue').
friend_('Delpha Donohue', 'Tiffany Bode').
friend_('Delpha Donohue', 'Ty Donohue').
friend_('Derick Backus', 'Ella Cater').
friend_('Derick Backus', 'Gustavo Leibowitz').
friend_('Derick Backus', 'Lisha Leibowitz').
friend_('Derick Backus', 'Mason Donohue').
friend_('Dirk Donohue', 'Margarite Ussery').
friend_('Dirk Donohue', 'Therese Donohue').
friend_('Dirk Donohue', 'Wilfredo Cater').
friend_('Ella Cater', 'Gustavo Leibowitz').
friend_('Ella Cater', 'Lisha Leibowitz').
friend_('Ella Cater', 'Mason Donohue').
friend_('Gerry Donohue', 'Jewel Backus').
friend_('Gerry Donohue', 'Pedro Donohue').
friend_('Gerry Donohue', 'Rigoberto Bode').
friend_('Gerry Donohue', 'Staci Donohue').
friend_('Gerry Donohue', 'Tiffany Bode').
friend_('Gerry Donohue', 'Ty Donohue').
friend_('Gerry Donohue', 'Veronica Donohue').
friend_('Gerry Donohue', 'Vita Cater').
friend_('Gustavo Leibowitz', 'Lisha Leibowitz').
friend_('Gustavo Leibowitz', 'Mason Donohue').
friend_('Jewel Backus', 'Pedro Donohue').
friend_('Jewel Backus', 'Staci Donohue').
friend_('Jewel Backus', 'Tiffany Bode').
friend_('Jewel Backus', 'Ty Donohue').
friend_('Karen Ervin', 'Tyler Ussery').
friend_('Lisha Leibowitz', 'Mason Donohue').
friend_('Lisha Leibowitz', 'Tyler Ussery').
friend_('Lisha Leibowitz', 'Wes Backus').
friend_('Margarite Ussery', 'Therese Donohue').
friend_('Margarite Ussery', 'Wilfredo Cater').
friend_('Mason Donohue', 'Wes Backus').
friend_('Pedro Donohue', 'Staci Donohue').
friend_('Pedro Donohue', 'Tiffany Bode').
friend_('Pedro Donohue', 'Ty Donohue').
friend_('Rigoberto Bode', 'Veronica Donohue').
friend_('Rigoberto Bode', 'Vita Cater').
friend_('Staci Donohue', 'Tiffany Bode').
friend_('Staci Donohue', 'Ty Donohue').
friend_('Therese Donohue', 'Wilfredo Cater').
friend_('Tiffany Bode', 'Ty Donohue').
friend_('Veronica Donohue', 'Vita Cater').

nephew(X, Y) :-
    sibling(X, A),
    son(A, Y).

grandparent(X, Y) :-
    parent(X, Z),
    parent(Z, Y).

friend(X, Y) :-
    friend_(X, Y).
friend(X, Y) :-
    friend_(Y, X).

:- dynamic expand_query/4.
:- multifile expand_query/4.


brother_in_law(X, Y) :-
    married(X, A),
    brother(A, Y).

husband(X, Y) :-
    married(X, Y),
    male(Y).

:- multifile message_property/2.


niece(X, Y) :-
    sibling(X, A),
    daughter(A, Y).

sister_in_law(X, Y) :-
    married(X, A),
    sister(A, Y).

daughter_in_law(X, Y) :-
    child(X, A),
    wife(A, Y).

daughter(X, Y) :-
    child(X, Y),
    female(Y).

:- dynamic expand_answer/2.
:- multifile expand_answer/2.


wife(X, Y) :-
    married(X, Y),
    female(Y).

son_in_law(X, Y) :-
    child(X, A),
    husband(A, Y).

male(X) :-
    gender(X, male).

father_in_law(X, Y) :-
    married(X, A),
    father(A, Y).

child(X, Y) :-
    parent(Y, X).

:- multifile prolog_clause_name/2.


son(X, Y) :-
    child(X, Y),
    male(Y).

mother_in_law(X, Y) :-
    married(X, A),
    mother(A, Y).

female(X) :-
    gender(X, female).

:- dynamic exception/3.
:- multifile exception/3.


:- multifile prolog_predicate_name/2.


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

parent('Adele Ervin', 'Boris Ervin').
parent('Adele Ervin', 'Karen Ervin').
parent('Alton Cater', 'Bruce Cater').
parent('Alton Cater', 'Vita Cater').
parent('Delpha Donohue', 'Rigoberto Bode').
parent('Delpha Donohue', 'Tiffany Bode').
parent('Derick Backus', 'Jewel Backus').
parent('Derick Backus', 'Wes Backus').
parent('Dirk Donohue', 'Mason Donohue').
parent('Dirk Donohue', 'Therese Donohue').
parent('Ella Cater', 'Margarite Ussery').
parent('Ella Cater', 'Tyler Ussery').
parent('Gerry Donohue', 'Dirk Donohue').
parent('Gerry Donohue', 'Staci Donohue').
parent('Gustavo Leibowitz', 'Aubrey Leibowitz').
parent('Gustavo Leibowitz', 'Lisha Leibowitz').
parent('Jewel Backus', 'Alton Cater').
parent('Jewel Backus', 'Ella Cater').
parent('Karen Ervin', 'Bruce Cater').
parent('Karen Ervin', 'Vita Cater').
parent('Lisha Leibowitz', 'Boris Ervin').
parent('Lisha Leibowitz', 'Karen Ervin').
parent('Pedro Donohue', 'Mason Donohue').
parent('Pedro Donohue', 'Therese Donohue').
parent('Ty Donohue', 'Mason Donohue').
parent('Ty Donohue', 'Therese Donohue').
parent('Veronica Donohue', 'Mason Donohue').
parent('Veronica Donohue', 'Therese Donohue').
parent('Vita Cater', 'Delpha Donohue').
parent('Vita Cater', 'Pedro Donohue').
parent('Wilfredo Cater', 'Alton Cater').
parent('Wilfredo Cater', 'Ella Cater').

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


aunt(X, Y) :-
    parent(X, A),
    sister(A, Y).

:- dynamic gender/2.

gender('Adele Ervin', female).
gender('Alton Cater', male).
gender('Aubrey Leibowitz', male).
gender('Boris Ervin', male).
gender('Bruce Cater', male).
gender('Delpha Donohue', female).
gender('Derick Backus', male).
gender('Dirk Donohue', male).
gender('Ella Cater', female).
gender('Gerry Donohue', male).
gender('Gustavo Leibowitz', male).
gender('Jewel Backus', female).
gender('Karen Ervin', female).
gender('Lisha Leibowitz', female).
gender('Margarite Ussery', female).
gender('Mason Donohue', male).
gender('Pedro Donohue', male).
gender('Rigoberto Bode', male).
gender('Staci Donohue', female).
gender('Therese Donohue', female).
gender('Tiffany Bode', female).
gender('Ty Donohue', male).
gender('Tyler Ussery', male).
gender('Veronica Donohue', female).
gender('Vita Cater', female).
gender('Wes Backus', male).
gender('Wilfredo Cater', male).

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
