"""Utilities for computing evaluation metrics given prediction files
"""
import logging
import re
from glob import glob

import numpy as np
import pandas as pd
from joblib import Memory, expires_after

memory = Memory("cachedir")

from . import constants
from .score import exact_match, f1, precision, recall
from .utils import load_data

# hard-code the order of the models for the plot
# otherwise, the order will be alphabetical (and the model size will not be in order)
MODELS = [
    "google/gemma-2-27b-it",
    "google/gemma-2-9b-it",
    "google/gemma-2-2b-it",
    "meta-llama/llama-3.3-70b-instruct",
    "meta-llama/llama-3.1-70b-instruct",
    "meta-llama/llama-3.1-8b-instruct",
    "meta-llama/llama-3.2-3b-instruct",
    "meta-llama/llama-3.2-1b-instruct",
    "microsoft/phi-3.5-moe-instruct",
    "microsoft/phi-3.5-mini-instruct",
    "mistralai/mistral-7b-instruct-v0.3",
    "gemini-1.5-flash-8b-001",
    "gemini-1.5-flash-002",
    "gemini-2.0-flash-exp",
    "gpt-4o-mini-2024-07-18",
    "gpt-4o-2024-11-20",
    "deepseek-ai/deepseek-r1-distill-qwen-32b",
]


def pivot_mean_std(acc_mean_std, metric, independent_variable="_split"):
    """Pivot acc_mean_std so that the specified independent variable becomes the rows"""
    assert (metric, "mean") in acc_mean_std.columns
    assert (metric, "std") in acc_mean_std.columns
    assert ("_model", "") in acc_mean_std.columns
    assert (independent_variable, "") in acc_mean_std.columns

    df_mean = acc_mean_std.pivot(index="_model", columns=independent_variable, values=(metric, "mean"))
    # change the column names to integers
    df_mean.columns = df_mean.columns.astype(int)
    # reorder the columns in ascending order
    df_mean = df_mean[sorted(df_mean.columns)]
    row_order = [name for name in MODELS if name in df_mean.index]
    df_mean = df_mean.loc[row_order]

    df_std = acc_mean_std.pivot(index="_model", columns=independent_variable, values=(metric, "std"))
    # change the column names to integers
    df_std.columns = df_std.columns.astype(int)
    df_std = df_std[sorted(df_std.columns)]
    row_order = [name for name in MODELS if name in df_std.index]
    df_std = df_std.loc[row_order]
    return df_mean, df_std


################ Utils for getting evaluation data ################
def _get_preds(output_dir, method):
    """Get predictions from the output directory corresponding to method `method`

    Args:
        output_dir (str): path to the output directory
        method (str): method used for inference (e.g., zeroshot, fewshot, etc.)

    Returns:
        pd.DataFrame: a dataframe containing the predictions
    """
    # get all files in the output directory
    # NOTE: the actual filenames do not matter, since each row also contains
    # the model, split, batch_size, batch_number, and seed in the metadata and sampling params fields
    files = glob(f"{output_dir}/preds/{method}/*.json")

    if len(files) == 0:
        logging.warning(f"No files found in {output_dir}/preds/{method}/*.json")
        return pd.DataFrame()

    df_list = []
    if False:  # old pred file format to maintain backwards compatibility
        # keys to create auxiliary columns that are useful for analysis
        METADATA = ["model", "split", "batch_size", "batch_number", "type", "seed"]
        SAMPLING_PARAMS = ["seed"]
        for filename in files:
            logging.info(f"Reading from {filename}...")
            df = pd.read_json(filename, orient="index", dtype=False)
            # add new columns corresponding to the metadata
            for key in METADATA:
                df["_" + key] = df["metadata"].apply(lambda x: x[key])
            # # add new columns corresponding to the sampling parameters
            # for key in SAMPLING_PARAMS:
            #     df["_" + key] = df['inference_params'].apply(lambda x: x[key])
            # drop the metadata column
            df = df.drop(columns=["metadata"])
            df_list.append(df)
    else:
        # keys to create auxiliary columns that are useful for analysis
        METADATA = ["model", "split", "batch_size", "batch_number", "type"]
        SAMPLING_PARAMS = ["seed"]
        for filename in files:
            logging.info(f"Reading from {filename}...")
            df = pd.read_json(filename, orient="index", dtype=False)
            # add new columns corresponding to the metadata
            for key in METADATA:
                df["_" + key] = df["metadata"].apply(lambda x: x[key])
            # add new columns corresponding to the sampling parameters
            for key in SAMPLING_PARAMS:
                df["_" + key] = df["inference_params"].apply(lambda x: x[key])
            # drop the metadata column
            df = df.drop(columns=["metadata"])
            df_list.append(df)
    # concatenate all dataframes
    df_preds = pd.concat(df_list)
    # and add a new index from 0 to len(df_preds) so that we can save the dataframe to a json file
    # assign the old index to a new column called 'id'
    df_preds = df_preds.reset_index(names="id")
    return df_preds


