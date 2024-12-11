import re
import string

import pandas as pd
from langchain.prompts import PromptTemplate
from termcolor import colored

from llm import LLMChat
from data import Conversation, ContentTextMessage, Message

# TODO add more examples
REACT_EXAMPLES6 = """
<question>Who is the father of anastasia?</question>
<thought round="1">I need to retrieve article about anastasia and find who her father is.</thought>
<action round="1">RetrieveArticle[anastasia]</action>
<observation round="1"># anastasia ## Family The child of anastasia is jack, ringo, maeve. The son of anastasia is dirk. The father of anastasia is daniel. The husband of anastasia is bob. ## Friends The friend of anastasia is marie, thomas, kate. ## Attributes The date of birth of anastasia is 0213-01-04. The job of anastasia is realtor. The hobby of anastasia is bird watching.</observation>
<thought round="2">The father of anastasia is daniel, so the answer is daniel.</thought>
<action round="2">Finish[daniel]</action>
"""

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
        self.answer: list[str] = []
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
                self.answer = []
                self.error = (type(e).__name__, e)
                break
    
    def step(self, llm_chat: LLMChat) -> None:
        def sys_print(message: str) -> None:
            print(colored(">>> ", "green") + message)
        
        # Think
        response = self.prompt_agent(llm_chat, is_action=False)
        thought = get_tag_at_round(response, tag_type="thought", step_round=self.step_round)
        self.scratchpad +=  "\n" + thought
        sys_print(f"LLM's response: {thought}")
        print()

        # Act
        response = self.prompt_agent(llm_chat, is_action=True)
        action = get_tag_at_round(response, tag_type="action", step_round=self.step_round)
        self.scratchpad += "\n" + action
        action_type, argument = parse_action(action)
        argument = argument.lower() # Normalize the argument
        sys_print(f"LLM's response: {action}")
        print()

        # MEMENTO
        self.actions.append((action_type, argument))

        # Observe
        match action_type:
            case "Finish":
                self.answer = argument.split(",")
                if self.is_correct():
                    observation_str = "Answer is CORRECT"
                else: 
                    observation_str = "Answer is INCORRECT"
                self.finished = True
                self.step_round += 1
                return
            case "RetrieveArticle":
                try:
                    article: str = self.text_corpus.loc[self.text_corpus["title"] == argument, "article"].values[0]
                    observation_str = format_step(article)
                except IndexError:
                    observation_str += f"The last article searched was not found. Please try retrieved another article."
            case _:
                observation_str += "Invalid Action. Valid Actions are RetrieveArticle[{{entity}}] and Finish[{{answer}}]."
        observation_for_round = f"<observation round=\"{self.step_round}\">{observation_str}</observation>"
        self.scratchpad += "\n" + observation_for_round
        sys_print(f"After action: {observation_for_round}")
        print()

        self.step_round += 1

    def prompt_agent(self, llm_chat: LLMChat, is_action: bool) -> str:
        # TODO is_action not used
        # No turn-style conversation. All of the back and forth conversation so far becomes the user prompt.
        user_message: str = self._build_agent_prompt()
        conv: Conversation = Conversation(messages=[
            Message(role="user", content=[ContentTextMessage(text=user_message)])
        ])
        resp = llm_chat.generate_response(conv)
        return format_step(resp)
    
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
        return self.step_round > self.max_steps

    def __reset_agent(self) -> None:
        self.step_round = 1
        self.finished = False
        self.scratchpad: str = ''
        self.actions = []
        # debugging outputs
        self.error = None


def get_tag_at_round(response: str, tag_type: str, step_round: int) -> str:
    if tag_type in ["thought", "action"]:
        pattern = f"(<{tag_type} round=\"{step_round}\">.+?</{tag_type}>)"
        match = re.search(pattern, response)
        return match.group(1)
    else:
        raise ValueError(f"Invalid tag_type: {tag_type} or {step_round}")


def parse_action(s: str) -> tuple[str, str] | None:
    """
    Returns a tuple of the action type and the argument, else None if the string s is not in correct format.
    Correct format: `<action_type>[<argument>]`.
    """
    pattern = r'<action round="\d">(\w+)\[(.+?)\]</action>$'
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


def is_exact_match(answer: list[str], keys: list[str]) -> bool:
    return set(map(normalize_answer, answer)) == set(map(normalize_answer, keys))
