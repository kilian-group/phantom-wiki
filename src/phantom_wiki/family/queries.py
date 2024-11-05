import janus_swi as janus

def get_family_relationships(name: str) -> dict:
    """
    Get the following relationships for a given name:
    - mother
    - father
    - siblings
    - children
    - wife/husband 

    Assumes that the prolog files are loaded and the predicates are defined in the prolog files.
    This can be done using the following code:
    ```
    janus.query_once("consult('../../tests/family_tree.pl')")
    janus.query_once("consult('./family/rules.pl')")
    ```

    Ref: https://www.swi-prolog.org/pldoc/man?section=janus-call-prolog
    """
    # name = 'elias'
    relations = {}
    # get mother
    if mother := janus.query_once("mother(X, Y)", {'Y': name})['X']:
        relations['mother'] = mother
    # print(mother)
    # get father
    if father := janus.query_once("father(X, Y)", {'Y': name})['X']:
        relations['father'] = father
    # print(father)
    # get siblings
    if siblings := [sibling['X'] for sibling in janus.query("sibling(X, Y)", {'Y': name})]:
        relations['sibling'] = ', '.join(siblings)
    # print(list(siblings))
    # get children
    if children := [child['X'] for child in list(janus.query("child(X, Y)", {'Y': name}))]:
        relations['child'] = ', '.join(children)
        relations['number of children'] = len(children)
    # print(list(children))
    
    # TODO: get wife and husband
    if spouse := (janus.query_once(f"husband(X, Y)", {'X': name}) or janus.query_once(f"wife(X, Y)", {'X': name}))['Y']:
        relations['spouse'] = spouse

    # facts = []
    # for relation, target in relations.items():
    #     relation_template = ppl_2_ppl[relation]
    #     fact = relation_template.replace("<subject>", name) + " " + str(target) + "."
    #     facts.append(fact)

    # article = "\n".join(facts)
    # return article

    return relations


# get names from the prolog file
def get_names_from_file(fact_file: str):
    person_list = []
    with open(fact_file, "r") as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("female") or line.startswith("male"):
                person = match_name(line)
                person_list.append(person)
            else:   
                print('skip line')
                continue


class FamilyDatabase:
    def __init__(self, facts_file: str, rules_file: str):
        janus.query_once(f"consult('{facts_file}')")
        janus.query_once(f"consult('{rules_file}')")

    def get_family_relationships(self, name: str) -> dict:
        return get_family_relationships(name)
    
    def get_names():
        pass # TODO and replace get_names_from_file
