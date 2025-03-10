"""Share data to HuggingFace Hub.

TODO: make this a CLI tool in pyproject.toml

Ref:
- https://huggingface.co/docs/datasets/main/en/package_reference/main_classes#datasets.Dataset.push_to_hub
- https://github.com/huggingface/datasets/blob/main/src/datasets/hub.py#L23
"""

import time
from argparse import ArgumentParser

from datasets import load_dataset
from datasets.hub import _delete_files
from huggingface_hub import DatasetCard, DatasetCardData, create_repo, repo_exists

from phantom_eval.utils import load_data

SPLITS = [
    "depth_20_size_50_seed_1",
    "depth_20_size_50_seed_2",
    "depth_20_size_50_seed_3",
    "depth_20_size_500_seed_1",
    "depth_20_size_500_seed_2",
    "depth_20_size_500_seed_3",
    "depth_20_size_5000_seed_1",
    "depth_20_size_5000_seed_2",
    "depth_20_size_5000_seed_3",
]
# TODO: refactor load_data and HF config names to be consistent
# NOTE: for now, I'm using the old config names, which are the values in the dictionary below
CONFIG_ALIASES = {
    "text": "text-corpus",
    "qa_pairs": "question-answer",
    "database": "database",
}


def main(args):
    """Push select data splits to HuggingFace Hub."""
    DATA_DIR = args.data_dir
    REPO_ID = args.repo_id

    # check if repo exists
    if repo_exists(REPO_ID, repo_type="dataset"):
        print(f"Repository {REPO_ID} already exists. Skipping creation.")
        # NOTE: pass in an arbitrary config name to load the dataset
        dataset = load_dataset(REPO_ID, name="question-answer", trust_remote_code=True)
        commit_info = dataset.push_to_hub(
            repo_id=REPO_ID,
            config_name="question-answer",
            commit_message="Update dataset",
            commit_description="Update dataset.",
            create_pr=True,
        )
        # delete files (except README.md and .gitattributes) from the main branch
        # NOTE: for some reason, even after deleting the files, HF still complains
        # about schema mismatches when pushing the new splits.
        print("Deleting files from the main branch...")
        _delete_files(REPO_ID, revision="main")
    else:
        # Create HuggingFace repo
        create_repo(REPO_ID, repo_type="dataset")
        # Push model card to HuggingFace Hub
        card_data = DatasetCardData(
            language="en",
            license="mit",
            annotations_creators="machine-generated",
            language_creators="machine-generated",
            multilinguality="monolingual",
            size_categories="1K-10K",
            source_datasets="original",
            task_categories="question-answering",
            pretty_name="PhantomWiki v1",
            config_names=["question-answer", "corpus", "database"],
        )
        card = DatasetCard.from_template(
            card_data=card_data,
            template_path="data/README.md",
        )
        commit_info = card.push_to_hub(
            repo_id=REPO_ID,
            commit_message="Add dataset card for PhantomWiki v1",
            create_pr=True,
        )

    time.sleep(5)
    pr_revision, pr_url = commit_info.pr_revision, commit_info.pr_url

    # push each split to the PR
    for split in SPLITS:
        print(f"Loading split: {split}")
        data = load_data(DATA_DIR, split=split, from_local=True)
        for config, dataset in data.items():
            print(f"Pushing {config} config of split {split} to HuggingFace Hub...")
            config_name = CONFIG_ALIASES[config]
            dataset.push_to_hub(
                repo_id=REPO_ID,
                config_name=config_name,
                commit_message=f"Add {config_name} config of split {split}",
                revision=pr_revision,
            )
            time.sleep(5)

    print(f"You can find your PR at: {pr_url}")
    print("Done!")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--data_dir",
        type=str,
        default="/Users/ag2435/phantom/data/phantom-wiki-v0.5",
        help="Path to the data directory.",
    )
    parser.add_argument(
        "--repo_id",
        type=str,
        default="kilian-group/phantom-wiki-v1",
        help="ID of the repository on HuggingFace Hub.",
    )
    args = parser.parse_args()
    main(args)
