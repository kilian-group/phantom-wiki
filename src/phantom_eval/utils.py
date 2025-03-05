import logging
import re

from datasets import Dataset, load_dataset
from joblib import Memory, expires_after

#
# RESTRICT TO LOW DEPTH QUESTIONS (i.e., questions generated from the CFG with depth=10)
# Note that the full dataset is generated using depth=20, but we can filter the
# question-answer pairs by the template used to generate the question, which is
# stored in the 'template' column of the dataframe.
#
from nltk import CFG

from phantom_wiki.facts.templates import QA_GRAMMAR_STRING, generate_templates
from phantom_wiki.utils.hf_datasets import PhantomWikiDatasetBuilder

memory = Memory("cachedir")
grammar = CFG.fromstring(QA_GRAMMAR_STRING)


@memory.cache(cache_validation_callback=expires_after(hours=4))
def load_data(dataset: str, split: str = None, from_local: bool = False) -> dict[str, Dataset]:
    """Load the phantom-wiki dataset from HuggingFace for a specific split or load from a local folder.

    NOTE: Split does not necessarily have to exist on HF. We can dynamically construct
    a split by using the fact that if if A <= B, then the questions generated
    using depth=A are strictly contained in the questions generated using depth=B.

    TODO: implement a test to check that the question-answer pairs returned by this
    function is the same as the question-answer pairs had we truly generated a dataset
    instance with the exact depth, size, seed.

    Args:
        dataset:
            if from_local=False: The name of the dataset on HF to load.
            if from_local=True: The path to the local folder.
        split:
            if from_local=False: The split of the dataset on HF to load.
            if from_local=True: The subdirectory of the local folder.
        from_local: Whether to load the dataset from a local folder.

    Returns:
        A dictionary containing the loaded datasets.
    Example:
        >>> from phantom_eval.utils import load_data
        >>> dataset = load_data("mlcore/phantom-wiki-v050", split="depth_20_size_50_seed_1") # load from HF
        >>> dataset = load_data("path_to_out_dir", "sub_dir", from_local=True) # load from local folder
    """

    def _get_params(split: str) -> tuple[int, int, int]:
        """Extract the depth, size, and seed from the split string."""

        # if loading from HF, the split has to match the format like "depth_20_size_50_seed_1"
        if not from_local:
            if match := re.search(r"depth_(\d+)_size_(\d+)_seed_(\d+)", split):
                depth, size, seed = match.groups()
                return int(depth), int(size), int(seed)
            else:
                raise ValueError(f"Invalid split format: {split}")

    if not from_local:
        ds_text_corpus = load_dataset(dataset, "text-corpus", trust_remote_code=True)
        ds_question_answer = load_dataset(dataset, "question-answer", trust_remote_code=True)
        ds_database = load_dataset(dataset, "database", trust_remote_code=True)
    else:
        builder_text_corpus = PhantomWikiDatasetBuilder(
            config_name="text-corpus", data_dir=f"{dataset}/{split}"
        )
        builder_text_corpus.download_and_prepare()
        ds_text_corpus = builder_text_corpus.as_dataset()

        builder_question_answer = PhantomWikiDatasetBuilder(
            config_name="question-answer", data_dir=f"{dataset}/{split}"
        )
        builder_question_answer.download_and_prepare()
        ds_question_answer = builder_question_answer.as_dataset()

        builder_database = PhantomWikiDatasetBuilder(config_name="database", data_dir=f"{dataset}/{split}")
        builder_database.download_and_prepare()
        ds_database = builder_database.as_dataset()

    available_splits = ds_question_answer.keys()

    if split in available_splits:
        logging.info(f"Using split {split} from dataset {dataset}.")
        return {
            "qa_pairs": ds_question_answer[split],
            "text": ds_text_corpus[split],
            "database": ds_database[split],
        }
    else:
        requested_depth, requested_size, requested_seed = _get_params(split)
        requested_question_templates = [
            question for question, _, _ in generate_templates(grammar, depth=requested_depth)
        ]
        # NOTE: requested_question_templates is a list of lists

        for s in available_splits:
            depth, size, seed = _get_params(s)
            if requested_depth <= depth and requested_size == size and requested_seed == seed:
                logging.info(f"Requested split {split} not found. Using subset of split {s} instead.")
                # filter by template (NOTE: each template is a list of strings)
                qa_pairs = ds_question_answer[s].filter(
                    lambda x: x["template"] in requested_question_templates
                )
                return {
                    "qa_pairs": qa_pairs,
                    # the text corpus remains the same, since it is not generated from the CFG
                    "text": ds_text_corpus[s],
                    "database": ds_database[s],
                }
        raise ValueError(
            f"Split {split} not found in dataset {dataset}. Available splits: {available_splits}"
        )


def get_relevant_articles(dataset: Dataset, name_list: list[str]) -> str:
    """
    Get articles for a certain list of names.
    """
    relevant_articles = []
    for name in name_list:
        relevant_articles.extend([entry["article"] for entry in dataset["text"] if entry["title"] == name])
    relevant_articles = "\n================\n\n".join(relevant_articles)
    return relevant_articles


def normalize_pred(pred: str, sep: str) -> set[str]:
    """
    Normalize the prediction by splitting and stripping whitespace the answers.

    Operations:
    1. Split by separator
    2. Strip whitespace
    3. Lowercase
    4. Convert to set to remove duplicates

    Args:
        pred (str): The prediction string of format "A<sep>B<sep>C".
        sep (str): The separator used to split the prediction.

    Returns:
        set[str]: A set of normalized answers.
    """
    return set(map(str.lower, map(str.strip, pred.split(sep))))


def setup_logging(log_level: str):
    # Suppress httpx logging from API requests
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
