# Adapted from: https://github.com/RUC-NLPIR/FlashRAG/blob/main/flashrag/retriever/retriever.py
# License: MIT
import json
import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"
import functools
import warnings

import faiss
import numpy as np
from flashrag.retriever.encoder import Encoder, STEncoder
from flashrag.retriever.utils import convert_numpy, load_corpus, load_docs
from flashrag.utils import get_reranker


def cache_manager(func):
    """
    Decorator used for retrieving document cache.
    With the decorator, The retriever can store each retrieved document as a file and reuse it.
    """

    @functools.wraps(func)
    def wrapper(self, query=None, num=None, return_score=False):
        if num is None:
            num = self.topk
        if self.use_cache:
            if isinstance(query, str):
                new_query_list = [query]
            else:
                new_query_list = query

            no_cache_query = []
            cache_results = []
            for new_query in new_query_list:
                if new_query in self.cache:
                    cache_res = self.cache[new_query]
                    if len(cache_res) < num:
                        warnings.warn(f"The number of cached retrieval results is less than topk ({num})")
                    cache_res = cache_res[:num]
                    # separate the doc score
                    doc_scores = [item["score"] for item in cache_res]
                    cache_results.append((cache_res, doc_scores))
                else:
                    cache_results.append(None)
                    no_cache_query.append(new_query)

            if no_cache_query != []:
                # use batch search without decorator
                no_cache_results, no_cache_scores = self._batch_search_with_rerank(no_cache_query, num, True)
                no_cache_idx = 0
                for idx, res in enumerate(cache_results):
                    if res is None:
                        assert new_query_list[idx] == no_cache_query[no_cache_idx]
                        cache_results[idx] = (
                            no_cache_results[no_cache_idx],
                            no_cache_scores[no_cache_idx],
                        )
                        no_cache_idx += 1

            results, scores = (
                [t[0] for t in cache_results],
                [t[1] for t in cache_results],
            )

        else:
            results, scores = func(self, query=query, num=num, return_score=True)

        if self.save_cache:
            # merge result and score
            save_results = results.copy()
            save_scores = scores.copy()
            if isinstance(query, str):
                query = [query]
                if "batch" not in func.__name__:
                    save_results = [save_results]
                    save_scores = [save_scores]
            for new_query, doc_items, doc_scores in zip(query, save_results, save_scores):
                for item, score in zip(doc_items, doc_scores):
                    item["score"] = score
                self.cache[new_query] = doc_items

        if return_score:
            return results, scores
        else:
            return results

    return wrapper


def rerank_manager(func):
    """
    Decorator used for reranking retrieved documents.
    """

    @functools.wraps(func)
    def wrapper(self, query, num=None, return_score=False):
        results, scores = func(self, query=query, num=num, return_score=True)
        if self.use_reranker:
            results, scores = self.reranker.rerank(query, results)
            if "batch" not in func.__name__:
                results = results[0]
                scores = scores[0]
        if return_score:
            return results, scores
        else:
            return results

    return wrapper


class BaseRetriever:
    """Base object for all retrievers."""

    def __init__(self, config):
        self._config = config
        self.update_config()

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, config_data):
        self._config = config_data
        self.update_config()

    def update_config(self):
        self.update_base_setting()
        self.update_additional_setting()

    def update_base_setting(self):
        self.retrieval_method = self._config["retrieval_method"]
        self.topk = self._config["retrieval_topk"]

        self.index_path = self._config["index_path"]
        self.corpus_path = self._config["corpus_path"]

        self.save_cache = self._config["save_retrieval_cache"]
        self.use_cache = self._config["use_retrieval_cache"]
        self.cache_path = self._config["retrieval_cache_path"]

        self.use_reranker = self._config["use_reranker"]
        if self.use_reranker:
            self.reranker = get_reranker(self._config)
        else:
            self.reranker = None

        if self.save_cache:
            self.cache_save_path = os.path.join(self._config["save_dir"], "retrieval_cache.json")
            self.cache = {}
        if self.use_cache:
            assert self.cache_path is not None
            with open(self.cache_path) as f:
                self.cache = json.load(f)
        self.silent = self._config["silent_retrieval"] if "silent_retrieval" in self._config else False

    def update_additional_setting(self):
        pass

    def _save_cache(self):
        self.cache = convert_numpy(self.cache)

        def custom_serializer(obj):
            if isinstance(obj, np.float32):
                return float(obj)
            raise TypeError(f"Type {type(obj)} not serializable")

        with open(self.cache_save_path, "w") as f:
            json.dump(self.cache, f, indent=4, default=custom_serializer)

    def _search(self, query: str, num: int, return_score: bool) -> list[dict[str, str]]:
        r"""Retrieve topk relevant documents in corpus.

        Return:
            list: contains information related to the document, including:
                contents: used for building index
                title: (if provided)
                text: (if provided)

        """

    def _batch_search(self, query, num, return_score):
        pass

    def search(self, *args, **kwargs):
        return self._search(*args, **kwargs)

    def batch_search(self, *args, **kwargs):
        return self._batch_search(*args, **kwargs)


