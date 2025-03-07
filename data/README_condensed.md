---
language:
  - en
license: mit
size_categories:
  - 1M<n<10M
task_categories:
  - question-answering
tags:
  - reasoning
  - retrieval
  - synthetic
  - evaluation
dataset_info:
  - config_name: database
    features:
      - name: content
        dtype: string
    splits:
      - name: depth_20_size_50_seed_1
        num_bytes: 25163
        num_examples: 1
      - name: depth_20_size_50_seed_2
        num_bytes: 25205
        num_examples: 1
      - name: depth_20_size_50_seed_3
        num_bytes: 25015
        num_examples: 1
      - name: depth_20_size_500_seed_1
        num_bytes: 191003
        num_examples: 1
      - name: depth_20_size_500_seed_2
        num_bytes: 190407
        num_examples: 1
      - name: depth_20_size_500_seed_3
        num_bytes: 189702
        num_examples: 1
      - name: depth_20_size_5000_seed_1
        num_bytes: 1847718
        num_examples: 1
      - name: depth_20_size_5000_seed_2
        num_bytes: 1845391
        num_examples: 1
      - name: depth_20_size_5000_seed_3
        num_bytes: 1846249
        num_examples: 1
    download_size: 1965619
    dataset_size: 6185853
  - config_name: question-answer
    features:
      - name: id
        dtype: string
      - name: question
        dtype: string
      - name: intermediate_answers
        dtype: string
      - name: answer
        sequence: string
      - name: prolog
        struct:
          - name: query
            sequence: string
          - name: answer
            dtype: string
      - name: template
        sequence: string
      - name: type
        dtype: int64
      - name: difficulty
        dtype: int64
    splits:
      - name: depth_20_size_50_seed_1
        num_bytes: 299562
        num_examples: 500
      - name: depth_20_size_50_seed_2
        num_bytes: 303664
        num_examples: 500
      - name: depth_20_size_50_seed_3
        num_bytes: 293959
        num_examples: 500
      - name: depth_20_size_500_seed_1
        num_bytes: 308562
        num_examples: 500
      - name: depth_20_size_500_seed_2
        num_bytes: 322956
        num_examples: 500
      - name: depth_20_size_500_seed_3
        num_bytes: 300467
        num_examples: 500
      - name: depth_20_size_5000_seed_1
        num_bytes: 338703
        num_examples: 500
      - name: depth_20_size_5000_seed_2
        num_bytes: 344577
        num_examples: 500
      - name: depth_20_size_5000_seed_3
        num_bytes: 320320
        num_examples: 500
    download_size: 689443
    dataset_size: 2832770
  - config_name: text-corpus
    features:
      - name: title
        dtype: string
      - name: article
        dtype: string
      - name: facts
        sequence: string
    splits:
      - name: depth_20_size_50_seed_1
        num_bytes: 25754
        num_examples: 51
      - name: depth_20_size_50_seed_2
        num_bytes: 26117
        num_examples: 50
      - name: depth_20_size_50_seed_3
        num_bytes: 25637
        num_examples: 51
      - name: depth_20_size_500_seed_1
        num_bytes: 262029
        num_examples: 503
      - name: depth_20_size_500_seed_2
        num_bytes: 260305
        num_examples: 503
      - name: depth_20_size_500_seed_3
        num_bytes: 259662
        num_examples: 504
      - name: depth_20_size_5000_seed_1
        num_bytes: 2614872
        num_examples: 5030
      - name: depth_20_size_5000_seed_2
        num_bytes: 2608826
        num_examples: 5029
      - name: depth_20_size_5000_seed_3
        num_bytes: 2609449
        num_examples: 5039
    download_size: 2851789
    dataset_size: 8692651
