import os

# Given path to vocabulary file, such as .classes, .individuals, or .relations, return vocabulary dictionary
def read_def_file(file_path):
  defs = open(file_path)
  return {
    i.split()[0]:i.split()[1] for i in defs
  }

# Path to output folder and index of output, return instructions 
def family_gen_to_prolog(pl_path, index=0, obtain_inferred=False):
    output = []
    output_inferred = []

    # Getting names for each individual
    name = f'{index}.individuals'
    individuals = read_def_file(os.path.join(pl_path, name))

    # Getting genders
    name = f'{index}.classes'
    classes = read_def_file(os.path.join(pl_path, name))

    # Getting relations
    name = f'{index}.relations'
    relations = read_def_file(os.path.join(pl_path, name))

    # Complete class information
    name = f'{index}.classes.data'
    with open(os.path.join(pl_path, name)) as classes_data_file:
        content = classes_data_file.readlines()

        for ind, l in enumerate(content): # Iterating through individuals
            ind = individuals[str(ind)]
            l = l.split()

            for cl, member in enumerate(l): # Iterating through each class
                cl = classes[str(cl)]
                if member=='1': # Individual is a member of that class
                    to_string = cl+"(" + ind + ")"
                    output.append(to_string)

                elif member=='-1': # Individual is not a member of that class
                    to_string = "not"+cl.capitalize()+"(" + ind + ")"
                    output.append(to_string)        

    # Basic & complete tree information
    name = f'{index}.relations.data'
    with open(os.path.join(pl_path, name)) as classes_data_file:
        content = classes_data_file.readlines()

        for i, l in enumerate(content):
            l = l.split()
            rel = relations[l[2]][:-2]

            if l[0]=="-": # Negative relation, ie. not ...
                rel = "not"+rel.capitalize()

            to_string = rel +"("+individuals[l[1]]+", "+individuals[l[3]]+")"
            output.append(to_string)

    # Inferred information from the tree
    name = f'{index}.relations.data.inf'
    if obtain_inferred:
        with open(os.path.join(pl_path, name)) as classes_data_file:
          content = classes_data_file.readlines()

          for i, l in enumerate(content):
              l = l.split()
              rel = relations[l[2]][:-2]
              if l[0]=="-":
                  rel = "not"+rel.capitalize()

              to_string = rel +"("+individuals[l[1]]+", "+individuals[l[3]]+")"
              output_inferred.append(to_string)

    # Inferred male/female relations
    name = f'{index}.classes.data.inf'
    if obtain_inferred:
        with open(os.path.join(pl_path, name)) as classes_data_file:
            content = classes_data_file.readlines()

            for ind, l in enumerate(content): # Iterating through individuals
                ind = individuals[str(ind)]
                l = l.split()

                for cl, member in enumerate(l): # Iterating through each class
                    cl = classes[str(cl)]
                    if member=='1': # Individual is a member of that class
                        to_string = cl+"(" + ind + ")"
                        output_inferred.append(to_string)
                        
                    elif member=='-1': # Individual is not a member of that class
                        to_string = "not"+cl.capitalize()+"(" + ind + ")"
                        output_inferred.append(to_string)

    return output, output_inferred

pl, pl_inferred = family_gen_to_prolog("~/dataset-project/family-tree-data-gen/out/")
pl = sorted(pl)

# Between each different relation, include a space
get_predicate = lambda x: x.split("(")[0]
i=0
while i < len(pl)-1:
    if get_predicate(pl[i])!=get_predicate(pl[i+1]):
        pl.insert(i+1, "")
        i+=1
    i+=1

with open("~/dataset-project/phantom-wiki/tests/family_tree.pl", "w") as f_pl:
    f_pl.write("\n".join(pl))