class BaseTextRetriever(BaseRetriever):
    """Base text retriever."""

    def __init__(self, config):
        super().__init__(config)

    @cache_manager
    @rerank_manager
    def search(self, *args, **kwargs):
        return self._search(*args, **kwargs)

    @cache_manager
    @rerank_manager
    def batch_search(self, *args, **kwargs):
        return self._batch_search(*args, **kwargs)

    @rerank_manager
    def _batch_search_with_rerank(self, *args, **kwargs):
        return self._batch_search(*args, **kwargs)

    @rerank_manager
    def _search_with_rerank(self, *args, **kwargs):
        return self._search(*args, **kwargs)


class BM25Retriever(BaseTextRetriever):
    r"""BM25 retriever based on pre-built bm25s index."""

    def __init__(self, config, corpus=None):
        super().__init__(config)
        self.load_model_corpus(corpus)

    def update_additional_setting(self):
        self.backend = "bm25s"

    def load_model_corpus(self, corpus):
        # only us bm25s backend
        import bm25s
        import Stemmer

        self.corpus = load_corpus(self.corpus_path)
        self.searcher = bm25s.BM25.load(self.index_path, mmap=True, load_corpus=False)

        stemmer = Stemmer.Stemmer("english")
        self.tokenizer = bm25s.tokenization.Tokenizer(stopwords="en", stemmer=stemmer)
        self.tokenizer.load_stopwords(self.index_path)
        self.tokenizer.load_vocab(self.index_path)

        self.searcher.corpus = self.corpus
        self.searcher.backend = "numba"

    def _check_contain_doc(self):
        r"""Check if the index contains document content"""
        return self.searcher.doc(0).raw() is not None

    def _search(self, query: str, num: int = None, return_score=False) -> list[dict[str, str]]:
        if num is None:
            num = self.topk

        query_tokens = self.tokenizer.tokenize([query], return_as="tuple", update_vocab=False)
        results, scores = self.searcher.retrieve(query_tokens, k=num)
        results = list(results[0])
        scores = list(scores[0])

        if return_score:
            return results, scores
        else:
            return results

    def _batch_search(self, query, num: int = None, return_score=False):
        if self.backend == "bm25s":
            query_tokens = self.tokenizer.tokenize(query, return_as="tuple", update_vocab=False)
            results, scores = self.searcher.retrieve(query_tokens, k=num)
        else:
            assert False, "Invalid bm25 backend!"
        results = results.tolist() if isinstance(results, np.ndarray) else results
        scores = scores.tolist() if isinstance(scores, np.ndarray) else scores
        if return_score:
            return results, scores
        else:
            return results


