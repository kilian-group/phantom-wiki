import argparse


def get_arguments():
    parser = argparse.ArgumentParser(description="Generate articles from Prolog files")
    parser.add_argument(
        "--pl_file", type=str, default="../../tests/family_tree.pl", help="Path to the Prolog file"
    )
    parser.add_argument("--skip_cfg", "-sc", action="store_true", help="Skip CFG generation")
    parser.add_argument(
        "--cfg_dir",
        "-cd",
        type=str,
        default=None,
        help="Path to the CFG directory if not generating new CFGs",
    )
    parser.add_argument("--output_folder", type=str, default="output", help="Path to the output folder")
    # TODO this should not depend on the testing directory
    parser.add_argument("--rules", type=list, default=['../../tests/base_rules.pl', '../../tests/derived_rules.pl'], help="list of Path to the rules file")
    (
        args,
        _,
    ) = (
        parser.parse_known_args()
    )  # this is useful when running the script from a notebook so that we use the default values
    return args
