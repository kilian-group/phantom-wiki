# PhantomWiki

PhantomWiki generates on-demand datasets to evaluate reasoning and retrieval capabilities of LLMs.

- [Paper](https://arxiv.org/abs/2502.20377)
- [Demo](/demo.ipynb)

## Contents

- [🚀 Quickstart](#-quickstart)
  - [Pre-generated PhantomWiki datasets on Huggingface](#pre-generated-phantomwiki-datasets-on-huggingface)
- [🔗 Installing dependencies](#-installing-dependencies)
  - [Installing PhantomWiki in development mode](#installing-phantomwiki-in-development-mode)
- [🔢 Evaluating LLMs on PhantomWiki](#-evaluating-llms-on-phantomwiki)
  - [Setting up API keys](#setting-up-api-keys)
  - [Reproducing LLM evaluation results in the paper](#reproducing-llm-evaluation-results-in-the-paper)
- [📃 Citation](#-citation)

## 🚀 Quickstart

First [install Prolog](#installation) on your machine, then PhantomWiki with `pip`:

```bash
pip install phantom-wiki
```

> \[!NOTE\]
> This package has been tested with Python 3.12. We require Python 3.10+ to support match statements.

To build from source, you can clone this repository and run `pip install .`.

Generate PhantomWiki datasets with random generation seed 1:

1. In Python:

```python
import phantom_wiki as pw

pw.generate_dataset(
    output_dir="/path/to/output",
    seed=1,
    use_multithreading=True,
)
```

2. In a terminal:

```bash
phantom-wiki-generate -od "/path/to/output" --seed 1 --use-multithreading
```

(You can also use the shorthand alias `pw-generate`.)

> \[!NOTE\]
> We do not support `--use-multithreading` on macOS yet, so you should skip this flag (or set it to `False`).

The following generation script creates datasets of various sizes with random generation seed 1:

```bash
./data/generate-v1.sh /path/to/output/ 1 --use-multithreading
```

- Universe sizes 25, 50, 500, ..., 5K, 500K, 1M (number of documents)
- Question template depth 20 (proportional to difficulty)

For example, it executes the following command to generate a size 5K universe (`5000 = --max-family-tree-size * --num-family-trees`):

```bash
pw-generate \
   -od /path/to/output/depth_20_size_5000_seed_1 \
   --seed 1 \
   --question-depth 20 \
   --num-family-trees 100 \
   --max-family-tree-size 50 \
   --max-family-tree-depth 20 \
   --article-format json \
   --question-format json \
   --use-multithreading
```

### Pre-generated PhantomWiki datasets on Huggingface

For convenience of development, we provide pre-generated PhantomWiki datasets on HuggingFace (sizes 50, 500, and 5000 with seeds 1, 2, and 3).

```python
from datasets import load_dataset

# Download the document corpus
ds_corpus = load_dataset("kilian-group/phantom-wiki-v1", "text-corpus")
# Download the question-answer pairs
ds_qa = load_dataset("kilian-group/phantom-wiki-v1", "question-answer")
```

## 🔗 Installing dependencies

PhantomWiki uses the [Prolog](https://en.wikipedia.org/wiki/Prolog) logic programming language, available on all operating systems through [SWI-Prolog](https://www.swi-prolog.org/).
We recommend installing SWI-prolog through your [distribution](https://www.swi-prolog.org/Download.html) or through conda, for example:

```bash
# On macOS: with homebrew
brew install swi-prolog

# On Linux: with apt
sudo add-apt-repository ppa:swi-prolog/stable
sudo apt-get update
sudo apt-get install swi-prolog

# On Linux: with conda
conda install conda-forge::swi-prolog

# On Windows: download and install binary from https://www.swi-prolog.org/download/stable
```

### Installing PhantomWiki in development mode

There are 2 options:

1. (Recommended) Install the package in editable mode using pip:

   ```bash
   pip install -e .
   ```

2. If you use VSCode, you can add to the python path without installing the package:

   1. Create a file in the repo root called `.env`
   2. Add `PYTHONPATH=src`
   3. Restart VSCode

## 🔢 Evaluating LLMs on PhantomWiki

First, install dependencies and [vLLM](https://github.com/vllm-project/vllm) to match your hardware (GPU, CPU, etc.):

```bash
pip install phantom-wiki[eval]
pip install "vllm>=0.6.6"
```

If you're installing from source, use `pip install -e ".[eval]"`.

### Setting up API keys

<details>
<summary>Anthropic</summary>

1. Register an account *with your cornell.edu email* and join "Kilian's Group"
2. Create an API key at https://console.anthropic.com/settings/keys under your name
3. Set your Anthropic API key in your conda environment:

```bash
conda env config vars set ANTHROPIC_API_KEY=xxxxx
```

Rate limits: https://docs.anthropic.com/en/api/rate-limits#updated-rate-limits

:rotating_light: The Anthropic API has particularly low rate limits so it takes longer to get predictions.

</details>

<details>
<summary>Google Gemini</summary>

1. Create an API key at https://aistudio.google.com/app/apikey (NOTE: for some reason, Google AI Studio is disabled for cornell.edu accounts, so use your personal account)
2. Set your Gemini API key:

```bash
conda env config vars set GEMINI_API_KEY=xxxxx
```

</details>

<details>
<summary>OpenAI</summary>

1. Register an account *with your cornell.edu email* at https://platform.openai.com/ and join "Kilian's Group"
2. Create an API key at https://platform.openai.com/settings/organization/api-keys under your name
3. Set your OpenAI API key in your conda environment:

```bash
conda env config vars set OPENAI_API_KEY=xxxxx
```

Rate limits: https://platform.openai.com/docs/guides/rate-limits#usage-tiers

</details>

<details>
<summary>TogetherAI</summary>

1. Register for an account at https://api.together.ai
2. Set your TogetherAI API key:

```bash
conda env config vars set TOGETHER_API_KEY=xxxxx
```

</details>

<details>
<summary>vLLM</summary>

Original setup instructions: https://docs.vllm.ai/en/stable/getting_started/installation.html#install-the-latest-code

Additional notes:

- It's recommended to download the model manually:

```bash
huggingface-cli download MODEL_REPO_ID
```

- The models and their configs are downloaded directly from HuggingFace and almost all models on HF are fair game (see also: https://docs.vllm.ai/en/stable/models/supported_models.html#supported-models)
- Total number of attention heads must be divisible by tensor parallel size
- See minimum GPU requirements for [small](eval/zeroshot_S.sh), [medium](eval/zeroshot_M.sh), and [large](eval/zeroshot_L.sh) models at the top of each eval inference script
- Running the same code on the same GPU indeed gives perfectly reproducible outputs, but running the same code on different GPUs (e.g., 3090 vs A6000) doesn't necessarily lead to the same results (see: https://github.com/albertgong1/phantom-wiki/pull/79#issuecomment-2559001925).

</details>

### Reproducing LLM evaluation results in the paper

> \[!NOTE\]
> For vLLM inference, make sure to request access for Gemma, Llama 3.1, 3.2, and 3.3 models on HuggingFace before proceeding.

🧪 To generate the predictions, run the following command from the root directory:

```bash
python -m phantom_eval --method METHOD --model_name MODEL_NAME --split_list SPLIT_LIST -od OUTPUT_DIRECTORY
```

> \[!TIP\]
> To generate a slurm script with the appropriate GPU allocation and inference config, run the [create_eval.sh](./eval/create_eval.sh) script and follow the prompted steps.

📊 To generate the tables and figures, run the following command from the root directory:

```bash
./eval/icml.sh OUTPUT_DIRECTORY METHOD
```

where OUTPUT_DIRECTORY and METHOD are the same as when generating the predictions. This script will create the following subdirectories in OUTPUT_DIRECTORY: `scores/` and `figures/`.

## 📃 Citation

```bibtex
@article{gong2025phantomwiki,
  title={{PhantomWiki}: On-Demand Datasets for Reasoning and Retrieval Evaluation},
  author={Gong, Albert and Stankevi{\v{c}}i{\=u}t{\.e}, Kamil{\.e} and Wan, Chao and Kabra, Anmol and Thesmar, Raphael and Lee, Johann and Klenke, Julius and Gomes, Carla P and Weinberger, Kilian Q},
  journal={arXiv preprint arXiv:2502.20377},
  year={2025}
}
```
