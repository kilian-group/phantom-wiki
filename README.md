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
conda install python=3.12 pandas numpy conda-forge::faker anaconda::sqlalchemy anaconda::nltk anaconda::termcolor
pip install together openai
pip install pydatalog
# install SWI-Prolog (on Mac)
brew install swi-prolog
# TODO: install SWI-Prolog (on Windows)
# install Janus-SWI (Python interface to SWI-Prolog)
pip install janus-swi
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
2. Add `PYTHONPATH=<path to src>`
3. Restart VSCode

# TogetherAI

1. Register for an account at https://api.together.ai
2. Set your TogetherAI API key:

```
conda env config vars set TOGETHER_API_KEY=xxxxx
```
