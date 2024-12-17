
:- dynamic term_expansion/2.
:- multifile term_expansion/2.


step_daughter(X, Y) :-
    step_child(X, Y),
    female(Y).

second_aunt(X, Y) :-
    great_grandparent(X, A),
    sister(A, Y).

second_uncle(X, Y) :-
    great_grandparent(X, A),
    brother(A, Y).

step_son(X, Y) :-
    step_child(X, Y),
    male(Y).

step_child(X, Y) :-
    step_parent(Y, X).

great_granddaughter(X, Y) :-
    great_grandchild(X, Y),
    female(Y).

:- multifile prolog_clause_name/2.


great_grandson(X, Y) :-
    great_grandchild(X, Y),
    male(Y).

step_father(X, Y) :-
    step_parent(X, Y),
    male(Y).

is_divorced(X) :-
    once_married(X, _Y).

:- dynamic library_directory/1.
:- multifile library_directory/1.


step_mother(X, Y) :-
    step_parent(X, Y),
    female(Y).

great_grandfather(X, Y) :-
    great_grandparent(X, Y),
    male(Y).

great_grandchild(X, Y) :-
    great_grandparent(Y, X).

step_parent(X, Y) :-
    parent(X, A),
    are_married(A, Y),
    \+ parent(X, Y).

:- dynamic term_expansion/4.
:- multifile term_expansion/4.


brother_in_law(X, Y) :-
    are_married(X, A),
    brother(A, Y).

great_grandparent(X, Y) :-
    grandparent(X, Z),
    parent(Z, Y).

:- dynamic goal_expansion/4.
:- multifile goal_expansion/4.


great_grandmother(X, Y) :-
    great_grandparent(X, Y),
    female(Y).

sister_in_law(X, Y) :-
    are_married(X, A),
    sister(A, Y).

daughter_in_law(X, Y) :-
    child(X, A),
    wife(A, Y).

granddaughter(X, Y) :-
    grandchild(X, Y),
    female(Y).

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

grandson(X, Y) :-
    grandchild(X, Y),
    male(Y).

son_in_law(X, Y) :-
    child(X, A),
    husband(A, Y).

father_in_law(X, Y) :-
    parent_in_law(X, Y),
    male(Y).

great_uncle(X, Y) :-
    grandparent(X, A),
    brother(A, Y).

:- multifile prolog_list_goal/1.


grandchild(X, Y) :-
    grandparent(Y, X).

mother_in_law(X, Y) :-
    parent_in_law(X, Y),
    female(Y).

parent_in_law(X, Y) :-
    are_married(X, A),
    parent(A, Y).

grandfather(X, Y) :-
    grandparent(X, Y),
    male(Y).

great_aunt(X, Y) :-
    grandparent(X, A),
    sister(A, Y).

husband(X, Y) :-
    are_married(X, Y),
    male(Y).

:- dynamic expand_query/4.
:- multifile expand_query/4.


wife(X, Y) :-
    are_married(X, Y),
    female(Y).

grandparent(X, Y) :-
    parent(X, Z),
    parent(Z, Y).

:- multifile message_property/2.


grandmother(X, Y) :-
    grandparent(X, Y),
    female(Y).

niece(X, Y) :-
    sibling(X, A),
    daughter(A, Y).

:- dynamic divorce/3.

divorce(alfonso, ila, '0273-07-17').
divorce(antionette, deangelo, '0271-10-28').
divorce(daisy, dominick, '0269-11-04').
divorce(deangelo, antionette, '0271-10-28').
divorce(derick, kanesha, '0244-09-01').
divorce(dominick, daisy, '0269-11-04').
divorce(ila, alfonso, '0273-07-17').
divorce(kanesha, derick, '0244-09-01').
divorce(lyndia, vicente, '0210-04-18').
divorce(maggie, scotty, '0181-12-17').
divorce(matt, thomasine, '0237-10-16').
divorce(meghann, tanner, '0263-07-16').
divorce(scotty, maggie, '0181-12-17').
divorce(tanner, meghann, '0263-07-16').
divorce(thomasine, matt, '0237-10-16').
divorce(vicente, lyndia, '0210-04-18').
divorce(alberto, ollie, '0299-01-15').
divorce(carmelita, edmond, '0273-07-19').
divorce(clifford, hannah, '0346-05-01').
divorce(clyde, paige, '0317-11-18').
divorce(coleen, devin, '0355-06-14').
divorce(derrick, monserrate, '0347-09-06').
divorce(devin, coleen, '0355-06-14').
divorce(dick, kayla, '0325-01-06').
divorce(edmond, carmelita, '0273-07-19').
divorce(gabriele, stan, '0326-02-07').
divorce(hannah, clifford, '0346-05-01').
divorce(kayla, dick, '0325-01-06').
divorce(monserrate, derrick, '0347-09-06').
divorce(ollie, alberto, '0299-01-15').
divorce(oma, stanford, '0355-08-04').
divorce(paige, clyde, '0317-11-18').
divorce(stan, gabriele, '0326-02-07').
divorce(stanford, oma, '0355-08-04').
divorce(tommy, vernell, '0273-04-19').
divorce(vernell, tommy, '0273-04-19').

