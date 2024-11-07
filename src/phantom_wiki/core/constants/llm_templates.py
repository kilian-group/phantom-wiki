CFG_PROMPT_TEMPLATE = """
Create a context-free grammar using arrow notation to generate a biography for {} whose occupation is {}, following these rules:
1. Use only fictional names and entity names
2. DO NOT include family information
3. Use the arrow notation
4. ONLY OUTPUT THE CONTEXT-FREE GRAMMAR.
"""

CFG2QAs_TEMPLATE = """
Suppose I have the following context-free grammar:

{}

Generate the questions you can ask about some non-terminals and output a list in the following format:

nonterminal: question

Each nonterminal and question pair should appear on a new line.
"""
