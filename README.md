# Phantom Wiki

> [!CAUTION]
> This is a **work-in-progress** project on automatic language model dataset generation.
> 
> Use at your own risk.

## Setup

Set up a virtual environment, clone and navigate to this repository, and run 
```
conda create -n dataset
conda activate dataset
conda install python=3.10 pandas numpy conda-forge::faker anaconda::sqlalchemy anaconda::nltk
pip install together openai
pip install pydatalog
# install SWI-Prolog (on Mac)
brew install swi-prolog
# TODO: install SWI-Prolog (on Windows)
# install Janus-SWI (Python interface to SWI-Prolog)
pip install janus-swi
```
<!-- pip install -e . -->
<!-- to install the dependencies and command line scripts. -->

# TogetherAI

1. Register for an account at https://api.together.ai
2. Set your TogetherAI API key:
```
conda env config vars set TOGETHER_API_KEY=xxxxx
```