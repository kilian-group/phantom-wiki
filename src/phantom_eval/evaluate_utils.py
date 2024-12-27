"""Utilities for computing evaluation metrics given prediction files
"""
from glob import glob
import pandas as pd

from .utils import load_data
from .score import (exact_match,
                    precision,
                    recall,
                    f1)
from . import constants

################ Utils and macros for plotting ################
# create a plot
import matplotlib.pyplot as plt
# utils for plotting
plt.rcParams.update({
    'font.size': 24,
    'font.family': 'serif',
    'mathtext.fontset': 'stix',
    'axes.labelsize': 30,
    'axes.titlesize': 30,
    'xtick.labelsize': 24,
    'ytick.labelsize': 24,
    'legend.fontsize': 24,
    'axes.linewidth': 0.8,
    'lines.linewidth': 3,
    'lines.markersize': 10,
    'axes.spines.top': False,
    'axes.spines.right': False,
})
# hard-code the order of the models for the plot
# otherwise, the order will be alphabetical (and the model size will not be in order)
MODELS = [
    'google/gemma-2-27b-it',
    'google/gemma-2-9b-it',
    'google/gemma-2-2b-it',
    'meta-llama/llama-3.3-70b-instruct',
    'meta-llama/llama-3.1-70b-instruct',
    'meta-llama/llama-3.1-8b-instruct',
    'meta-llama/llama-3.2-3b-instruct',
    'meta-llama/llama-3.2-1b-instruct',
    'microsoft/phi-3.5-moe-instruct',
    'microsoft/phi-3.5-mini-instruct',
    'mistralai/mistral-7b-instruct-v0.3',
    'gemini-1.5-flash-8b-001',
    'gemini-1.5-flash-002',
    'gemini-2.0-flash-exp',
]
COLORS = {
    'google/gemma-2-27b-it': 'tab:blue',
    'google/gemma-2-9b-it': 'tab:blue',
    'google/gemma-2-2b-it': 'tab:blue',
    'meta-llama/llama-3.3-70b-instruct': 'tab:orange',
    'meta-llama/llama-3.1-70b-instruct': 'tab:orange',
    'meta-llama/llama-3.1-8b-instruct': 'tab:orange',
    'meta-llama/llama-3.2-3b-instruct': 'tab:orange',
    'meta-llama/llama-3.2-1b-instruct': 'tab:orange',
    'microsoft/phi-3.5-mini-instruct': 'tab:green',
    'microsoft/phi-3.5-mini-instruct': 'tab:green',
    'mistralai/mistral-7b-instruct-v0.3' : 'tab:red',
    'gemini-1.5-flash-002': 'tab:purple',
    'gemini-1.5-flash-8b-001': 'tab:purple',
    'gemini-2.0-flash-exp': 'tab:purple',
}
LINESTYLES = {
    'google/gemma-2-27b-it': '-',
    'google/gemma-2-9b-it': '--',
    'google/gemma-2-2b-it': 'dotted',
    'meta-llama/llama-3.3-70b-instruct': 'dashdot',
    'meta-llama/llama-3.1-70b-instruct': '-',
    'meta-llama/llama-3.1-8b-instruct': '--',
    'meta-llama/llama-3.2-3b-instruct': 'dotted',
    'meta-llama/llama-3.2-1b-instruct': (10, (1, 10)), # loosely dotted
    'microsoft/phi-3.5-moe-instruct': '-',
    'microsoft/phi-3.5-mini-instruct': '--',
    'mistralai/mistral-7b-instruct-v0.3' : '-',
    'gemini-2.0-flash-exp': '-',
    'gemini-1.5-flash-002': '--',
    'gemini-1.5-flash-8b-001': 'dotted',
}

def pivot_mean_std(acc_mean_std, metric, independent_variable='_split'):
    """Pivot acc_mean_std so that the specified independent variable becomes the rows
    """
    assert (metric, 'mean') in acc_mean_std.columns
    assert (metric, 'std') in acc_mean_std.columns
    assert ('_model', '') in acc_mean_std.columns
    assert (independent_variable, '') in acc_mean_std.columns

    df_mean = acc_mean_std.pivot(index='_model', columns=independent_variable, values=(metric, 'mean'))
    # change the column names to integers
    df_mean.columns = df_mean.columns.astype(int)
    # reorder the columns in ascending order
    df_mean = df_mean[sorted(df_mean.columns)]
    row_order = [name for name in MODELS if name in df_mean.index]
    df_mean = df_mean.loc[row_order]

    df_std = acc_mean_std.pivot(index='_model', columns=independent_variable, values=(metric, 'std'))
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
    df_list = []
    if False: # old pred file format to maintain backwards compatibility
        # keys to create auxiliary columns that are useful for analysis
        METADATA = [
            'model', 'split', 'batch_size', 'batch_number', 'type', 
            'seed'
        ]
        SAMPLING_PARAMS = ['seed']
        for filename in files:
            print(f"Reading from {filename}...")
            df = pd.read_json(filename, orient='index', dtype=False)
            # add new columns corresponding to the metadata
            for key in METADATA:
                df["_" + key] = df['metadata'].apply(lambda x: x[key])
            # # add new columns corresponding to the sampling parameters
            # for key in SAMPLING_PARAMS:
            #     df["_" + key] = df['inference_params'].apply(lambda x: x[key])
            # drop the metadata column
            df = df.drop(columns=['metadata'])
            df_list.append(df)
    else:
        # keys to create auxiliary columns that are useful for analysis
        METADATA = ['model', 'split', 'batch_size', 'batch_number', 'type']
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

def _get_qa_pairs(splits):
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

def get_evaluation_data(output_dir: str, method: str, sep: str = constants.answer_sep):
    """Get the evaluation data for a given method

    Args:
        output_dir (str): path to the output directory
        method (str): method used for inference (e.g., zeroshot, fewshot, etc.)
        sep (str): separator when pre-processing pred/true strings

    Returns:
        pd.DataFrame: a dataframe containing the evaluation data, 
            including the predictions, the qa pairs (with auxiliary columns), 
            and per-instance evaluation metrics
    """
    # get the predictions
    df_preds = _get_preds(output_dir, method)
    # get unique splits
    splits = df_preds['_split'].unique()
    # get the qa pairs
    df_qa_pairs = _get_qa_pairs(splits)
    # join with original qa pairs to get additional information about
    # the prolog queries and the templates
    df = df_preds.merge(df_qa_pairs, left_index=True, right_index=True, how='left')

    # join the true answers with the appropriate seperator since the scoring functions expect strings
    df['EM'] = df.apply(lambda x: exact_match(x['pred'], sep.join(x['true']), sep=sep), axis=1)
    df['precision'] = df.apply(lambda x: precision(x['pred'], sep.join(x['true']), sep=sep), axis=1)
    df['recall'] = df.apply(lambda x: recall(x['pred'], sep.join(x['true']), sep=sep), axis=1)
    df['f1'] = df.apply(lambda x: f1(x['pred'], sep.join(x['true']), sep=sep), axis=1)
    return df
