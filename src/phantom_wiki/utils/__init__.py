from termcolor import colored
# 
# Colorful print
# See possible colors here: https://pypi.org/project/termcolor/
# 
def red(text):
    print(colored(text, 'red'))
def blue(text):
    print(colored(text, 'blue'))
def green(text):
    print(colored(text, 'green'))
def yellow(text):
    print(colored(text, 'yellow'))
def cyan(text):
    print(colored(text, 'cyan'))

import uuid
def generate_unique_id():
    return str(uuid.uuid4())