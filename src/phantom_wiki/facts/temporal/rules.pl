%% Temporal event rules for PhantomWiki
%%
%% These rules support temporal queries over life events.

%% lived_in_at(Name, City, Year) - true if Name lived in City during Year
:- dynamic lived_in/4.
lived_in_at(Name, City, Year) :-
    lived_in(Name, City, Start, End),
    Year >= Start,
    Year =< End.

%% career_at(Name, JobTitle, Company, Year) - true if Name worked at Company as JobTitle during Year
:- dynamic career/5.
career_at(Name, JobTitle, Company, Year) :-
    career(Name, JobTitle, Company, Start, End),
    Year >= Start,
    Year =< End.

%% career_before(Name, JobBefore, JobAfter) - true if Name held JobBefore before JobAfter
career_before(Name, JobBefore, JobAfter) :-
    career(Name, JobBefore, _, _, EndBefore),
    career(Name, JobAfter, _, StartAfter, _),
    EndBefore =< StartAfter,
    JobBefore \= JobAfter.

%% married_first(Name1, Name2) - true if Name1 married before Name2
:- dynamic marriage_year/3.
married_first(Name1, Name2) :-
    marriage_year(Name1, _, Year1),
    marriage_year(Name2, _, Year2),
    Name1 \= Name2,
    Year1 < Year2.

%% education facts
:- dynamic education/3.
