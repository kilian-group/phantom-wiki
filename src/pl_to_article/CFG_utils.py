import re
import textwrap
import random
import openai
from nltk import CFG


CFG_prompt_template = """
write me a CFG using arrow notation to generate a bio for {} whose occupation is {},  You have to follow the following rules: 
1. use only fictional names and entity names 
2. use the arrow notation 
3. ONLY OUTPUT THE CFG 
begin your response."""

def remove_brackets(text):
    cleaned_text = re.sub(r'<(.*?)>', r'\1', text)
    return cleaned_text

def substitute_arrow(text):
    text = text.replace("→", "->")
    text = text.replace("::=", "->")
    return text

def one_line_cfg(cfg):
    lines = cfg.strip().split("\n")
    current_rule = None
    one_line_cfg = []
    
    for line in lines:
        line = line.strip()
        
        # If the line starts with a non-terminal followed by '->', it's a new rule
        if "->" in line:
            if current_rule:
                # Append the previous rule to the result before starting a new one
                one_line_cfg.append(current_rule)
            current_rule = line
        else:
            # If it's a continuation of the previous rule, append it to the same line
            current_rule += " " + line
    
    # Append the last rule
    if current_rule:
        one_line_cfg.append(current_rule)
    
    return "\n".join(one_line_cfg)

def write_bio(bio, file_path):
    bio = textwrap.fill(bio, width=80)
    with open(file_path, "w") as file:
        file.write(bio)

def match_name(line):
    # import pdb; pdb.set_trace()
    pattern = r"\((?:[A-Z][a-z]+|[a-z]+(?:\s[A-Z][a-z]+)*)\)"
    matches = re.findall(pattern, line)
    names = [match.strip("()") for match in matches]
    return names[0]

def extract_content_between_triple_quotes(paragraph):
    # Regex pattern to capture content between the first pair of triple quotes
    match = re.search(r"'''(.*?)'''", paragraph, flags=re.DOTALL)
    
    if match:
        return match.group(1).strip()
    else:
        return paragraph  # Return an empty string if no triple quotes are found
    
# Function to generate a random sentence from the CFG
def generate_sentence(grammar, production=None):
    if production is None:
        production = grammar.start()

    if isinstance(production, str):
        return production
    else:
        chosen_prod = random.choice(grammar.productions(lhs=production))
        return ' '.join(generate_sentence(grammar, prod) for prod in chosen_prod.rhs())
    
def generate_article_with_retries(person, job, max_attempts=100):
    for attempt in range(max_attempts):
        try:
            # Get a new CFG and attempt to generate an article
            raw_text = get_CFG(person, job)  # Each time we get a potentially different CFG
            processed_text = formatting_raw_input(raw_text)
            grammar = CFG.fromstring(processed_text)
            article = generate_sentence(grammar)
            if article:  # Check if the article is non-empty
                print(f"Attempt {attempt + 1}: Successfully generated article for {person}")
                return article, processed_text
        except Exception as e:
            # Catch any exceptions that might occur during generation
            print(f"Attempt {attempt + 1}: Error generating article - {e}")
    return "Failed to generate an article after multiple attempts."

def get_CFG(person, job):
        CFG_prompt = CFG_prompt_template.format(person, job)
        response =openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": CFG_prompt}
            ]
        )
        raw_text = response.choices[0].message.content
        return raw_text

def formatting_raw_input(raw_text):
        # delete the ``` and strip the text
        processed_text = raw_text.replace("```", "").strip()
        # sustitue '<>' with '' using regex
        processed_text = remove_brackets(processed_text)
        # substitute '::=' with '->'
        processed_text = substitute_arrow(processed_text)
        # convert to one line CFG
        processed_text = one_line_cfg(processed_text)

        return processed_text