def _get_qa_pairs(dataset: str, splits: list[str], from_local: bool = False):
    df_list = []
    for split in splits:
        df = load_data(dataset, split, from_local)["qa_pairs"].to_pandas()
        # # set index to id
        # df = df.set_index('id')
        # convert template column to string
        df["template"] = df["template"].apply(lambda x: " ".join(x))
        # compute the number of hops by taking the length of the prolog query
        df["hops"] = df["prolog"].apply(lambda x: len(x["query"]))
        # determine whether a question is an aggregation question or not
        df["aggregation"] = df["prolog"].apply(lambda x: "aggregate_all" in " ".join(x["query"])).astype(int)
        # determine the number of solutions to each question
        df["solutions"] = df["answer"].apply(lambda x: len(x))
        df_list.append(df)
    # merge on the index
    df_qa_pairs = pd.concat(df_list)
    return df_qa_pairs


@memory.cache(cache_validation_callback=expires_after(hours=4))
def get_evaluation_data(
    output_dir: str,
    method: str,
    dataset: str,
    from_local: bool = False,
    sep: str = constants.answer_sep,
):
    """Get the evaluation data for a given method

    First reads the predictions from the output directory, then joins with the qa pairs.
    NOTE: The results are cached for 1 hour at `cachedir` (see `memory` object).

    Args:
        output_dir (str): path to the output directory
        method (str): method used for inference (e.g., zeroshot, fewshot, etc.)
        dataset (str): dataset name (e.g., "mlcore/phantom-wiki", "mlcore/phantom-wiki-v0.2")
        from_local (bool) : if loading the data from a local folder.
            Default is False.
        sep (str): separator when pre-processing pred/true strings.
            Default is `constants.answer_sep`.

    Returns:
        pd.DataFrame: a dataframe containing the evaluation data,
            including the predictions, the qa pairs (with auxiliary columns),
            and per-instance evaluation metrics
    """
    # get the predictions
    df_preds = _get_preds(output_dir, method)
    if df_preds.empty:
        return df_preds
    # get unique splits
    splits = df_preds["_split"].unique().tolist()
    # get the qa pairs
    df_qa_pairs = _get_qa_pairs(dataset, splits, from_local)
    # join with original qa pairs to get additional information about
    # the prolog queries and the templates
    df = df_preds.merge(df_qa_pairs, on="id", how="left")

    # join the true answers with the appropriate separator since the scoring functions expect strings
    df["EM"] = df.apply(lambda x: exact_match(x["pred"], sep.join(x["true"]), sep=sep), axis=1)
    df["precision"] = df.apply(lambda x: precision(x["pred"], sep.join(x["true"]), sep=sep), axis=1)
    df["recall"] = df.apply(lambda x: recall(x["pred"], sep.join(x["true"]), sep=sep), axis=1)
    df["f1"] = df.apply(lambda x: f1(x["pred"], sep.join(x["true"]), sep=sep), axis=1)

    # add a column for the data seed
    df["_depth"] = (
        df["_split"].apply(lambda x: re.match(r"depth_(\d+)_size_(\d+)_seed_(\d+)", x).group(1)).astype(int)
    )
    df["_size"] = (
        df["_split"].apply(lambda x: re.match(r"depth_(\d+)_size_(\d+)_seed_(\d+)", x).group(2)).astype(int)
    )
    df["_data_seed"] = (
        df["_split"].apply(lambda x: re.match(r"depth_(\d+)_size_(\d+)_seed_(\d+)", x).group(3)).astype(int)
    )
    # drop the split column
    df = df.drop(columns=["_split"])
    return df


def mean(x):
    """Aggregation function that computes the mean of a given metric"""
    return x.mean()


def std(x):
    """Aggregation function that computes the standard error of the mean of a given metric"""
    return x.std(ddof=1) / np.sqrt(len(x))
