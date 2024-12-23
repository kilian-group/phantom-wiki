# Phantom Wiki

> \[!CAUTION\]
> This is a **work-in-progress** project on automatic language model dataset generation.
>
> Use at your own risk.

## Setup

Set up a virtual environment, clone and navigate to this repository, and run

```bash
conda create -n dataset
conda activate dataset
conda install python=3.12 conda-forge::faker anaconda::sqlalchemy anaconda::nltk anaconda::termcolor pydot pytest
# on G2, use pip instead of conda to install pandas and numpy to avoid C dependency conflicts
pip install pandas numpy
pip install together openai pre-commit datasets google-generativeai anthropic transformers tenacity tiktoken vllm langchain
```

### Installing phantom-wiki in development mode

There are 2 options:
1. (Recommended) Install the package in editable mode using pip:
    ```bash
    pip install -e .
    ```

2. If you use VSCode, you can add to the python path without installing the package:
    1. Create a file in the repo root called `.env`
    2. Add `PYTHONPATH=src`
    3. Restart VSCode

### Prolog

Setting up Prolog (see also the [Prolog tutorial](docs/prolog.md)):

```bash
# install SWI-Prolog (on Mac)
brew install swi-prolog
# TODO: install SWI-Prolog (on Windows)
# install Python wrapper for Prolog
pip install pyswip
```

## Evaluation

Run evaluation methods (like `zeroshot,fewshot,react,...`) with an LLM like so:
```bash
python -m phantom_eval --method <method> --model_name <llm_name>
```

**Steps for reproducing all results:**

🧪 To generate the prediction files, run the following scripts (e.g., using slurm):
```
conda activate dataset
# run small models (< 4B params) locally (allocates 1 3090)
sbatch eval/zeroshot_S.sh <output directory>
# run medium models (< 10B params) locally (allocates 4 A6000s)
sbatch eval/zeroshot_M.sh <output directory>
# run large models (10-70B params) locally (allocates 8 A6000s)
sbatch eval/zeroshot_L.sh <output directory>
# run API models (NOTE: this can be very expensive!)
sbatch eval/zeroshot_cpu.sh <output directory> <model name>
```
📊 To generate the tables and figures, run the following script:
```
# make sure the dataset conda env is activated!
./eval/evaluate.sh <output directory> <method>
```
where <output directory> here is the same as <output directory> when generating the prediction and <method> cam be zeroshot/react/etc.

NOTE: this script will save the outputs to OUTPUT_DIRECTORY under `scores/` and `figures/`

TODO: make the folder naming structure more consistent

Run `python -m phantom_eval -h` for usage help and a list of supported models.
Below are setup instructions for various LLM providers supported in evaluation.

### TogetherAI

1. Register for an account at https://api.together.ai
2. Set your TogetherAI API key:

```
conda env config vars set TOGETHER_API_KEY=xxxxx
```

### OpenAI
1. Register an account *with your cornell.edu email* at https://platform.openai.com/ and join "Kilian's Group"
2. Create an API key at https://platform.openai.com/settings/organization/api-keys under your name
3. Set your OpenAI API key in your conda environment:
```
conda env config vars set OPENAI_API_KEY=xxxxx
```
Rate limits: https://platform.openai.com/docs/guides/rate-limits#usage-tiers

### Google Gemini
1. Create an API key at https://aistudio.google.com/app/apikey (NOTE: for some reason, Google AI Studio is disabled for cornell.edu accounts, so use your personal account)
2. Set your Google API key:
```
conda env config vars set GOOGLE_API_KEY=xxxxx
```

### Anthropic
1. Register an account *with your cornell.edu email* and join "Kilian's Group" 
2. Create an API key at https://console.anthropic.com/settings/keys under your name
3. Set your Anthropic API key in your conda environment:
```
conda env config vars set ANTHROPIC_API_KEY=xxxxx
```
Rate limits: https://docs.anthropic.com/en/api/rate-limits#updated-rate-limits

:rotating_light: The Anthropic API has particularly low rate limits so it takes longer to get predictions.

### vLLM
Setup (following [these](https://docs.vllm.ai/en/stable/getting_started/installation.html) instructions):
```
# allocate an GPU with CUDA 12.2 (if you have Xiangyu's graphite-utils, you can do `cuda121` in zsh)
conda activate dataset
pip install vllm
```
NOTE: almost all models on HF are fair game (see also: https://docs.vllm.ai/en/stable/models/supported_models.html#supported-models)

**System requirements**
- `meta-llama/Llama-3.1-8B-Instruct`: >= one 3090
- `meta-llama/Llama-3.1-70B-Instruct`: 
   - `max_model_len = 4096` requires >= four A6000s
   - `max_model_len = None` requires >= eight A6000s
With four A6000s:
```
[rank0]: ValueError: The model's max seq len (131072) is larger than the maximum number of tokens that can be stored in KV cache (106848). Try increasing `gpu_memory_utilization` or decreasing `max_model_len` when initializing the engine.
```
With six A6000s:
```
ValueError: Total number of attention heads (64) must be divisible by tensor parallel size (6).
```
NOTE: These models and their configs are downloaded directly from HuggingFace

## Development best practices

**Git:**

```
git add <files that you want to stage>
pre-commit run
# at this point, you might need to fix any issues raised by pre-commit and restage your modified files
git commit -m "your commit message"
git push
```

**Testing:**

1. If prompted, select `pytest` as the testing framework for the VSCode Testing Extension
2. To run the tests, there are two methods:
   - Run from the Testing Extension (note: your python interpreter must be set to the `dataset` conda environment created above)
   - Call `pytest` in the terminal (note: make sure the `dataset` conda environment is activated)

## Sharing dataset to HuggingFace

1. Clone the HuggingFace dataset repo (note: you only need to do this once):

```
cd <some location outside of this repo>
pip install -U "huggingface_hub[cli]"
huggingface-cli login
# NOTE: when creating a new access token, set the token type to be `write`
git clone https://huggingface.co/datasets/mlcore/phantom-wiki
git lfs install
```

2. Generate a new dataset and save to the location of the huggingface repo

```
python -m phantom_wiki -op <path to huggingface repo> --article_format json --question_format json --valid_only -s <global seed>
```

3. Push the files to the huggingface repo:

```
git add .
git commit -m "some message"
git push
```
