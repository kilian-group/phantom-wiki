"""Script to convert a script-based dataset to Parquet data-only dataset, so that the dataset viewer will be supported.

NOTE: the dataset-cli convert_to_parquet command has a fixed wait time of 5 seconds between configs,
which leads to rate limits on the huggingface.co side. This script includes an adjustable wait time to respect rate limits.

Ref:
https://github.com/huggingface/datasets/blob/main/src/datasets/commands/convert_to_parquet.py
https://github.com/huggingface/datasets/blob/main/src/datasets/hub.py
"""

import time
from argparse import ArgumentParser

import datasets.config
from datasets.inspect import get_dataset_config_names, get_dataset_default_config_name
from datasets.load import load_dataset
from huggingface_hub import CommitInfo, HfApi
from huggingface_hub.utils import HfHubHTTPError


def convert_to_parquet(
    repo_id: str,
    revision: str | None = None,
    token: bool | str | None = None,
    trust_remote_code: bool | None = None,
) -> CommitInfo:
    """Convert Hub [script-based dataset](dataset_script) to Parquet [data-only dataset](repository_structure), so that
    the dataset viewer will be supported.

    This function:
    - makes a copy of the script on the "main" branch into a dedicated branch called "script" (if it does not already exist)
    - creates a pull request to the Hub dataset to convert it to Parquet files (and deletes the script from the main branch)

    If in the future you need to recreate the Parquet files from the "script" branch, pass the `revision="script"` argument.

    Note that you should pass the `trust_remote_code=True` argument only if you trust the remote code to be executed locally on your machine.

    Args:
        repo_id (`str`): ID of the source Hub dataset repository, in the following format: `<user>/<dataset_name>` or
            `<org>/<dataset_name>`.
        revision (`str`, *optional*): Branch of the source Hub dataset repository. Defaults to the `"main"` branch.
        token (`bool` or `str`, *optional*): Authentication token for the Hugging Face Hub.
        trust_remote_code (`bool`, defaults to `False`): Whether you trust the remote code of the Hub script-based
            dataset to be executed locally on your machine. This option should only be set to `True` for repositories
            where you have read the code and which you trust.

            <Changed version="2.20.0">

            `trust_remote_code` defaults to `False` if not specified.

            </Changed>

    Returns:
        `huggingface_hub.CommitInfo`
    """
    print(f"{repo_id}")
    configs = get_dataset_config_names(
        repo_id, token=token, revision=revision, trust_remote_code=trust_remote_code
    )
    print(f"{configs = }")
    default_config = get_dataset_default_config_name(
        repo_id, token=token, revision=revision, trust_remote_code=trust_remote_code
    )
    print(f"{default_config = }")
    if default_config:
        config = default_config
        configs.remove(default_config)
    else:
        config = configs.pop(0)
    print(f"{config = }")
    dataset = load_dataset(repo_id, config, revision=revision, trust_remote_code=trust_remote_code)
    commit_info = dataset.push_to_hub(
        repo_id,
        config_name=config,
        commit_message="Convert dataset to Parquet",
        commit_description="Convert dataset to Parquet.",
        create_pr=True,
        token=token,
        set_default=default_config is not None,
    )
    time.sleep(5)
    pr_revision, pr_url = commit_info.pr_revision, commit_info.pr_url
    for config in configs:
        print(f"{config = }")
        dataset = load_dataset(repo_id, config, revision=revision, trust_remote_code=trust_remote_code)
        dataset.push_to_hub(
            repo_id,
            config_name=config,
            commit_message=f"Add '{config}' config data files",
            revision=pr_revision,
            token=token,
        )
        time.sleep(5)
    _delete_files(repo_id, revision=pr_revision, token=token)
    if not revision:
        api = HfApi(endpoint=datasets.config.HF_ENDPOINT, token=token)
        try:
            api.create_branch(repo_id, branch="script", repo_type="dataset", token=token, exist_ok=True)
        except HfHubHTTPError:
            pass
    print(f"You can find your PR to convert the dataset to Parquet at: {pr_url}")
    return commit_info


def _delete_files(dataset_id, revision=None, token=None):
    """Delete all files in a dataset repository except the README.md and .gitattributes files.

    NOTE: this implementation uses delete_files instead of delete_file to avoid rate limits.
    https://huggingface.co/docs/huggingface_hub/v0.28.1/en/package_reference/hf_api#huggingface_hub.HfApi.delete_files
    """
    dataset_name = dataset_id.split("/")[-1]
    hf_api = HfApi(endpoint=datasets.config.HF_ENDPOINT, token=token)
    repo_files = hf_api.list_repo_files(
        dataset_id,
        repo_type="dataset",
    )
    if repo_files:
        legacy_json_file = []
        python_files = []
        data_files = []
        for filename in repo_files:
            if filename in {".gitattributes", "README.md"}:
                continue
            elif filename == f"{dataset_name}.py":
                hf_api.delete_file(
                    filename,
                    dataset_id,
                    repo_type="dataset",
                    revision=revision,
                    commit_message="Delete loading script",
                )
            elif filename == "dataset_infos.json":
                legacy_json_file.append(filename)
            elif filename.endswith(".py"):
                python_files.append(filename)
            else:
                data_files.append(filename)
        if legacy_json_file:
            hf_api.delete_file(
                "dataset_infos.json",
                dataset_id,
                repo_type="dataset",
                revision=revision,
                commit_message="Delete legacy dataset_infos.json",
            )
        if python_files:
            # for filename in python_files:
            #     hf_api.delete_file(
            #         filename,
            #         dataset_id,
            #         repo_type="dataset",
            #         revision=revision,
            #         commit_message="Delete loading script auxiliary file",
            #     )
            hf_api.delete_files(
                dataset_id,
                python_files,
                repo_type="dataset",
                revision=revision,
                commit_message="Delete loading script auxiliary files",
            )
        if data_files:
            # for filename in data_files:
            #     hf_api.delete_file(
            #         filename,
            #         dataset_id,
            #         repo_type="dataset",
            #         revision=revision,
            #         commit_message="Delete data file",
            #     )
            hf_api.delete_files(
                dataset_id,
                data_files,
                repo_type="dataset",
                revision=revision,
                commit_message="Delete data files",
            )


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "dataset_id", help="source dataset ID, e.g. USERNAME/DATASET_NAME or ORGANIZATION/DATASET_NAME"
    )
    parser.add_argument(
        "--token", help="access token to the Hugging Face Hub (defaults to logged-in user's one)"
    )
    parser.add_argument("--revision", help="source revision")
    parser.add_argument(
        "--trust_remote_code",
        action="store_true",
        help="whether to trust the code execution of the load script",
    )
    args = parser.parse_args()
    convert_to_parquet(
        repo_id=args.dataset_id,
        revision=args.revision,
        token=args.token,
        trust_remote_code=args.trust_remote_code,
    )
