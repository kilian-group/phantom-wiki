"""
Article generation pipeline. We separate the facts into:
1. Prolog-derived facts: these are stored as predicates in the Prolog file.
2. Non-prolog-derived facts: these are not stored as prolog predicates.
For example, they could be implicitly stored in the CFGs.

NOTE: we must ensure that the prolog-derived facts are never contradicted
in the final article. Otherwise, when we generate the questions, the answer
may not be well-defined.
- Is it sufficient to avoid contradictions? Or are there potentially other isssues?
"""

import os
import subprocess
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("--seed", "-s", type=str, help="Global seed for reproducibility")
parser.add_argument("--output_path", "-op", type=str, default="out", help="Output file path")
parser.add_argument("--skip_cfg", "-sc", action="store_true", help="Skip CFG generation")
parser.add_argument(
    "--cfg_dir", "-cd", type=str, default=None, help="Path to the CFG directory if not generating new CFGs"
)
parser.add_argument("--skip_family_tree_gen", "-sc", action="store_true", help="Skip family tree generation")
parser.add_argument(
    "--family_tree_data_gen_path",
    "-ftdgp",
    type=str,
    default="./run-data-gen.sh" "Path to the family tree data generation repo root",
)

args = parser.parse_args()
output_path = args.output_path
ftdgp_path = args.family_tree_data_gen_path

#
# Generate the family tree
#
if not args.skip_family_tree_gen:
    # for now, we use the family-tree-data-gen repo
    ftdgp_executable = os.path.join(ftdgp_path, "run-data-gen.sh")
    ftdgp_output_path = os.path.join(output_path, "ftdgp")
    cmd = [ftdgp_executable, "--output_path", ftdgp_output_path]
    result = subprocess.run(cmd, capture_output=True)
    # save result to output path
    with open(os.path.join(output_path, "ftdgp.log"), "w") as f:
        f.write(result.stdout)
    # since ftdpg uses DLV, we need to convert it to Prolog


# Prolog -> Table


# Table -> family article

# Prolog -> article
pl_to_article_executable = os.path.join("pl_to_article", "pl_to_article.py")


"""
TODO: Question generation pipeline
"""
