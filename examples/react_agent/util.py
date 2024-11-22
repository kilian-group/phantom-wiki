import os
import joblib
import dill

'''
%%%%%%%%%%%%%%%%% Logging utils for CoT methods %%%%%%%%%%%%%%%%%
'''
def summarize_trial(agents):
    correct = [a for a in agents if a.is_correct()]
    incorrect = [a for a in agents if a.is_finished() and not a.is_correct()]
    return correct, incorrect

def remove_fewshot(prompt: str) -> str:
    prefix = prompt.split('Here are some examples:')[0]
    suffix = prompt.split('(END OF EXAMPLES)')[1]
    return prefix.strip('\n').strip() + '\n' +  suffix.strip('\n').strip()

def log_trial(agents, trial_n):
    correct, incorrect = summarize_trial(agents)

    log = f"""
########################################
BEGIN TRIAL {trial_n}
Trial summary: Correct: {len(correct)}, Incorrect: {len(incorrect)}
#######################################
"""

    log += '------------- BEGIN CORRECT AGENTS -------------\n\n'
    for agent in correct:
        log += remove_fewshot(agent._build_agent_prompt()) + f'\nCorrect answer: {agent.keys}\n\n'

    log += '------------- BEGIN INCORRECT AGENTS -----------\n\n'
    for agent in incorrect:
        log += remove_fewshot(agent._build_agent_prompt()) + f'\nCorrect answer: {agent.keys}\n\n'

    return log

'''
%%%%%%%%%%%%%%%%% Logging utils for ReAct/Reflexion methods %%%%%%%%%%%%%%%%%
'''
def summarize_react_trial(agents,llm):
    correct = [a for a in agents if a.is_correct()]
    halted = [a for a in agents if a.is_halted(llm)]
    incorrect = [a for a in agents if a.is_finished() and not a.is_correct()]
    runtime_error = [a for a in agents if (not a.is_finished()) and a.error]
    return correct, incorrect, halted, runtime_error

def log_react_trial(agents, trial_n, llm):
    def format_actions(agent):
        try:
            # React and ReactReflectAgent
            actions = agent.actions
        except AttributeError:
            # MementoAgent
            actions = [step['action'] for step in agent.memories]
        s = '\n'.join([f'{i+1}. {action}' for i, action in enumerate(actions)]) + '\n'
        return s
    
    correct, incorrect, halted, runtime_error = summarize_react_trial(agents, llm)

    log = f"""
########################################
BEGIN TRIAL {trial_n}
Trial summary: Correct: {len(correct)}, Incorrect: {len(incorrect)}, Halted: {len(halted)}, Runtime Error: {len(runtime_error)}
#######################################
"""

    log += '------------- BEGIN CORRECT AGENTS -------------\n\n'
    for agent in correct:
        log += remove_fewshot(agent._build_agent_prompt()) + f'\nCorrect answer: {agent.keys}'
        log += f'\nActions:\n{format_actions(agent)}'
        log += '\n\n'

    log += '------------- BEGIN INCORRECT AGENTS -----------\n\n'
    for agent in incorrect:
        log += remove_fewshot(agent._build_agent_prompt()) + f'\nCorrect answer: {agent.keys}'
        log += f'\nActions:\n{format_actions(agent)}'
        log += '\n\n'

    log += '------------- BEGIN HALTED AGENTS -----------\n\n'
    for agent in halted:
        log += remove_fewshot(agent._build_agent_prompt()) + f'\nCorrect answer: {agent.keys}'
        log += f'\nActions:\n{format_actions(agent)}'
        log += '\n\n'

    log += '------------- BEGIN RUNTIME ERROR AGENTS -----------\n\n'
    for agent in runtime_error:
        log += remove_fewshot(agent._build_agent_prompt()) + f'\nCorrect answer: {agent.keys}'
        log += f'\nActions:\n{format_actions(agent)}'
        log += f'\nError: {agent.error}'
        log += '\n\n'

    return log

def save_log(log, save_dir:str, file_name:str):
    os.makedirs(save_dir, exist_ok = True)
    save_path = os.path.join(save_dir, file_name)
    with open(save_path, 'w') as f:
        f.write(log)
def save_agents(agents, dir: str):
    os.makedirs(dir, exist_ok=True)
    for i, agent in enumerate(agents):
        with open(os.path.join(dir, f'{i}.dill'), 'wb') as f:
            dill.dump(agent, f)


'''
%%%%%%%%%%%%%%%%% Print Utils %%%%%%%%%%%%%%%%%
'''
from termcolor import colored
import textwrap

WRAPPER = textwrap.TextWrapper(width=80)

def print_wrap(output):
    """
    Print the output with text wrapping (80 characters per line).
    """
    word_list = WRAPPER.wrap(text=output)
    for element in word_list: 
        print(element)

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