step_sister(X, Y) :-
    step_parent(X, A),
    daughter(A, Y).

:- dynamic expand_answer/2.
:- multifile expand_answer/2.


nephew(X, Y) :-
    sibling(X, A),
    son(A, Y).

:- dynamic marriage/3.

marriage(alfonso, ila, '0257-07-17').
marriage(alfonso, paige, '0318-11-18').
marriage(antionette, clyde, '0318-11-18').
marriage(antionette, deangelo, '0255-10-28').
marriage(daisy, devin, '0356-06-14').
marriage(daisy, dominick, '0253-11-04').
marriage(deangelo, antionette, '0255-10-28').
marriage(deangelo, kayla, '0326-01-06').
marriage(derick, kanesha, '0228-09-01').
marriage(derick, oma, '0356-08-04').
marriage(dominick, daisy, '0253-11-04').
marriage(dominick, tommy, '0274-04-19').
marriage(ila, alfonso, '0257-07-17').
marriage(ila, stanford, '0356-08-04').
marriage(kanesha, derick, '0228-09-01').
marriage(kanesha, monserrate, '0348-09-06').
marriage(lyndia, vernell, '0274-04-19').
marriage(lyndia, vicente, '0194-04-18').
marriage(maggie, coleen, '0356-06-14').
marriage(maggie, scotty, '0165-12-17').
marriage(matt, gabriele, '0327-02-07').
marriage(matt, thomasine, '0221-10-16').
marriage(meghann, derrick, '0348-09-06').
marriage(meghann, tanner, '0247-07-16').
marriage(scotty, dick, '0326-01-06').
marriage(scotty, maggie, '0165-12-17').
marriage(tanner, meghann, '0247-07-16').
marriage(tanner, ollie, '0300-01-15').
marriage(thomasine, alberto, '0300-01-15').
marriage(thomasine, matt, '0221-10-16').
marriage(vicente, clifford, '0347-05-01').
marriage(vicente, lyndia, '0194-04-18').
marriage(alberto, ollie, '0283-01-15').
marriage(alberto, thomasine, '0300-01-15').
marriage(carmelita, edmond, '0257-07-19').
marriage(clifford, hannah, '0330-05-01').
marriage(clifford, vicente, '0347-05-01').
marriage(clyde, antionette, '0318-11-18').
marriage(clyde, paige, '0301-11-18').
marriage(coleen, devin, '0339-06-14').
marriage(coleen, maggie, '0356-06-14').
marriage(derrick, meghann, '0348-09-06').
marriage(derrick, monserrate, '0331-09-06').
marriage(devin, coleen, '0339-06-14').
marriage(devin, daisy, '0356-06-14').
marriage(dick, kayla, '0309-01-06').
marriage(dick, scotty, '0326-01-06').
marriage(edmond, carmelita, '0257-07-19').
marriage(gabriele, matt, '0327-02-07').
marriage(gabriele, stan, '0310-02-07').
marriage(hannah, clifford, '0330-05-01').
marriage(kayla, deangelo, '0326-01-06').
marriage(kayla, dick, '0309-01-06').
marriage(monserrate, derrick, '0331-09-06').
marriage(monserrate, kanesha, '0348-09-06').
marriage(ollie, alberto, '0283-01-15').
marriage(ollie, tanner, '0300-01-15').
marriage(oma, derick, '0356-08-04').
marriage(oma, stanford, '0339-08-04').
marriage(paige, alfonso, '0318-11-18').
marriage(paige, clyde, '0301-11-18').
marriage(stan, gabriele, '0310-02-07').
marriage(stanford, ila, '0356-08-04').
marriage(stanford, oma, '0339-08-04').
marriage(tommy, dominick, '0274-04-19').
marriage(tommy, vernell, '0257-04-19').
marriage(vernell, lyndia, '0274-04-19').
marriage(vernell, tommy, '0257-04-19').

