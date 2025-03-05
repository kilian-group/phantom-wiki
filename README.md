# PhantomWiki

PhantomWiki generates on-demand datasets to evaluate reasoning and retrieval capabilities of LLMs.

- [Website](/todo)
- [Paper](/todo)
- [Demo](/demo.ipynb)

For convenience, we pre-generate PhantomWiki instances of size 50, 500, and 5000 with seeds 1,2,3. These can be downloaded using HuggingFace:

```python
from datasets import load_dataset

# Download the document corpus
ds_corpus = load_dataset("kilian-group/phantom-wiki-v1", "text-corpus")
# Download the question-answer pairs
ds_qa = load_dataset("kilian-group/phantom-wiki-v1", "question-answer")
```

## Using PhantomWiki

PhantomWiki is available with Python 3.12+ through

```bash
pip install phantom-wiki
```

To build from source, you can clone this repository and run `pip install .`.

Then generate datasets of varying sizes with:

```bash
./data/generate-v05.sh /path/to/output/ 1 --use-multithreading
```

**NOTE:** We do not support `--use-multithreading` on macOS yet.

This generation script creates PhantomWiki datasets with random generation seed 1:

- Universe sizes 25, 50, 500, ..., 5K, 500K, 1M (number of documents)
- Question template depth 20 (proportional to difficulty)

For example, it executes the following command to generate a size 5K universe (`5000 = --max-tree-size * --num-samples`):

```bash
python -m phantom_wiki \
   -od /path/to/output/depth_20_size_5000_seed_1 \
   -s 1 \
   --depth 20 \
   --num-samples 100 \
   --max-tree-size 50 \
   --max-tree-depth 20 \
   --article-format json \
   --question-format json \
   --hard-mode \
   --valid-only \
   --use-multithreading
```

## Installation

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

## Evaluating LLMs on PhantomWiki

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

🧪 To generate the prediction files, run the following scripts (e.g., using slurm) from the root directory:

```bash
python -m phantom_eval --method METHOD --model_name MODEL_NAME --split_list SPLIT_LIST -od OUTPUT_DIRECTORY
```

> \[!TIP\]
> To generate a slurm script with the appropriate GPU allocation and inference config, run the [create_eval.sh](./eval/create_eval.sh) script and follow the prompted steps.

📊 To generate the tables and figures, run the following script from the root directory:

```
# make sure the dataset conda env is activated!
./eval/icml.sh OUTPUT_DIRECTORY METHOD
```

where OUTPUT_DIRECTORY and METHOD are the same as when generating the predictions. This script will create the following subdirectories in OUTPUT_DIRECTORY: `scores/` and `figures/`.

## Development best practices

**Git:**

Use [pre-commit](https://pre-commit.com/) for automatic code formatting.
You can install the git hook that automatically runs pre-commit on every commit.

```bash
pip install phantom-wiki[dev] # or pip install -e .[dev]
pre-commit install
```

To run pre-commit manually:

```bash
git add <files that you want to stage>
pre-commit run
# at this point, you might need to fix any issues raised by pre-commit and restage your modified files
git commit -m "your commit message"
git push
```

**Testing:**

Run `pytest` to run tests:

```bash
pip install phantom-wiki[tests] # or pip install -e .[tests]
pytest
```

Alternatively, you can use `pytest` through your editor's (like VSCode) testing extension.
Accordingly specify your python environment and interpreter.

**Sharing results:**

- Model predictions can be shared at `/share/nikola/phantom-wiki/eval/`
- Please copy the predictions to your local working directory rather than reading from the shared directory directly

## Sharing dataset to HuggingFace

Use the huggingface cli (see https://huggingface.co/docs/datasets/en/share#upload-an-entire-folder):

```bash
huggingface-cli upload mlcore/phantom-wiki-v<version> OUTPUT_DIRECTORY . --repo-type dataset --commit-message="optional commit message"
```

## Citation

TODO with arxiv link

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
