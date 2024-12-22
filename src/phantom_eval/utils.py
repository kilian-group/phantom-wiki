import argparse
import logging

from datasets import load_dataset, Dataset

from .llm import SUPPORTED_LLM_NAMES


def load_data(split: str) -> dict[str, Dataset]:
    """
    Load the phantom-wiki dataset from HuggingFace for a specific split.
    example: load_data("depth6")
    """
    qa_pairs = load_dataset("mlcore/phantom-wiki", "question-answer")[split]
    text = load_dataset("mlcore/phantom-wiki", "text-corpus")[split]

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


def setup_logging(log_level: str) -> str:
    # Suppress httpx logging from API requests
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PhantomWiki Evaluation")
    parser.add_argument("--model_name", "-m", type=str, default="together:meta-llama/Llama-Vision-Free",
                        help="model name. " \
                            "NOTE: to add a new model, please submit a PR to the repo with the new model name", 
                        choices=SUPPORTED_LLM_NAMES)
    parser.add_argument("--model_path", type=str, default=None, help="Path to the model")
    parser.add_argument("--method", type=str, required=True,
                        help="Evaluation method. " \
                            "NOTE: to add a new method, please submit a PR with the implementation",
                        choices=["zeroshot", "fewshot", "CoT", "react"])
    
    # Method params
    parser.add_argument("--react_max_steps", type=int, default=6,
                        help="Maximum number of steps for the ReAct agent")

    # LLM inference params
    parser.add_argument("--inf_vllm_max_model_len", type=int, default=None,
                        help="Maximum model length (vLLM param)" \
                        "if None, uses max model length specified in model config")
    parser.add_argument("--inf_vllm_tensor_parallel_size", type=int, default=None,
                        help="number of gpus (vLLM param)" \
                        "if None, uses all available gpus")
    parser.add_argument("--inf_max_tokens", type=int, default=4096,
                        help="Maximum number of tokens to generate")
    parser.add_argument("--inf_temperature", "-T", type=float, default=0.0,
                        help="Temperature for sampling")
    parser.add_argument("--inf_top_p", "-p", type=float, default=0.7,
                        help="Top-p for sampling")
    parser.add_argument("--inf_top_k", "-k", type=int, default=50,
                        help="Top-k for sampling")
    parser.add_argument("--inf_repetition_penalty", "-r", type=float, default=1.0,
                        help="Repetition penalty for sampling")
    parser.add_argument("--inf_seed_list", type=int, nargs="+", default=[1],
                        help="List of seeds to evaluate")
    parser.add_argument("--inf_max_retries", type=int, default=3,
                        help="Number of tries to get response")
    parser.add_argument("--inf_wait_seconds", type=int, default=2,
                        help="Seconds to wait between tries")

    # Dataset params
    parser.add_argument("--split_list", default=["depth_10_size_26_seed_1"], type=str, nargs="+",
                        help="List of dataset splits to evaluate")
    parser.add_argument("--batch_size", "-bs", default=10, type=int,
                        help="Batch size (>=1)")
    parser.add_argument("--batch_number", "-bn", default=None, type=int,
                        help="Batch number (>=1). For example, if batch_size=100 and batch_number=1, " \
                            "then the first 100 questions will be evaluated " \
                            "if None (default), all batches will be evaluated")
    # Saving params
    parser.add_argument("--output_dir", "-od", default="out",
                    help="Path to read/write the outputs")
    parser.add_argument("--log_level", default="INFO", type=str.upper,
                        help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])

    return parser