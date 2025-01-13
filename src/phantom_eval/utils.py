import argparse
import logging

from datasets import load_dataset, Dataset


def load_data(dataset: str, split: str) -> dict[str, Dataset]:
    """
    Load the phantom-wiki dataset from HuggingFace for a specific split.
    example: load_data("depth6")
    """
    qa_pairs = load_dataset(dataset, "question-answer")[split]
    text = load_dataset(dataset, "text-corpus")[split]

    dataset = {"qa_pairs": qa_pairs, "text": text}
    return dataset


def get_relevant_articles(dataset: Dataset, name_list: list[str]) -> str:
    """
    Get articles for a certain list of names.
    """
    relevant_articles = []
    for name in name_list:
        relevant_articles.extend([entry['article'] for entry in dataset['text'] if entry['title']==name])
    relevant_articles = "\n================\n\n".join(relevant_articles)
    return relevant_articles


def normalize_pred(pred: str, sep: str) -> set[str]:
    """
    Normalize the prediction by splitting and stripping whitespace the answers.

    Args:
        pred (str): The prediction string of format "A<sep>B<sep>C".
        sep (str): The separator used to split the prediction.

    Returns:
        set[str]: A set of normalized answers.
    """
    # Operations:
    # 1. Split by separator
    # 2. Strip whitespace
    # 3. Lowercase
    # 4. Convert to set to remove duplicates
    return set(
        map(str.lower,
        map(str.strip,
            pred.split(sep)
        ))
    )


def setup_logging(log_level: str) -> str:
    # Suppress httpx logging from API requests
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

