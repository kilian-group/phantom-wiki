# PhantomWiki

## Installation

PhantomWiki uses the [Prolog](https://en.wikipedia.org/wiki/Prolog) logic programming language, available on all operating systems through [SWI-Prolog](https://www.swi-prolog.org/).
We recommend installing SWI-prolog through your [distribution](https://www.swi-prolog.org/Download.html) or through conda, for example:
```bash
# On MacOS
brew install swi-prolog

# On Linux with apt
sudo add-apt-repository ppa:swi-prolog/stable
sudo apt-get update
sudo apt-get install swi-prolog

# With conda package manager
conda install conda-forge::swi-prolog
```

PhantomWiki is available with Python 3.12+ through `pip install phantom-wiki`.
Alternatively, clone this github repo and run `pip install .`

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

## PhantomWiki Evaluation

First, install dependencies and [vLLM](https://github.com/vllm-project/vllm) to match your hardware (GPU, CPU, etc.):
```bash
pip install -r requirements-eval.txt
pip install "vllm>=0.6.6"
```

Then run evaluation methods (like `zeroshot,fewshot,react,...`) with an LLM like so:
```bash
python -m phantom_eval --method <method> --model_name <llm_name>
```

**Steps for reproducing all results:**

🛑 Make sure to request access for Gemma, Llama 3.1, 3.2, and 3.3 models on HuggingFace before proceeding. 

🧪 To generate the prediction files, run the following scripts (e.g., using slurm) from the root directory:
```
# Create a dir for slurm logs
mkdir slurm

conda activate dataset
# run small models (< 4B params) locally (allocates 1 3090)
sbatch eval/zeroshot_S.sh <output directory>
sbatch eval/fewshow_S.sh <output directory>
sbatch eval/cot_S.sh <output directory>
# run medium models (< 10B params) locally (allocates 2 A6000s)
sbatch eval/zeroshot_M.sh <output directory>
sbatch eval/fewshot_M.sh <output directory>
sbatch eval/cot_M.sh <output directory>
# run large models (10-70B params) locally (allocates 8 A6000s)
sbatch eval/zeroshot_L.sh <output directory>
sbatch eval/fewshow_L.sh <output directory>
sbatch eval/cot_L.sh <output directory>
# run API models (NOTE: this can be very expensive!)
sbatch eval/zeroshot_cpu.sh <output directory> <model name>
sbatch eval/cot_cpu.sh <output directory> <model name>
```
📊 To generate the tables and figures, run the following script from the root directory:
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
conda env config vars set GEMINI_API_KEY=xxxxx
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

**Sharing results:**

- Model predictions can be shared at `/share/nikola/phantom-wiki/eval`
- Please copy the predictions to your local working directory rather than reading from the shared directory directly

## Sharing dataset to HuggingFace

1. Clone the HuggingFace dataset repo (note: you only need to do this once):

```bash
cd PATH_TO_LOCAL_HF_REPO
pip install -U "huggingface_hub[cli]"
huggingface-cli login
# NOTE: when creating a new access token, set the token type to be `write`
git clone https://huggingface.co/datasets/mlcore/phantom-wiki
git lfs install
```

2. Generate a new dataset and save to the location of the huggingface repo

```bash
python -m phantom_wiki -od PATH_TO_LOCAL_HF_REPO --article-format json --question-format json --valid-only -s SEED
```

3. Push the files to the huggingface repo:

```bash
git add .
git commit -m "some message"
git push
```

Alternatively, can use the huggingface cli (see https://huggingface.co/docs/datasets/en/share#upload-an-entire-folder):
```bash
huggingface-cli upload mlcore/phantom-wiki-v<version> OUTPUT_DIRECTORY . --repo-type dataset --commit-message="optional commit message"
```
