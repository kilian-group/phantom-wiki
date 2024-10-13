import janus_swi as janus

if __name__ == "__main__":
    # load the prolog files
    janus.query_once("consult('tests/family_tree.pl')")
    janus.query_once("consult('src/phantom_wiki/family/rules.pl')")

    results = janus.query_once("mother(elias, helga)")
    print(results) 

    results = janus.query_once("greatGranddaughter(natalie, anastasia)")
    print(results)

    results = janus.query_once("greatGrandson(natalie, anastasia)")
    print(results)