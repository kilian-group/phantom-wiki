"""
Script to aggregate ReAct predictions and compute metrics.
Usage:
    python evaluate.py --output_dir path/to/out/react/
"""
import argparse
from pathlib import Path
from typing import Iterator

import pandas as pd
from phantom_eval.score import match, precision, recall, f1


def main(args: argparse.Namespace) -> None:
    pred_dir: Path = Path(args.output_dir) / "preds"
    json_files: list[Path] = list(pred_dir.glob("*.json"))
    assert len(json_files) > 0, f"No JSON files found in {args.output_dir}/preds/"

    # Collect all JSON files as a single dataframe
    df_list: list[pd.DataFrame] = []
    # keys in the metadata to create new columns
    METADATA = ["model", "split", "batch_size", "batch_number", "type"]
    for json_file in json_files:
        print(f"* Reading from {json_file}")
        df = pd.read_json(json_file, orient="index", dtype=False)
        # add new columns corresponding to the metadata
        for key in METADATA:
            df["_" + key] = df["metadata"].apply(lambda x: x[key])
        # drop the metadata column
        df = df.drop(columns=["metadata"])
        df_list.append(df)

    # Concatenate all dataframes
    df = pd.concat(df_list)

    # Convert preds and true columns to str from list by joining
    # Because the scoring functions expect strings
    sep = ","
    df["pred"] = df["pred"].apply(lambda x: sep.join(x))
    df["true"] = df["true"].apply(lambda x: sep.join(x))

    # Compute scores
    df["EM"] = df.apply(lambda x: match(x["pred"], x["true"]), axis=1)
    df["precision"] = df.apply(lambda x: precision(x["pred"], x["true"], sep=sep), axis=1)
    df["recall"] = df.apply(lambda x: recall(x["pred"], x["true"], sep=sep), axis=1)
    df["f1"] = df.apply(lambda x: f1(x["pred"], x["true"], sep=sep), axis=1)
    # print(df)

    # Group by model, split, and type of question, and compute metrics
    grouped = df.groupby(["_model", "_split", "_type"])
    acc = grouped[["EM", "precision", "recall", "f1"]].mean()
    print(acc.to_markdown())

    # Save file
    acc_save_path: Path = pred_dir / "metrics.csv"
    acc.to_csv(acc_save_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Evalute ReAct predictions")
    parser.add_argument("--output_dir")

    args = parser.parse_args()
    main(args)
