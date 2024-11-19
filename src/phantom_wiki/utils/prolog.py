import re

from nltk import CFG

from ..facts.templates import QA_GRAMMAR_STRING, generate_templates


def print_question_templates(grammar_string=QA_GRAMMAR_STRING, depth=6):
    grammar = CFG.fromstring(grammar_string)
    questions = generate_templates(grammar, depth=depth)
    total_questions = 0
    for question, query, answer in questions:
        total_questions += 1
        print("Question:\t" + question)
        print("Query:\t\t" + query)
        print("Answer:\t\t" + answer)
        print()
    print(f"Total questions (depth {depth}):\t{total_questions}")


def parse_prolog_predicate(line: str) -> tuple[str, list[str]]:
    """
    Parses a Prolog predicate.

    Examples:
        female(vanessa). -> ('female', ['vanessa', 'albert'])
        parent(anastasia, sarah). -> ('parent', ['anastasia', 'sarah'])

    Args:
        line (str): predicate(arg1, arg2, ..., argn).
    Returns:
        (predicate, [arg1, arg2, ..., argn])
    """
    pattern = r"^([a-z]+)\((.*)\)\.$"
    match = re.search(pattern, line)
    return match.group(1), [s.strip() for s in match.group(2).split(",")]


def parse_prolog_predicate_definition(line):
    """
    parses a Prolog predicate
    Examples:
        female(vanessa). -> ('female', ['vanessa', 'albert'])
        parent(anastasia, sarah). -> ('parent', ['anastasia', 'sarah'])

    Args:
        line (str): predicate(arg1, arg2, ..., argn).
    Returns:
        (predicate, [arg1, arg2, ..., argn])
    """
    pattern = r"^([a-zA-Z_]+)\((.*)\) :-\n$"
    match = re.search(pattern, line)
    return match.group(1), [s.strip() for s in match.group(2).split(",")]
