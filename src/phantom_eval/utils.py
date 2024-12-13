from datasets import load_dataset
from argparse import ArgumentParser

def load_data(split):
    """
    Load the phantom-wiki dataset from HuggingFace for a specific split.
    example: load_data("depth6")
    """
    qa_pairs = load_dataset("mlcore/phantom-wiki", "question-answer")[split]
    text = load_dataset("mlcore/phantom-wiki", "text-corpus")[split]

    dataset = {"qa_pairs": qa_pairs, "text": text}
    return dataset


def get_all_articles(dataset):
    """
    Get all articles for a given split.
    """
    all_articles = "\n================\n\n".join(dataset['text']['article'])
    return all_articles

def get_relevant_articles(dataset, name_list:list):
    """
    Get articles for a certain list of names.
    """
    relevant_articles = []
    for name in name_list:
        relevant_articles.extend([entry['article'] for entry in dataset['text'] if entry['title']==name])
    relevant_articles = "\n================\n\n".join(relevant_articles)
    return relevant_articles

LOCAL_MODELS = [
    # HF models (run via vLLM)
    "meta-llama/llama-3.1-8b-instruct", 
    "meta-llama/llama-3.1-70b-instruct", 
    "microsoft/phi-3.5-mini-instruct",
    "microsoft/phi-3.5-moe-instruct",
    "google/gemma-2-2b-it",
    "google/gemma-2-9b-it",
    "google/gemma-2-27b-it",
    "mistralai/mistral-7b-instruct-v0.3",
]
MODEL_CHOICES = LOCAL_MODELS + [
    # Together models (https://docs.together.ai/docs/serverless-models)
    "together:meta-llama/llama-3.1-8b-instruct", 
    "together:meta-llama/llama-3.1-70b-instruct", 
    "together:meta-llama/llama-3.1-405b-instruct",
    # OpenAI models (https://platform.openai.com/docs/models)
    "gpt-4o-mini-2024-07-18",
    "gpt-4o-2024-11-20",
    # Anthropic models (https://docs.anthropic.com/en/docs/about-claude/models)
    "claude-3-5-haiku-20241022",
    "claude-3-5-sonnet-20241022",
    # Google models (https://ai.google.dev/gemini-api/docs/models/gemini)
    "gemini-1.5-flash-002",
    "gemini-1.5-pro-002",
]

def get_parser():
    parser = ArgumentParser(description="PhantomWiki Evaluation")
    parser.add_argument("--model", "-m", type=str.lower, default='llama-3.1-8b',
                        help="model name (case insensitive) "\
                            "NOTE: to add a new model, please submit a PR to the repo with the new model name", 
                        choices=MODEL_CHOICES)
    # LLM inference params
    parser.add_argument("--max_model_len", type=int, default=None,
                        help="Maximum model length (vLLM param)")
    parser.add_argument("--tensor_parallel_size", type=int, default=1,
                        help="number of gpus (vLLM param")
    parser.add_argument("--temperature", "-T", type=float, default=0.7,
                        help="Temperature for sampling")
    parser.add_argument("--top_p", "-p", type=float, default=0.7,
                        help="Top-p for sampling")
    parser.add_argument("--top_k", "-k", type=float, default=50,
                        help="Top-k for sampling")
    parser.add_argument("--seed", type=int, default=1,
                        help="Seed for sampling (vLLM param)")
    # Dataset params
    parser.add_argument("--split", "-s", default="depth_6_size_26_seed_1", type=str,
                        help="Dataset split (e.g., train, val, test)")
    parser.add_argument("--batch_size", "-bs", default=10, type=int,
                        help="Batch size (>=1)")
    parser.add_argument("--batch_number", "-bn", default=1, type=int,
                        help="Batch number (>=1). For example, if batch_size=100 and batch_number=1," \
                            "then the first 100 questions will be evaluated")
    # Saving params
    parser.add_argument("--output_dir", "-od", default="out",
                    help="Path to read/write the outputs")
    return parser