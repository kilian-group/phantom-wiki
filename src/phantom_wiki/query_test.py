import janus_swi as janus

if __name__ == "__main__":
    # load the prolog files
    janus.query_once("consult('src/phantom_wiki/family/rules.pl')")
    janus.query_once("consult('tests/family_tree.pl')")

    results = janus.query_once("mother(jan, helga)")
    print(results) 

    results = janus.query_once("grandson(jan, elena)")
    print(results)