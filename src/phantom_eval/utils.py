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
    # article_list = [item['article'] for item in dataset]
    # all_article = '\n'.join(article_list)
    # return all_article

def get_parser():
    parser = ArgumentParser(description="PhantomWiki Evaluation")
    parser.add_argument("--model", "-m", type=str, default='llama-3.1-8b',
                        help="Base model for inference (for HF and Together models, replace '/' with '::')" \
                        "llama-3.1-8b, llama-3.1-70b, llama-3.1-405b" \
                        "microsoft::phi-3.5-mini-instruct" \
                        "google::gemma-2-2b-it, google::gemma-2-9b-it")
    parser.add_argument("--max_model_len", type=int, default=4096,
                        help="Maximum model length (vLLM param)")
    parser.add_argument("--tensor_parallel_size", type=int, default=1,
                        help="number of gpus (vLLM param")
    parser.add_argument("--temperature", "-T", type=float, default=0.7,
                        help="Temperature for sampling")
    parser.add_argument("--top_p", "-p", type=float, default=0.7,
                        help="Top-p for sampling")
    parser.add_argument("--top_k", "-k", type=float, default=50,
                        help="Top-k for sampling")
    parser.add_argument("--repetition_penalty", "-rp", type=float, default=1.0,
                        help="Repetition penalty for sampling")
    parser.add_argument("--use_together", "-together", action="store_true", default=False,
                        help="Use Together for inference")
    parser.add_argument("--output_dir", "-od", default="out",
                    help="Path to read/write the outputs")
    parser.add_argument("--split", "-s", default="depth_6_size_26_seed_1", type=str,
                        help="Dataset split (e.g., train, val, test)")
    parser.add_argument("--batch_size", "-bs", default=10, type=int,
                        help="Batch size (>=1)")
    parser.add_argument("--batch_number", "-bn", default=1, type=int,
                        help="Batch number (>=1). For example, if batch_size=100 and batch_number=1," \
                            "then the first 100 questions will be evaluated")
    return parser