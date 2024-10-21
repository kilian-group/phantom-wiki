import argparse
import os
import random

import janus_swi as janus

from person import *

parser = argparse.ArgumentParser(description='Generate a family tree')
parser.add_argument('--first_gen_num_people', type=int, default=5, help='Number of people to generate')
parser.add_argument('--num_generations', type=int, default=3, help='Number of generations to generate')
parser.add_argument('--family_folder', type=str, default='family', help='Prolog file to write to')
parser.add_argument('--rules_file', type=str, default='rules.pl', help='Prolog file with rules')

args = parser.parse_args()


if __name__ == "__main__":
    # Step 1 : 
    # generate first generation
    # generate first generation names
    # assign gender, single status (everyone single), generation number gen_num (here generation number defines a group of people who can marry each other)
    # find people who can get married;

    gen_num = 0
    family_file = os.path.join(args.family_folder, f"generation_{gen_num}.pl")
    plg_syntax = ""

    os.makedirs(args.family_folder, exist_ok=True)

    for i in range(args.first_gen_num_people):
        person = generate_person()
        name = person.first_name.lower()
        gender = person.gender

        # parents for the first generation are just place holders
        father_name = f'unknown_{2*i}'
        mother_name = f'unknown_{2*i+1}'

        plg_syntax += "parent({}, {}).\n".format(father_name, name)
        plg_syntax += "parent({}, {}).\n".format(mother_name, name)
        plg_syntax += "single({}).\n".format(name)
        plg_syntax += "generation({}, {}).\n".format(name, gen_num)
        plg_syntax += "{}({}).\n\n".format(gender, name)

    # TODO: should we keep different files for different generations? 
    with open (family_file, "w") as f:
        f.write(plg_syntax)
    f.close()

    # Step 2: assign marriage
    import pdb; pdb.set_trace()
    while gen_num+1 < args.num_generations:

        # load the prolog files
        janus.query_once(f"consult('{args.rules_file}')")
        janus.query_once(f"consult('{family_file}')")
        print('files loaded.')

        # find people who can get married
        plg_syntax_marriage = ""
        # for now make everyone get married
        # TODO: need a ratio for single people
        # This returns an iterator of dict like {'truth': False, 'X': None, 'Y': None} if there are no eligible couples
        # otherwise returns {'truth': True, 'X': 'john', 'Y': 'jane'}
        while True:
            janus.query_once(f"consult('{args.rules_file}')")
            janus.query_once(f"consult('{family_file}')")
            print('files loaded.')

            potential_couple = janus.query_once("can_get_married(X,Y)")
            if potential_couple['truth'] == True:

                groom = potential_couple['X']
                bride = potential_couple['Y']

                plg_syntax = plg_syntax.replace("single({}).".format(groom), "")
                plg_syntax = plg_syntax.replace("single({}).".format(bride), "")

                plg_syntax_marriage += "married({}, {}).\n".format(groom, bride)

                # needs to write to the file after every marriage
                with open (family_file, "w") as f:
                    f.write(plg_syntax)
                f.close()

                with open (family_file, "a") as f:
                    f.write(plg_syntax_marriage)
                f.close()
            
            else:
                break

        janus.query_once(f"consult('{family_file}')")

        # increase the generation number
        gen_num += 1 
        family_file = os.path.join(args.family_folder, f"generation_{gen_num}.pl")

        # give birth to kids 
        married_couples = list(janus.query("married(X,Y)"))

        new_kids_plg_syntax = ""
        for couple in married_couples:
            dad = couple['X']
            mom = couple['Y']
            # num_kids = random.randint(0,5)
            num_kids = 1
            for i in range(num_kids):

                kid = generate_person()
                name = kid.first_name.lower()
                gender = kid.gender
                new_kids_plg_syntax += "{}({}).\n".format(gender, name)
                new_kids_plg_syntax += "generation({}, {}).\n".format(name, gen_num)
                new_kids_plg_syntax += "parent({}, {}).\n".format(dad, name)
                new_kids_plg_syntax += "parent({}, {}).\n".format(mom, name)
                new_kids_plg_syntax += "single({}).\n".format(name)
        
        with open (family_file, "a") as f:
            f.write(new_kids_plg_syntax)
        f.close() 

