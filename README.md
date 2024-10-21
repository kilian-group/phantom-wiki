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
pip install pydatalog
# install SWI-Prolog
brew install swi-prolog
# install Janus-SWI (Python interface to SWI-Prolog)
pip install janus-swi
```
<!-- pip install -e . -->
<!-- to install the dependencies and command line scripts. -->