configs:
  - config_name: database
    data_files:
      - split: depth_20_size_50_seed_1
        path: database/depth_20_size_50_seed_1-*
      - split: depth_20_size_50_seed_2
        path: database/depth_20_size_50_seed_2-*
      - split: depth_20_size_50_seed_3
        path: database/depth_20_size_50_seed_3-*
      - split: depth_20_size_500_seed_1
        path: database/depth_20_size_500_seed_1-*
      - split: depth_20_size_500_seed_2
        path: database/depth_20_size_500_seed_2-*
      - split: depth_20_size_500_seed_3
        path: database/depth_20_size_500_seed_3-*
      - split: depth_20_size_5000_seed_1
        path: database/depth_20_size_5000_seed_1-*
      - split: depth_20_size_5000_seed_2
        path: database/depth_20_size_5000_seed_2-*
      - split: depth_20_size_5000_seed_3
        path: database/depth_20_size_5000_seed_3-*
  - config_name: question-answer
    data_files:
      - split: depth_20_size_50_seed_1
        path: question-answer/depth_20_size_50_seed_1-*
      - split: depth_20_size_50_seed_2
        path: question-answer/depth_20_size_50_seed_2-*
      - split: depth_20_size_50_seed_3
        path: question-answer/depth_20_size_50_seed_3-*
      - split: depth_20_size_500_seed_1
        path: question-answer/depth_20_size_500_seed_1-*
      - split: depth_20_size_500_seed_2
        path: question-answer/depth_20_size_500_seed_2-*
      - split: depth_20_size_500_seed_3
        path: question-answer/depth_20_size_500_seed_3-*
      - split: depth_20_size_5000_seed_1
        path: question-answer/depth_20_size_5000_seed_1-*
      - split: depth_20_size_5000_seed_2
        path: question-answer/depth_20_size_5000_seed_2-*
      - split: depth_20_size_5000_seed_3
        path: question-answer/depth_20_size_5000_seed_3-*
  - config_name: text-corpus
    data_files:
      - split: depth_20_size_50_seed_1
        path: text-corpus/depth_20_size_50_seed_1-*
      - split: depth_20_size_50_seed_2
        path: text-corpus/depth_20_size_50_seed_2-*
      - split: depth_20_size_50_seed_3
        path: text-corpus/depth_20_size_50_seed_3-*
      - split: depth_20_size_500_seed_1
        path: text-corpus/depth_20_size_500_seed_1-*
      - split: depth_20_size_500_seed_2
        path: text-corpus/depth_20_size_500_seed_2-*
      - split: depth_20_size_500_seed_3
        path: text-corpus/depth_20_size_500_seed_3-*
      - split: depth_20_size_5000_seed_1
        path: text-corpus/depth_20_size_5000_seed_1-*
      - split: depth_20_size_5000_seed_2
        path: text-corpus/depth_20_size_5000_seed_2-*
      - split: depth_20_size_5000_seed_3
        path: text-corpus/depth_20_size_5000_seed_3-*
---

# Dataset Card for PhantomWiki

This repository contains pre-generated instances of the PhantomWiki dataset, created using the `phantom-wiki` Python package.  PhantomWiki is a framework for evaluating LLMs, particularly RAG and agentic workflows, designed to be resistant to memorization. Unlike fixed datasets, PhantomWiki generates unique instances on demand, ensuring novelty and preventing data leakage.

## Dataset Details

### Dataset Description

PhantomWiki generates a synthetic fictional universe populated with characters and facts, mirroring the structure of a fan wiki.  These facts are reflected in a large-scale corpus, and diverse question-answer pairs of varying difficulties are then generated.

- **Created by:** Albert Gong, Kamilė Stankevičiūtė, Chao Wan, Anmol Kabra, Raphael Thesmar, Johann Lee, Julius Klenke, Carla P. Gomes, Kilian Q. Weinberger
- **Funded by:**  See the [paper](https://huggingface.co/papers/2502.20377) for details.
- **License:** MIT License
- **Paper:** [PhantomWiki: On-Demand Datasets for Reasoning and Retrieval Evaluation](https://huggingface.co/papers/2502.20377)
- **Code:** [https://github.com/kilian-group/phantom-wiki](https://github.com/kilian-group/phantom-wiki)

### Dataset Sources

- **Repository (Code):** [https://github.com/kilian-group/phantom-wiki](https://github.com/kilian-group/phantom-wiki)

## Uses

PhantomWiki is designed to evaluate retrieval augmented generation (RAG) systems and agentic workflows.  To avoid data leakage and overfitting, generate a new, unique PhantomWiki instance for each evaluation.  Our paper details an analysis of frontier LLMs using PhantomWiki.

### Dataset Structure

PhantomWiki provides three configurations:

1. `question-answer`: Question-answer pairs generated using a context-free grammar
2. `text-corpus`: Documents generated using natural-language templates
3. `database`: Prolog database containing the facts and clauses representing the universe

Each universe is saved as a separate split.  See the original repository for details on generation and usage.

## Bias, Risks, and Limitations

PhantomWiki, while effective at evaluating complex reasoning and retrieval, is limited in its representation of family relations and attributes.  Extending its complexity is a future research direction.  For a holistic evaluation, combine PhantomWiki with other benchmarks.

## Citation

```bibtex
@article{2025_phantomwiki,
  title={{PhantomWiki: On-Demand Datasets for Reasoning and Retrieval Evaluation}},
  author={Albert Gong and Kamilė Stankevičiūtė and Chao Wan and Anmol Kabra and Raphael Thesmar and Johann Lee and Julius Klenke and Carla P. Gomes and Kilian Q. Weinberger},
  year={2025},
  journal={todo},
  url={todo},
  note={Under Review},
}
```
