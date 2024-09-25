import argparse

import random

import janus_swi as janus

from person import *

parser = argparse.ArgumentParser(description='Generate a family tree')
parser.add_argument('--num_people', type=int, default=10, help='Number of people to generate')
parser.add_argument('--num_generations', type=int, default=3, help='Number of generations to generate')

args = parser.parse_args()

# TODO

if __name__ == "__main__":

    # generate first generation
    # generate first generation names
    # assign gender, single status (everyone single), generation number gen_num (here generation number defines a group of people who can marry each other)
    # find people who can get married;

    gen_num = 0
    plg_syntax = ""

    male = []
    female = []

    for i in range(args.num_people):
        person = generate_person()
        name = person.first_name
        gender = person.gender

        if gender == 'male':
            male.append(name)
        else:
            female.append(name)

        plg_syntax += "single({}).\n".format(name)
        plg_syntax += "generation({}, {}).\n".format(name, gen_num)
        plg_syntax += "{}({}).\n\n".format(gender, name)

    with open ("family.pl", "w") as f:
        f.write(plg_syntax)
    f.close()

    # load the prolog files
    janus.query_once("consult('rules.pl')")
    janus.query_once("consult('family.pl')")
    print('files loaded.')

    # find people who can get married
    import pdb; pdb.set_trace()
    plg_syntax_marriage = ""
    while not (male == [] or female == []):

        single_man = random.choice(male)
        single_woman = random.choice(female)
        plg_syntax = plg_syntax.replace("single({}).".format(single_man), "")
        plg_syntax = plg_syntax.replace("single({}).".format(single_woman), "")

        plg_syntax_marriage += "married({}, {}).\n".format(single_man, single_woman)

        male.remove(single_man)
        female.remove(single_woman)

    with open ("family.pl", "w") as f:
        f.write(plg_syntax)
    f.close()

    with open ("family.pl", "a") as f:
        f.write(plg_syntax_marriage)
    f.close()


#  4.   update database with
# single(X), single(Y) -> married(X,Y)
#  5.   repeat until ~everyone get married
#  6.   gen_num += 1
#  7.  for each new married couple
# generate a list of names of random length
# for name in names:
# person(name)
# gender(name)
# parent(X, name) , parent(Y, name)
# generation (name, gen_num)
# single(name)
#  8.  repeat step 3-7
