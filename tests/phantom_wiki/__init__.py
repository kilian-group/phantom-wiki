
import sys; print('\n'.join(sys.path))
from importlib.resources import files

ARTICLE_EXAMPLE_PATH = files("tests").joinpath("phantom_wiki/Adele Ervin.txt")