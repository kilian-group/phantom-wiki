"""Share data to HuggingFace Hub.

TODO: make this a CLI tool in pyproject.toml

Ref: https://huggingface.co/docs/datasets/main/en/package_reference/main_classes#datasets.Dataset.push_to_hub
"""

import time
from argparse import ArgumentParser

from huggingface_hub import DatasetCard, DatasetCardData

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
    # DATA_DIR = "/Users/ag2435/phantom/data/phantom-wiki-v0.5"
    # REPO_ID = "kilian-group/phantom-wiki-v1"
    DATA_DIR = args.data_dir
    REPO_ID = args.repo_id

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
            )
            time.sleep(5)

    # Push model card to HuggingFace Hub
    card_data = DatasetCardData(
        language="en",
        license="mit",
        annotations_creators="machine-generated",
        language_creators="machine-generated",
        multilinguality="monolingual",
        # size_categories='1K1T',
        source_datasets="original",
        task_categories="question-answering",
        pretty_name="PhantomWiki v1",
        config_names=["question-answer", "corpus", "database"],
    )
    card = DatasetCard.from_template(
        card_data=card_data,
        template_path="data/README.md",
    )
    card.push_to_hub(
        repo_id=REPO_ID,
        commit_message="Add dataset card for PhantomWiki v1",
    )


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
