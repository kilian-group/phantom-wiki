# FlashRAG

Follow the setup instructions at https://github.com/kilian-group/phantom-wiki?tab=readme-ov-file#-evaluating-llms-on-phantomwiki.

> \[!NOTE\]
> FlashRAG doesn't install the right version of bm25s, so manually upgrade it by running `pip install bm25s --upgrade`.

## Results

1. Save the corpus in the format that FlashRAG expects:

```bash
python save_as_jsonl.py --dataset kilian-group/phantom-wiki-v1 --split_list depth_20_size_$size_seed_$seed
```

> \[!NOTE\]
> If using local dataset, add the `--from_local` flag.

2. Build bm25 index

```bash
python -m flashrag.retriever.index_builder \
    --retrieval_method bm25 \
    --corpus_path indexes/depth_20_size_$size_seed_$seed.jsonl \
    --bm25_backend bm25s \
    --save_dir indexes/depth_20_size_$size_seed_$seed
```

3. Run IRCoT and Self-Ask:

To run Self-Ask:

```bash
python run_selfask.py --split SPLIT --model_name MODEL_NAME --output_dir OUTPUT_DIR
```

To run IRCoT:

```bash
python pred.py --dataset kilian-group/phantom-wiki-v1 --split_list depth_20_size_50_seed_1 -od out-XXXX --model_name meta-llama/llama-3.3-70b-instruct --method ircot
```
