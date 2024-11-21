# Phantom Wiki

> \[!CAUTION\]
> This is a **work-in-progress** project on automatic language model dataset generation.
>
> Use at your own risk.

## Setup

Set up a virtual environment, clone and navigate to this repository, and run
```
conda create -n dataset
conda activate dataset
conda install python=3.12 pandas numpy conda-forge::faker anaconda::sqlalchemy anaconda::nltk anaconda::termcolor pydot pytest
pip install together openai pre-commit
```
Setting up Prolog (see also the [Prolog tutorial](docs/prolog.md)):
```
# install SWI-Prolog (on Mac)
brew install swi-prolog
# TODO: install SWI-Prolog (on Windows)
# install Python wrapper for Prolog
pip install pyswip
```

To install the source code in development mode:

Option 1:
```
conda activate dataset
cd src
conda develop .
```

Option 2:
1. Create a file in the repo root called `.env`
2. Add `PYTHONPATH=src`
3. Restart VSCode

## TogetherAI

1. Register for an account at https://api.together.ai
2. Set your TogetherAI API key:

```
conda env config vars set TOGETHER_API_KEY=xxxxx
```

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
hugginface-cli login
git clone https://huggingface.co/datasets/mlcore/phantom-wiki
git lfs install
```
2. Generate a new dataset and save to the location of the huggingface repo
```
python -m phantom_wiki -op <path to huggingface repo> --article_format json --question_format json
```
3. Push the files to the huggingface repo:
```
git add .
git commit -m "some message"
git push
```