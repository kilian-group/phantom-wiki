CFG_PROMPT_TEMPLATE = """
Create a context-free grammar using arrow notation to generate a biography for {} whose occupation is {}, following these rules:
1. Use only fictional names and entity names
2. DO NOT include family information
3. Use the arrow notation
4. ONLY OUTPUT THE CONTEXT-FREE GRAMMAR.
"""

CFG2QAs_TEMPLATE = """
For the following context-free grammar (CFG):

{}

Suppose you are given an article generated with this CFG.
Generate the questions you can ask about some non-terminals where the answer is one of the choices from the CFG and output a list in the following format:

nonterminal: question

Each nonterminal and question pair should appear on a new line.
"""

CFG_PROMPT_TEMPLATE_LLAMA = """
Create a context-free grammar (CFG) using arrow notation to generate a short, formal bio for a fictional character with a specified occupation.
Please follow these rules:
Use only fictional names and entity names.
Exclude all family information (family name, spouse, children, parents, etc.).
Use standard arrow notation for the CFG, with quotes around all terminal strings (i.e., plain text).
Output only the CFG, aiming for a moderate level of complexity.
Use the given character name as a fixed value in the CFG (do not generate alternative names).
Character: {} Occupation: {}"""