step_brother(X, Y) :-
    step_parent(X, A),
    son(A, Y).

male(X) :-
    gender(X, male).

never_married(X, Y) :-
    \+ marriage(X, Y, _D1).

son(X, Y) :-
    child(X, Y),
    male(Y).

friend(X, Y) :-
    friend_(X, Y).
friend(X, Y) :-
    friend_(Y, X).

daughter(X, Y) :-
    child(X, Y),
    female(Y).

once_married(X, Y) :-
    marriage(X, Y, _D1),
    divorce(X, Y, _D2).

:- dynamic friend_/2.

friend_(alfonso, alton).
friend_(alfonso, colby).
friend_(alfonso, derick).
friend_(alfonso, miki).
friend_(alfonso, alberto).
friend_(alfonso, clyde).
friend_(alfonso, mohammed).
friend_(alton, colby).
friend_(alton, derick).
friend_(alton, kari).
friend_(alton, miki).
friend_(alton, alberto).
friend_(alton, clyde).
friend_(alton, coleen).
friend_(alton, mohammed).
friend_(alton, ollie).
friend_(alton, stan).
friend_(antionette, daisy).
friend_(antionette, dominick).
friend_(antionette, matt).
friend_(antionette, tanner).
friend_(antionette, thomasine).
friend_(antionette, monserrate).
friend_(colby, derick).
friend_(colby, kari).
friend_(colby, miki).
friend_(colby, alberto).
friend_(colby, clyde).
friend_(colby, coleen).
friend_(colby, mohammed).
friend_(colby, stan).
friend_(daisy, dominick).
friend_(daisy, matt).
friend_(daisy, tanner).
friend_(daisy, thomasine).
friend_(daisy, gabriele).
friend_(daisy, monserrate).
friend_(deangelo, dominick).
friend_(deangelo, ila).
friend_(deangelo, maggie).
friend_(deangelo, meghann).
friend_(deangelo, reyna).
friend_(deangelo, rosalee).
friend_(deangelo, derrick).
friend_(deangelo, edmond).
friend_(deangelo, gertrude).
friend_(deangelo, kayla).
friend_(deangelo, stan).
friend_(deanna, dixie).
friend_(deanna, ellis).
friend_(deanna, kanesha).
friend_(deanna, lyndia).
friend_(deanna, clifford).
friend_(deanna, hannah).
friend_(deanna, marybeth).
friend_(deanna, paige).
friend_(deanna, reggie).
friend_(deanna, vernell).
friend_(derick, kari).
friend_(derick, miki).
friend_(derick, alberto).
friend_(derick, clyde).
friend_(derick, coleen).
friend_(derick, mohammed).
friend_(derick, stan).
friend_(dixie, ellis).
friend_(dixie, kanesha).
friend_(dixie, lyndia).
friend_(dixie, clifford).
friend_(dixie, hannah).
friend_(dixie, marybeth).
friend_(dixie, paige).
friend_(dixie, reggie).
friend_(dominick, ila).
friend_(dominick, maggie).
friend_(dominick, matt).
friend_(dominick, meghann).
friend_(dominick, reyna).
friend_(dominick, rosalee).
friend_(dominick, tanner).
friend_(dominick, thomasine).
friend_(dominick, derrick).
friend_(dominick, edmond).
friend_(dominick, gertrude).
friend_(dominick, kayla).
friend_(dominick, monserrate).
friend_(ellis, kanesha).
friend_(ellis, lyndia).
friend_(ellis, clifford).
friend_(ellis, hannah).
friend_(ellis, marybeth).
friend_(ellis, paige).
friend_(ellis, reggie).
friend_(ellis, vernell).
friend_(ila, maggie).
friend_(ila, meghann).
friend_(ila, reyna).
friend_(ila, rosalee).
friend_(ila, derrick).
friend_(ila, edmond).
friend_(ila, gertrude).
friend_(ila, kayla).
friend_(ila, stan).
friend_(johnna, scotty).
friend_(johnna, carmelita).
friend_(johnna, dick).
friend_(johnna, oma).
friend_(johnna, sherrie).
friend_(kanesha, lyndia).
friend_(kanesha, scotty).
friend_(kanesha, vicente).
friend_(kanesha, clifford).
friend_(kanesha, hannah).
friend_(kanesha, luciano).
friend_(kanesha, marybeth).
friend_(kanesha, paige).
friend_(kanesha, reggie).
friend_(kanesha, tommy).
friend_(kanesha, vernell).
friend_(kari, miki).
friend_(kari, alberto).
friend_(kari, coleen).
friend_(kari, mohammed).
friend_(kari, stan).
friend_(lyndia, vicente).
friend_(lyndia, clifford).
friend_(lyndia, hannah).
friend_(lyndia, marybeth).
friend_(lyndia, paige).
friend_(lyndia, reggie).
friend_(lyndia, vernell).
friend_(maggie, meghann).
friend_(maggie, reyna).
friend_(maggie, rosalee).
friend_(maggie, derrick).
friend_(maggie, edmond).
friend_(maggie, gertrude).
friend_(maggie, kayla).
friend_(maggie, stan).
friend_(matt, tanner).
friend_(matt, thomasine).
friend_(matt, gabriele).
friend_(matt, monserrate).
friend_(meghann, reyna).
friend_(meghann, rosalee).
friend_(meghann, derrick).
friend_(meghann, edmond).
friend_(meghann, gertrude).
friend_(meghann, kayla).
friend_(meghann, stan).
friend_(miki, alberto).
friend_(miki, clyde).
friend_(miki, coleen).
friend_(miki, dick).
friend_(miki, mohammed).
friend_(miki, stan).
friend_(reyna, rosalee).
friend_(reyna, derrick).
friend_(reyna, edmond).
friend_(reyna, gertrude).
friend_(reyna, kayla).
friend_(reyna, stan).
friend_(rosalee, derrick).
friend_(rosalee, edmond).
friend_(rosalee, gertrude).
friend_(rosalee, kayla).
friend_(rosalee, stan).
friend_(scotty, carmelita).
friend_(scotty, dick).
friend_(scotty, oma).
friend_(scotty, sherrie).
friend_(tanner, thomasine).
friend_(tanner, gabriele).
friend_(tanner, monserrate).
friend_(thomasine, gabriele).
friend_(thomasine, monserrate).
friend_(vicente, marybeth).
friend_(vicente, paige).
friend_(alberto, clyde).
friend_(alberto, coleen).
friend_(alberto, mohammed).
friend_(alberto, stan).
friend_(carmelita, dick).
friend_(carmelita, mohammed).
friend_(carmelita, oma).
friend_(carmelita, sherrie).
friend_(clifford, hannah).
friend_(clifford, marybeth).
friend_(clifford, paige).
friend_(clyde, mohammed).
friend_(coleen, mohammed).
friend_(coleen, stan).
friend_(derrick, edmond).
friend_(derrick, gertrude).
friend_(derrick, kayla).
friend_(derrick, stan).
friend_(dick, mohammed).
friend_(dick, oma).
friend_(dick, sherrie).
friend_(edmond, gertrude).
friend_(edmond, kayla).
friend_(edmond, stan).
friend_(gabriele, monserrate).
friend_(gertrude, kayla).
friend_(hannah, marybeth).
friend_(hannah, paige).
friend_(hannah, reggie).
friend_(kayla, stan).
friend_(luciano, marybeth).
friend_(luciano, paige).
friend_(marybeth, paige).
friend_(marybeth, reggie).
friend_(marybeth, tommy).
friend_(marybeth, vernell).
friend_(mohammed, sherrie).
friend_(mohammed, stan).
friend_(oma, sherrie).
friend_(paige, reggie).
friend_(paige, tommy).
friend_(paige, vernell).

