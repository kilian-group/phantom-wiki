"""Utilities for computing evaluation metrics given prediction files
"""
from glob import glob
import pandas as pd

from .utils import load_data
from .score import (match,
                    precision,
                    recall,
                    f1)

def get_preds(output_dir, method):
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
    df_list = []
    # keys to create auxiliary columns that are useful for analysis
    METADATA = [
        'model', 'split', 'batch_size', 'batch_number', 'type', 
        # 'seed'
    ]
    SAMPLING_PARAMS = ['seed']
    for filename in files:
        print(f"Reading from {filename}...")
        df = pd.read_json(filename, orient='index', dtype=False)
        # add new columns corresponding to the metadata
        for key in METADATA:
            df["_" + key] = df['metadata'].apply(lambda x: x[key])
        # add new columns corresponding to the sampling parameters
        for key in SAMPLING_PARAMS:
            df["_" + key] = df['inference_params'].apply(lambda x: x[key])
        # drop the metadata column
        df = df.drop(columns=['metadata'])
        df_list.append(df)
    # concatenate all dataframes
    df_preds = pd.concat(df_list)
    return df_preds

def get_qa_pairs(splits):
    df_list = []
    for split in splits:
        df = load_data(split)['qa_pairs'].to_pandas()
        # set index to id
        df = df.set_index('id')
        # convert template column to string
        df['template'] = df['template'].apply(lambda x : ' '.join(x))
        # compute the number of hops by taking the length of the prolog query
        df['hops'] = df['prolog'].apply(lambda x : len(x['query']))
        # determine whether a question is an aggregation question or not
        df['aggregation'] = df['prolog'].apply(lambda x : 'aggregate_all' in ' '.join(x['query'])).astype(int)
        # determine the number of solutions to each question
        df['solutions'] = df['answer'].apply(lambda x : len(x))
        df_list.append(df)
    # merge on the index
    df_qa_pairs = pd.concat(df_list)
    return df_qa_pairs

def get_evaluation_data(output_dir, method, sep=', '):
    """Get the evaluation data for a given method

    Args:
        output_dir (str): path to the output directory
        method (str): method used for inference (e.g., zeroshot, fewshot, etc.)
        sep (str): separator when pre-processing pred/true strings

    Returns:
        pd.DataFrame: a dataframe containing the evaluation data, 
            including the predictions, the qa pairs, and per-instance evaluation metrics
    """
    # get the predictions
    df_preds = get_preds(output_dir, method)
    # get unique splits
    splits = df_preds['_split'].unique()
    # get the qa pairs
    df_qa_pairs = get_qa_pairs(splits)
    # join with original qa pairs to get additional information about
    # the prolog queries and the templates
    df = df_preds.merge(df_qa_pairs, left_index=True, right_index=True, how='left')

    # NOTE: we join the true answers with the appropriate seperator
    # since the scoring functions expect strings
    df['EM'] = df.apply(lambda x: match(x['pred'], sep.join(x['true']), exact=True, sep=sep), axis=1)
    df['precision'] = df.apply(lambda x: precision(x['pred'], sep.join(x['true']), sep=sep), axis=1)
    df['recall'] = df.apply(lambda x: recall(x['pred'], sep.join(x['true']), sep=sep), axis=1)
    df['f1'] = df.apply(lambda x: f1(x['pred'], sep.join(x['true']), sep=sep), axis=1)
    return df
