# FlashRAG

Setup instructions:

```bash
git clone https://github.com/RUC-NLPIR/FlashRAG.git
cd FlashRAG
pip install -e .
pip install bm25s --upgrade
```

<!-- Install dependencies:

> \[!TIP\]
> Pyserini relies on Java. To update Java version, run `conda install -c conda-forge openjdk=21`.

```bash
pip install pyserini
``` -->

## Results

References:
- https://github.com/RUC-NLPIR/FlashRAG/blob/main/docs/original_docs/reproduce_experiment.md
- https://github.com/RUC-NLPIR/FlashRAG/blob/main/docs/original_docs/introduction_for_beginners_en.md

```bash
python pred.py --dataset kilian-group/phantom-wiki-v1 --split_list depth_20_size_50_seed_1 -od out-XXXX --model_name meta-llama/llama-3.3-70b-instruct --method ircot
```