female(X) :-
    gender(X, female).

:- dynamic exception/3.
:- multifile exception/3.


father(X, Y) :-
    parent(X, Y),
    male(Y).

:- thread_local thread_message_hook/3.
:- dynamic thread_message_hook/3.
:- volatile thread_message_hook/3.


child(X, Y) :-
    parent(Y, X).

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
attribute(acupuncturist).
attribute('flying disc').
attribute('museum/gallery curator').
attribute(cricket).
attribute('engineer, technical sales').
attribute(weightlifting).
attribute('pharmacist, hospital').
attribute(meditation).
attribute('air cabin crew').
attribute('ballroom dancing').
attribute('secretary, company').
attribute(microscopy).
attribute('environmental education officer').
attribute(reading).
attribute('primary school teacher').
attribute('laser tag').
attribute('research scientist (life sciences)').
attribute('hiking/backpacking').
attribute(surgeon).
attribute(audiophile).
attribute('exhibitions officer, museum/gallery').
attribute('tennis polo').
attribute('location manager').
attribute(photography).
attribute('exercise physiologist').
attribute(backgammon).
attribute('english as a foreign language teacher').
attribute(microscopy).
attribute('psychiatric nurse').
attribute(herping).
attribute('horticultural consultant').
attribute(philately).
attribute('advertising copywriter').
attribute(birdwatching).
attribute('pension scheme manager').
attribute(shogi).
attribute('surveyor, commercial/residential').
attribute('magnet fishing').
attribute(chiropodist).
attribute('table tennis').
attribute('electronics engineer').
attribute('scuba diving').
attribute('housing manager/officer').
attribute(biology).
attribute('community arts worker').
attribute('sea glass collecting').
attribute('learning mentor').
attribute(research).
attribute('restaurant manager, fast food').
attribute(gongoozling).

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

