# TODO: this is yet to be refactored.

import os

from nltk import CFG

from phantom_wiki.utils.parsing import *  # noqa: F403

# Define the CFG as a string and parse it using nltk.CFG.fromstring
# cfg_string = """
# S -> "Anastasia is a talented" Occupation "known for her" Skill "in the music world."
# Description Achievements Influence
# Occupation -> "musician" | "composer" | "violinist" | "guitarist" | "pianist" | "singer-songwriter"
# Skill -> "mastery of melodies" | "ability to captivate audiences" | "passion for composing" |
# "skill with harmonies" | "unique musical style" | "innovative approach to music" | "expressive performance"
# Description -> Genre Style
# Genre -> "She specializes in" MusicStyle "."
# MusicStyle -> "classical music" | "jazz fusion" | "indie rock" | "electronic compositions" |
# "folk tunes" | "contemporary ballads"
# Style -> "Her music is often described as" Adjective "."
# Adjective -> "ethereal and haunting" | "dynamic and intense" | "melodic and harmonious" |
#  "soulful and introspective" | "energetic and captivating"
# Achievements -> "She has released" Number AlbumType "and" Number SingleType "."
# Number -> "several" | "two" | "three" | "numerous" | "a collection of"
# AlbumType -> "albums" | "EPs" | "soundtracks"
# SingleType -> "singles" | "music videos" | "chart-topping hits"
# Influence -> "Her work has influenced" Artists "and continues to inspire" Audience "."
# Artists -> "upcoming artists in the industry" | "fellow musicians" | "many aspiring composers"
# Audience -> "listeners around the world" | "a dedicated fanbase" | "music lovers across generations"
# """


def TO_BE_REFACTORED():
    # TODO: refactor
    person = "Anastasia"
    with open(f"output/CFG/{person}_CFG.txt") as file:
        cfg_string = file.read()

    # Parse the CFG
    grammar = CFG.fromstring(cfg_string)

    # Generate the questions associated with each non-terminal
    # import pdb; pdb.set_trace()
    raw_questions = get_response(None, None, cfg_string)  # noqa: F405
    questions = parse_question_list(raw_questions)  # noqa: F405

    # Questions associated with each CFG non-terminal
    # questions = {
    #     "Occupation": "What is Anastasia's primary occupation?",
    #     "Skill": "What specific talent is Anastasia known for?",
    #     "MusicStyle": "In what genre does Anastasia specialize?",
    #     "Adjective": "How is Anastasia’s music described?",
    #     "Number (albums and singles)": "How many albums or singles has Anastasia released?",
    #     "AlbumType": "What type of music releases has she made (e.g., albums, EPs)?",
    #     "SingleType": "What other music projects has she released (e.g., singles, music videos)?",
    #     "Artists": "Who has Anastasia influenced with her work?",
    #     "Audience": "Who is inspired by Anastasia’s music?"
    # }
    # Generate Python code from parsed CFG
    def generate_code_from_parsed_cfg(grammar, questions):
        # Initialize the generated code as a list of strings for easier formatting
        code = [
            "import random\n\n",
            "import textwrap\n\n",
            "# Define possible choices for each CFG terminal\n",
        ]

        # Create a dictionary to collect production rules by their LHS
        rules = {}
        for production in grammar.productions():
            lhs = str(production.lhs())
            rhs = " ".join(str(sym) for sym in production.rhs())
            if lhs not in rules:
                rules[lhs] = []
            rules[lhs].append(rhs)

        # Generate Python lists for each non-terminal's choices
        for lhs, rhss in rules.items():
            var_name = lhs.lower() + "_choices"
            formatted_rhss = [f'"{rhs}"' if '"' not in rhs else rhs for rhs in rhss]
            code.append(f"{var_name} = [{', '.join(formatted_rhss)}]\n")

        # Add questions as a dictionary
        code.append("\n# Define questions associated with each CFG terminal\n")
        code.append("questions = {\n")
        for key, question in questions.items():
            code.append(f'    "{key}": "{question}",\n')
        code.append("}\n\n")

        # Randomly generate values for each CFG terminal
        code.append("# Randomly generate values for each CFG terminal\n")
        for lhs in rules.keys():
            var_name = lhs.lower()
            code.append(f"{var_name} = random.choice({var_name}_choices)\n")

        # Generate the article based on recursive expansion
        code.append("\n# Recursive expansion of the CFG to build the article\n")
        code.append("def expand_rule(rule):\n")
        code.append("    components = rule.split()\n")
        code.append("    expanded = []\n")
        code.append("    for component in components:\n")
        code.append("        if component.lower() in globals():\n")
        code.append("            expanded.append(expand_rule(globals()[component.lower()]))\n")
        code.append("        else:\n")
        code.append("            expanded.append(component.strip('\"'))\n")
        code.append("    return ' '.join(expanded)\n\n")

        # Build the article from the start symbol of the grammar
        start_symbol = str(grammar.start()) + "_choices"
        code.append(f"article = expand_rule(random.choice({start_symbol}))\n\n")

        # Generate answers to each question based on selected values
        code.append("# Generate answers to each question based on selected values\n")
        code.append("answers = {\n")
        for key, question in questions.items():
            var_name = key.lower().replace(" (albums and singles)", "")
            code.append(f'    questions["{key}"]: {var_name},\n')
        code.append("}\n\n")

        # Output the article and answers
        # code.append("# Write to file\n")
        # code.append("with open(file_name, \"a\") as f:\n")
        # code.append("  f.write(\"Article\:\\n" + article + "\\n\\n")
        # code.append("  f.write(\"Article\:\\n" + article + "\\n\\n")

        # code.append("  for question, answer in answers.items():\n")
        # code.append("    print(f\"{question}: {answer}\")\n")
        file_name = f"{person}_questions.txt"
        code.append("# Write to file\n")
        code.append(f'with open("{file_name}", "w") as f:\n')
        # code.append("  f.write(\"Article:\\n" + 'article' + "\\n\\n\")\n")
        # code.append("  f.write(\"Article:\\n" + 'article' + "\\n\\n\")\n")
        #   f.write("Article:\n" + article + "\n\n")
        code.append('  f.write("Article:\\n"' + " + textwrap.fill(article,width=80) + " + '"\\n\\n")\n')
        code.append("  for question, answer in answers.items():\n")
        code.append('    f.write(f"{question}: {answer}\\n")\n')

        # Return the entire code as a string
        return "".join(code)

    # Generate the Python code
    generated_code = generate_code_from_parsed_cfg(grammar, questions)
    # print(generated_code)

    # Write the generated code to a Python file
    os.makedirs("output/cfg2qa", exist_ok=True)
    file_name = f"output/cfg2qa/{person}_test.py"
    with open(file_name, "w") as file:
        file.write(generated_code)
    print(f"Generated Python code saved to: {file_name}")
