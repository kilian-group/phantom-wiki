import janus_swi as janus

if __name__ == "__main__":
    # load the prolog files
    janus.query_once("consult('src/phantom_wiki/family/rules.pl')")
    janus.query_once("consult('tests/family_example.pl')")

    results = janus.query_once("can_get_married(bob, alice)")
    print(results)

    results = janus.query_once("mother(jane, alice)")
    print(results) 

    results = janus.query_once("father(bob, alice)")
    print(results)