are_married(X, Y) :-
    marriage(X, Y, _D1),
    \+ divorce(X, Y, _D2).

brother(X, Y) :-
    sibling(X, Y),
    male(Y).

:- dynamic nonbinary/1.

nonbinary(X) :-
    gender(X, nonbinary).

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
type(alberto, person).
type(carmelita, person).
type(clifford, person).
type(clyde, person).
type(coleen, person).
type(derrick, person).
type(devin, person).
type(dick, person).
type(edmond, person).
type(gabriele, person).
type(gertrude, person).
type(hannah, person).
type(kayla, person).
type(luciano, person).
type(marybeth, person).
type(mohammed, person).
type(monserrate, person).
type(ollie, person).
type(oma, person).
type(paige, person).
type(reggie, person).
type(sherrie, person).
type(stan, person).
type(stanford, person).
type(tommy, person).
type(vernell, person).

:- dynamic message_hook/3.
:- multifile message_hook/3.


mother(X, Y) :-
    parent(X, Y),
    female(Y).

male_first_cousin_once_removed(X, Y) :-
    cousin(X, A),
    son(A, Y),
    X\=Y.

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
dob(alberto, '0267-01-15').
dob(carmelita, '0241-07-19').
dob(clifford, '0314-05-01').
dob(clyde, '0285-11-18').
dob(coleen, '0322-09-15').
dob(derrick, '0314-05-05').
dob(devin, '0323-06-14').
dob(dick, '0292-09-27').
dob(edmond, '0237-12-06').
dob(gabriele, '0292-03-12').
dob(gertrude, '0341-11-30').
dob(hannah, '0313-12-28').
dob(kayla, '0293-01-06').
dob(luciano, '0350-04-23').
dob(marybeth, '0271-09-23').
dob(mohammed, '0347-11-08').
dob(monserrate, '0315-09-06').
dob(ollie, '0266-05-02').
dob(oma, '0323-08-04').
dob(paige, '0282-01-13').
dob(reggie, '0321-11-07').
dob(sherrie, '0342-02-21').
dob(stan, '0294-02-07').
dob(stanford, '0322-10-22').
dob(tommy, '0241-04-19').
dob(vernell, '0238-08-06').

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
job(alberto, 'special educational needs teacher').
job(carmelita, acupuncturist).
job(clifford, 'museum/gallery curator').
job(clyde, 'engineer, technical sales').
job(coleen, 'pharmacist, hospital').
job(derrick, 'air cabin crew').
job(devin, 'secretary, company').
job(dick, 'environmental education officer').
job(edmond, 'primary school teacher').
job(gabriele, 'research scientist (life sciences)').
job(gertrude, surgeon).
job(hannah, 'exhibitions officer, museum/gallery').
job(kayla, 'location manager').
job(luciano, 'exercise physiologist').
job(marybeth, 'english as a foreign language teacher').
job(mohammed, 'psychiatric nurse').
job(monserrate, 'horticultural consultant').
job(ollie, 'advertising copywriter').
job(oma, 'pension scheme manager').
job(paige, 'surveyor, commercial/residential').
job(reggie, chiropodist).
job(sherrie, 'electronics engineer').
job(stan, 'housing manager/officer').
job(stanford, 'community arts worker').
job(tommy, 'learning mentor').
job(vernell, 'restaurant manager, fast food').

