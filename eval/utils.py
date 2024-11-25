from datasets import load_dataset

def load_data(split):
    """
    Load the phantom-wiki dataset from HuggingFace for a specific split.
    """
    qa_pairs = load_dataset("mlcore/phantom-wiki", "question-answer")[split]
    text = load_dataset("mlcore/phantom-wiki", "text-corpus")[split]

    dataset = {"qa_pairs": qa_pairs, "text": text}
    return dataset


def get_all_articles(dataset):
    """
    Get all articles for a given split.
    """
    article_list = [item['article'] for item in dataset]
    all_article = '\n'.join(article_list)
    return all_article
