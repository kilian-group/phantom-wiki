import re
import string

import pandas as pd
from langchain.prompts import PromptTemplate
from termcolor import colored

from llm import LLMChat
from data import Conversation, ContentTextMessage, Message

# TODO add more examples
REACT_EXAMPLES6 = """Question: Who is the father of anastasia?
Thought 1: I need to retrieve article about anastasia and find who her father is.
Action 1: RetrieveArticle[anastasia]
Observation 1: # anastasia ## Family The child of anastasia is jack, ringo, maeve. The son of anastasia is dirk. The father of anastasia is daniel. The husband of anastasia is bob. ## Friends The friend of anastasia is marie, thomas, kate. ## Attributes The date of birth of anastasia is 0213-01-04. The job of anastasia is realtor. The hobby of anastasia is bird watching.
Thought 2: The father of anastasia is daniel, so the answer is daniel.
Action 2: Finish[daniel]"""

class ReactAgent:
    def __init__(
        self,
        question: str,
        keys: list[str],
        agent_prompt: PromptTemplate,
        max_steps: int,
        text_corpus: pd.DataFrame,
    ):
        """
        Args:
            question (str): The question to be answered.
            keys (list[str]): List of correct answers.
            agent_prompt (PromptTemplate): The prompt template for the agent.
            max_steps (int): The maximum number of steps the agent can take.
            text_corpus (pd.DataFrame): The text corpus to search for answers.
                Must contain two columns: 'title' and 'article'.
        """
        self.question = question
        self.answer = ""
        self.keys = keys
        self.max_steps = max_steps
        self.agent_prompt = agent_prompt
        self.text_corpus = text_corpus
        self.react_examples = REACT_EXAMPLES6

        self.__reset_agent()

        ############ MEMENTO ############
        # keep track of actions
        self.actions = []
        # debugging outputs
        self.error = None


    def run(self, llm_chat: LLMChat, reset: bool = True) -> None:
        if reset:
            self.__reset_agent()
        
        while (not self.is_halted(llm_chat)) and (not self.is_finished()):
            try:
                self.step(llm_chat)
            except Exception as e:
                self.answer = "" 
                self.error = (type(e).__name__, e)
                break
    
    def step(self, llm_chat: LLMChat) -> None:
        def sys_print(message: str) -> None:
            print(colored(">>> ", "green") + message)
        
        # Think
        self.scratchpad += f"\nThought {self.step_n}:"
        self.scratchpad += " " + self.prompt_agent(llm_chat, is_action=False)
        sys_print(f"LLM's response: {self.scratchpad.split('\n')[-1]}")
        print()

        # Act
        self.scratchpad += f"\nAction {self.step_n}:"
        action = self.prompt_agent(llm_chat, is_action=True)
        self.scratchpad += " " + action
        action_type, argument = parse_action(action)
        # Normalize the argument
        argument = argument.lower()
        sys_print(f"LLM's response: {self.scratchpad.split('\n')[-1]}")
        print()

        # MEMENTO
        self.actions.append((action_type, argument))

        # Observe
        self.scratchpad += f"\nObservation {self.step_n}: "
        
        match action_type:
            case "Finish":
                self.answer = argument
                if self.is_correct():
                    self.scratchpad += "Answer is CORRECT"
                else: 
                    self.scratchpad += "Answer is INCORRECT"
                self.finished = True
                self.step_n += 1
                return
            case "RetrieveArticle":
                try:
                    article: str = self.text_corpus.loc[self.text_corpus["title"] == argument, "article"].values[0]
                    self.scratchpad += format_step(article)
                except IndexError:
                    self.scratchpad += f"The last article searched was not found. Please try retrieved another article."
            case _:
                self.scratchpad += "Invalid Action. Valid Actions are RetrieveArticle[<topic>] and Finish[<answer>]."

        sys_print(f"After action: {self.scratchpad.split('\n')[-1]}")
        print()

        self.step_n += 1

    def prompt_agent(self, llm_chat: LLMChat, is_action: bool) -> str:
        # TODO is_action not used
        # No turn-style conversation. All of the back and forth conversation so far becomes the user prompt.
        user_message: str = self._build_agent_prompt()
        conv: Conversation = Conversation(messages=[
            Message(role="user", content=[ContentTextMessage(text=user_message)])
        ])
        return format_step(llm_chat.generate_response(conv))
    
    def _build_agent_prompt(self) -> str:
        return self.agent_prompt.format(
            examples=self.react_examples,
            question=self.question,
            scratchpad=self.scratchpad
        )
    
    def is_finished(self) -> bool:
        return self.finished

    def is_correct(self) -> bool:
        return is_exact_match(self.answer, self.keys)

    def is_halted(self, llm_chat: LLMChat) -> bool:
        return self.step_n > self.max_steps

    # def is_halted(self, llm_chat: LLMChat) -> bool:
    #     # TODO why get_length?
    #     return ((self.step_n > self.max_steps) or (llm_chat.get_length(self._build_agent_prompt())) > 3896) and not self.finished

    def __reset_agent(self) -> None:
        self.step_n = 1
        self.finished = False
        self.scratchpad: str = ''
        self.actions = []
        # debugging outputs
        self.error = None

    # def set_qa(self, question: str, keys: str) -> None:
    #     self.question = question
    #     self.keys = keys


def parse_action(s: str) -> tuple[str, str] | None:
    """
    Returns a tuple of the action type and the argument, else None if the string s is not in correct format.
    Correct format: `<action_type>[<argument>]`.
    """
    pattern = r'(\w+)\[(.+?)\]$'
    match = re.search(pattern, s)
    
    if match:
        action_type = match.group(1)
        argument = match.group(2)
        return action_type, argument
    else:
        return None


def format_step(step: str) -> str:
    # return step
    return step.strip('\n').strip().replace('\n', ' ')


def normalize_answer(s):
    def remove_articles(text):
        return re.sub(r"\b(a|an|the)\b", " ", text)
  
    def white_space_fix(text):
        return " ".join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return "".join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))


def is_exact_match(answer: str, keys: list[str]) -> bool:
    return normalize_answer(answer) in [normalize_answer(key) for key in keys]
