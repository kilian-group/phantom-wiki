CFG_prompt_template_Openai = """
write me a CFG using arrow notation to generate a bio for {} whose occupation is {},  You have to follow the following rules: 
1. use only fictional names and entity names 
2. DO NOT include family information
3. use the arrow notation 
4. ONLY OUTPUT THE CFG 
begin your response."""

CFG_prompt_template_Llama = """
Create a context-free grammar (CFG) using arrow notation to generate a short, formal bio for a fictional character with a specified occupation. 
Please follow these rules: 
Use only fictional names and entity names. 
Exclude all family information (family name, spouse, children, parents, etc.). 
Use standard arrow notation for the CFG, with quotes around all terminal strings (i.e., plain text). 
Output only the CFG, aiming for a moderate level of complexity. 
Use the given character name as a fixed value in the CFG (do not generate alternative names). 
Character: {} Occupation: {}"""

CFG2QAs_TEMPLATE = """For the following CFG: 
{}
Suppose you are given an article generated with this CFG, generate concrete questions you can ask about some non-terminals where the answer is one of the choices from the CFG and output in a list in the following format : 
nonterminal: question 
in different lines"""
