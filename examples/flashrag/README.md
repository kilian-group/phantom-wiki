# FlashRAG

Setup instructions:

```bash
git clone https://github.com/RUC-NLPIR/FlashRAG.git
cd FlashRAG
pip install -e .
```

Install dependencies:

> \[!TIP\]
> Pyserini relies on Java. To update Java version, run `conda install -c conda-forge openjdk=21`.

```bash
pip install pyserini
```

## Results

References:
- https://github.com/RUC-NLPIR/FlashRAG/blob/main/docs/original_docs/reproduce_experiment.md
- https://github.com/RUC-NLPIR/FlashRAG/blob/main/docs/original_docs/introduction_for_beginners_en.md

### Instructions to run IRCoT on PhantomWiki

1. Save corpus and QA pairs as .jsonl files:

```bash
python save_as_jsonl.py --split_list depth_20_size_50_seed_1
```
NOTE: this will save the corpus to `indexes/depth_20_size_50_seed_1.jsonl` and the QA pairs to `dataset/phantom-wiki-v1/depth_20_size_50_seed_1.jsonl`.

2. Build index with BM25s:

Upgrade bm25s: `pip install bm25s --upgrade`

```bash
python -m flashrag.retriever.index_builder --retrieval_method bm25 --corpus_path indexes/depth_20_size_50_seed_1.jsonl --bm25_backend bm25s
```

NOTE (Chao): curently pyserini backend does not work
```bash
python -m flashrag.retriever.index_builder --retrieval_method bm25 --corpus_path indexes/depth_20_size_50_seed_1.jsonl --bm25_backend pyserini --save_dir indexes/
```