class DenseRetriever(BaseTextRetriever):
    r"""Dense retriever based on pre-built faiss index."""

    def __init__(self, config: dict, corpus=None):
        super().__init__(config)

        self.load_corpus(corpus)
        self.load_index()
        self.load_model()

    def load_corpus(self, corpus):
        if corpus is None:
            self.corpus = load_corpus(self.corpus_path)
        else:
            self.corpus = corpus

    def load_index(self):
        if self.index_path is None or not os.path.exists(self.index_path):
            raise Warning(f"Index file {self.index_path} does not exist!")
        self.index = faiss.read_index(self.index_path)
        if self.use_faiss_gpu:
            co = faiss.GpuMultipleClonerOptions()
            co.useFloat16 = True
            co.shard = True
            self.index = faiss.index_cpu_to_all_gpus(self.index, co=co)

    def update_additional_setting(self):
        self.query_max_length = self._config["retrieval_query_max_length"]
        self.pooling_method = self._config["retrieval_pooling_method"]
        self.use_fp16 = self._config["retrieval_use_fp16"]
        self.batch_size = self._config["retrieval_batch_size"]
        self.instruction = self._config["instruction"]

        self.retrieval_model_path = self._config["retrieval_model_path"]
        self.use_st = self._config["use_sentence_transformer"]
        self.use_faiss_gpu = self._config["faiss_gpu"]

    def load_model(self):
        if self.use_st:
            self.encoder = STEncoder(
                model_name=self.retrieval_method,
                model_path=self._config["retrieval_model_path"],
                max_length=self.query_max_length,
                use_fp16=self.use_fp16,
                instruction=self.instruction,
                silent=self.silent,
            )
        else:
            # check pooling method
            self._check_pooling_method(self.retrieval_model_path, self.pooling_method)
            self.encoder = Encoder(
                model_name=self.retrieval_method,
                model_path=self.retrieval_model_path,
                pooling_method=self.pooling_method,
                max_length=self.query_max_length,
                use_fp16=self.use_fp16,
                instruction=self.instruction,
            )

    def _check_pooling_method(self, model_path, pooling_method):
        try:
            # read pooling method from 1_Pooling/config.json
            pooling_config = json.load(open(os.path.join(model_path, "1_Pooling/config.json")))
            for k, v in pooling_config.items():
                if k.startswith("pooling_mode") and v == True:
                    detect_pooling_method = k.split("pooling_mode_")[-1]
                    if detect_pooling_method == "mean_tokens":
                        detect_pooling_method = "mean"
                    elif detect_pooling_method == "cls_token":
                        detect_pooling_method = "cls"
                    else:
                        # raise warning: not implemented pooling method
                        warnings.warn(
                            f"Pooling method {detect_pooling_method} is not implemented.", UserWarning
                        )
                        detect_pooling_method = "mean"
                    break
        except:
            detect_pooling_method = None

        if detect_pooling_method is not None and detect_pooling_method != pooling_method:
            warnings.warn(
                f"Pooling method in model config file is {detect_pooling_method}, but the input is {pooling_method}. Please check carefully."
            )

    def _search(self, query: str, num: int = None, return_score=False):
        if num is None:
            num = self.topk
        query_emb = self.encoder.encode(query)
        scores, idxs = self.index.search(query_emb, k=num)
        scores = scores.tolist()
        idxs = idxs[0]
        scores = scores[0]

        results = load_docs(self.corpus, idxs)
        if return_score:
            return results, scores
        else:
            return results

    def _batch_search(self, query: list[str], num: int = None, return_score=False):
        if isinstance(query, str):
            query = [query]
        if num is None:
            num = self.topk
        batch_size = self.batch_size

        results = []
        scores = []
        emb = self.encoder.encode(query, batch_size=batch_size, is_query=True)
        scores, idxs = self.index.search(emb, k=num)
        scores = scores.tolist()
        idxs = idxs.tolist()

        flat_idxs = sum(idxs, [])
        results = load_docs(self.corpus, flat_idxs)
        results = [results[i * num : (i + 1) * num] for i in range(len(idxs))]

        if return_score:
            return results, scores
        else:
            return results


def get_retriever(config):
    r"""Automatically select retriever class based on config's retrieval method

    Args:
        config (dict): configuration with 'retrieval_method' key

    Returns:
        Retriever: retriever instance
    """

    if config["retrieval_method"] == "bm25":
        return BM25Retriever(config)
    else:
        return DenseRetriever(config)