female_first_cousin_once_removed(X, Y) :-
    cousin(X, A),
    daughter(A, Y),
    X\=Y.

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
parent(alberto, carmelita).
parent(alberto, edmond).
parent(clyde, alberto).
parent(clyde, ollie).
parent(coleen, gabriele).
parent(coleen, stan).
parent(gertrude, derrick).
parent(gertrude, monserrate).
parent(hannah, clyde).
parent(hannah, paige).
parent(kayla, alberto).
parent(kayla, ollie).
parent(luciano, coleen).
parent(luciano, devin).
parent(marybeth, carmelita).
parent(marybeth, edmond).
parent(mohammed, oma).
parent(mohammed, stanford).
parent(monserrate, dick).
parent(monserrate, kayla).
parent(ollie, tommy).
parent(ollie, vernell).
parent(reggie, gabriele).
parent(reggie, stan).
parent(sherrie, clifford).
parent(sherrie, hannah).
parent(stan, alberto).
parent(stan, ollie).
parent(stanford, gabriele).
parent(stanford, stan).

:- dynamic save_all_clauses_to_file/1.

save_all_clauses_to_file(A) :-
    open(A, write, B),
    set_output(B),
    listing,
    close(B).

:- dynamic resource/2.
:- multifile resource/2.


:- dynamic portray/1.
:- multifile portray/1.


:- dynamic goal_expansion/2.
:- multifile goal_expansion/2.


sister(Y, X) :-
    sibling(X, Y),
    female(X).

male_second_cousin(X, Y) :-
    parent(X, A),
    parent(Y, B),
    cousin(A, B),
    male(Y),
    X\=Y.

:- dynamic prolog_load_file/2.
:- multifile prolog_load_file/2.


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
hobby(alberto, judo).
hobby(carmelita, 'flying disc').
hobby(clifford, cricket).
hobby(clyde, weightlifting).
hobby(coleen, meditation).
hobby(derrick, 'ballroom dancing').
hobby(devin, microscopy).
hobby(dick, reading).
hobby(edmond, 'laser tag').
hobby(gabriele, 'hiking/backpacking').
hobby(gertrude, audiophile).
hobby(hannah, 'tennis polo').
hobby(kayla, photography).
hobby(luciano, backgammon).
hobby(marybeth, microscopy).
hobby(mohammed, herping).
hobby(monserrate, philately).
hobby(ollie, birdwatching).
hobby(oma, shogi).
hobby(paige, 'magnet fishing').
hobby(reggie, 'table tennis').
hobby(sherrie, 'scuba diving').
hobby(stan, biology).
hobby(stanford, 'sea glass collecting').
hobby(tommy, research).
hobby(vernell, gongoozling).

female_second_cousin(X, Y) :-
    parent(X, A),
    parent(Y, B),
    cousin(A, B),
    female(Y),
    X\=Y.

sibling(X, Y) :-
    parent(X, A),
    parent(Y, A),
    X\=Y.

male_cousin(X, Y) :-
    cousin(X, Y),
    male(Y).

:- dynamic resource/3.
:- multifile resource/3.


is_single(X) :-
    never_married(X, _Y).

female_cousin(X, Y) :-
    cousin(X, Y),
    female(Y).

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
gender(alberto, male).
gender(carmelita, female).
gender(clifford, male).
gender(clyde, male).
gender(coleen, female).
gender(derrick, male).
gender(devin, male).
gender(dick, male).
gender(edmond, male).
gender(gabriele, female).
gender(gertrude, female).
gender(hannah, female).
gender(kayla, female).
gender(luciano, male).
gender(marybeth, female).
gender(mohammed, male).
gender(monserrate, female).
gender(ollie, female).
gender(oma, female).
gender(paige, female).
gender(reggie, male).
gender(sherrie, female).
gender(stan, male).
gender(stanford, male).
gender(tommy, male).
gender(vernell, female).

is_married(X) :-
    are_married(X, _Y).

cousin(X, Y) :-
    parent(X, A),
    parent(Y, B),
    sibling(A, B),
    X\=Y.

uncle(X, Y) :-
    parent(X, A),
    brother(A, Y).

:- dynamic pyrun/2.

pyrun(A, B) :-
    read_term_from_atom(A, C, [variable_names(B)]),
    call(C).

aunt(X, Y) :-
    parent(X, A),
    sister(A, Y).
