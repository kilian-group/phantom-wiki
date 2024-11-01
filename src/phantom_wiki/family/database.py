import os

# TODO: typing

def read_def_file(file_path):
    """Given a path to a vocabulary file, return vocabulary dictionary.

    Args:
        file_path: Path to the vocabulary file, such as *.classes, *.individuals, or *.relations.
    """
    with open(file_path) as defs:
        return {i.split()[0]: i.split()[1] for i in defs}


# Path to output folder and index of output, return instructions
def family_gen_to_prolog(pl_path, index=0, obtain_inferred=False):
    # TODO: documentation
    # TODO: C901 'family_gen_to_prolog' is too complex (15)
    # TODO: clearer naming

    output = []
    output_inferred = []

    # Getting names for each individual
    name = f"{index}.individuals"
    individuals = read_def_file(os.path.join(pl_path, name))

    # Getting genders
    name = f"{index}.classes"
    classes = read_def_file(os.path.join(pl_path, name))

    # Getting relations
    name = f"{index}.relations"
    relations = read_def_file(os.path.join(pl_path, name))

    # Complete class information
    name = f"{index}.classes.data"
    with open(os.path.join(pl_path, name)) as classes_data_file:
        content = classes_data_file.readlines()

        for ind, line in enumerate(content):  # Iterating through individuals
            ind = individuals[str(ind)]
            line = line.split()

            for cl, member in enumerate(line):  # Iterating through each class
                cl = classes[str(cl)]
                if member == "1":  # Individual is a member of that class
                    to_string = cl + "(" + ind + ")."
                    output.append(to_string)

                elif member == "-1":  # Individual is not a member of that class
                    to_string = "not" + cl.capitalize() + "(" + ind + ")."
                    output.append(to_string)

    # Basic & complete tree information
    name = f"{index}.relations.data"
    with open(os.path.join(pl_path, name)) as classes_data_file:
        content = classes_data_file.readlines()

        for i, line in enumerate(content):
            line = line.split()
            rel = relations[line[2]][:-2]

            if line[0] == "-":  # Negative relation, ie. not ...
                rel = "not" + rel.capitalize()

            to_string = rel + "(" + individuals[line[1]] + ", " + individuals[line[3]] + ")."
            output.append(to_string)

    # Inferred information from the tree
    name = f"{index}.relations.data.inf"
    if obtain_inferred:
        with open(os.path.join(pl_path, name)) as classes_data_file:
            content = classes_data_file.readlines()

            for i, line in enumerate(content):
                line = line.split()
                rel = relations[line[2]][:-2]
                if line[0] == "-":
                    rel = "not" + rel.capitalize()

                to_string = rel + "(" + individuals[line[1]] + ", " + individuals[line[3]] + ")."
                output_inferred.append(to_string)

    # Inferred male/female relations
    name = f"{index}.classes.data.inf"
    if obtain_inferred:
        with open(os.path.join(pl_path, name)) as classes_data_file:
            content = classes_data_file.readlines()

            for ind, line in enumerate(content):  # Iterating through individuals
                ind = individuals[str(ind)]
                line = line.split()

                for cl, member in enumerate(line):  # Iterating through each class
                    cl = classes[str(cl)]
                    if member == "1":  # Individual is a member of that class
                        to_string = cl + "(" + ind + ")."
                        output_inferred.append(to_string)

                    elif member == "-1":  # Individual is not a member of that class
                        to_string = "not" + cl.capitalize() + "(" + ind + ")."
                        output_inferred.append(to_string)

    return output, output_inferred
