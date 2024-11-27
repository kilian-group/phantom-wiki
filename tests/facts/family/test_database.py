# from phantom_wiki.facts.database import family_gen_to_prolog


def test_database_generation():
    # TODO: implement as a test
    # TODO: refactor files to be independent on users' personal directory structure

    # pl, pl_inferred = family_gen_to_prolog("~/dataset-project/family-tree-data-gen/out/")
    # pl = sorted(pl)

    # # Between each different relation, include a space
    # get_predicate = lambda x: x.split("(")[0]
    # i = 0
    # while i < len(pl) - 1:
    #     if get_predicate(pl[i]) != get_predicate(pl[i + 1]):
    #         pl.insert(i + 1, "")
    #         i += 1
    #     i += 1

    # with open("~/dataset-project/phantom-wiki/tests/family_tree.pl", "w") as f_pl:
    #     f_pl.write("\n".join(pl))
    pass
