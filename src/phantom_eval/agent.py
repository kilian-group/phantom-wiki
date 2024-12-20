import abc
import logging
import re

import pandas as pd

from langchain.prompts import PromptTemplate
from phantom_eval.llm import LLMChat, LLMChatResponse
from phantom_eval.data import Conversation, ContentTextMessage, Message

logger = logging.getLogger(__name__)


class Agent(abc.ABC):
    @abc.abstractmethod
    def run(self, llm_chat: LLMChat, reset: bool = True) -> None:
        pass

    # TODO function to get answer from the agent


class ReactAgent(Agent):
    def __init__(
        self,
        question: str,
        keys: list[str],
        agent_prompt: PromptTemplate,
        max_steps: int,
        text_corpus: pd.DataFrame,
        react_examples: str,
        seed: int,
    ):
        """
        Args:
            question (str): The question to be answered.
            keys (list[str]): List of correct answers.
            agent_prompt (PromptTemplate): The prompt template for the agent.
            max_steps (int): The maximum number of steps the agent can take.
            text_corpus (pd.DataFrame): The text corpus to search for answers.
                Must contain two columns: 'title' and 'article'.
            react_examples (str): Prompt examples to include in agent prompt.
        """
        self.question = question
        self.answer: list[str] = []
        self.keys = keys
        self.max_steps = max_steps
        self.agent_prompt = agent_prompt
        self.text_corpus = text_corpus
        self.react_examples = react_examples
        self.seed = seed

        self.__reset_agent()


    def run(self, llm_chat: LLMChat, reset: bool = True) -> None:
        if reset:
            self.__reset_agent()

        logger.debug(f"\n\t>>> question: {self.question}\n")
        
        while (not self.is_halted(llm_chat)) and (not self.is_finished()):
            try:
                self.step(llm_chat)
            except Exception as e:
                self.answer = []
                break
    
    def step(self, llm_chat: LLMChat) -> None:
        # Stop generating when end tag encountered. Add the end tag if not present in response
        # Think
        response = self.prompt_agent(llm_chat, stop_sequences=["</thought>"])
        response = f"{response}</thought>"
        logger.debug(f"\n\t>>> {response}\n")
        thought = get_tag_at_round(response, tag_type="thought", step_round=self.step_round)
        self.scratchpad +=  "\n" + thought
        logger.debug(thought)

        # Act
        response = self.prompt_agent(llm_chat, stop_sequences=["</action>"])
        response = f"{response}</action>"
        logger.debug(f"\n\t>>> {response}\n")
        action = get_tag_at_round(response, tag_type="action", step_round=self.step_round)
        self.scratchpad += "\n" + action
        action_type, argument = parse_action(action)
        argument = argument.lower() # Normalize the argument
        logger.debug(action)

        # Observe
        match action_type:
            case "Finish":
                self.answer = argument.split(",")
                self.finished = True
                self.step_round += 1
                return
            case "RetrieveArticle":
                try:
                    article: str = self.text_corpus.loc[self.text_corpus["title"] == argument, "article"].values[0]
                    observation_str = format_step(article)
                except IndexError:
                    observation_str += f"No article exists for the requested entity. Please try retrieving article for another entity."
            case "Search":
                try:
                    articles: list[str]  = self.text_corpus.loc[self.text_corpus["article"].str.contains(argument), "article"].tolist()
                    enum_articles: str = "\n\n".join(f"{i+1}: {article}" for i, article in enumerate(articles))
                    observation_str = format_step(enum_articles)
                except IndexError:
                    observation_str += f"No articles contain the requested attribute. Please try searching for another attribute."
            case _:
                observation_str += "Invalid action. Valid actions are RetrieveArticle[{{entity}}], Search[{{attribute}}], and Finish[{{answer}}]."
        observation_for_round = f"<observation round=\"{self.step_round}\">{observation_str}</observation>"
        self.scratchpad += "\n" + observation_for_round
        logger.debug(observation_for_round)

        self.step_round += 1

    def prompt_agent(self, llm_chat: LLMChat, stop_sequences: list[str] | None = None) -> str:
        # No turn-style conversation. All of the back and forth conversation so far becomes the user prompt.
        user_message: str = self._build_agent_prompt()
        conv: Conversation = Conversation(messages=[
            Message(role="user", content=[ContentTextMessage(text=user_message)])
        ])
        response: LLMChatResponse = llm_chat.generate_response(
            conv, stop_sequences=stop_sequences, seed=self.seed
    )
        # TODO Log resp.usage somewhere as well
        return format_step(response.pred)
    
    def _build_agent_prompt(self) -> str:
        return self.agent_prompt.format(
            examples=self.react_examples,
            question=self.question,
            scratchpad=self.scratchpad
        )
    
    def is_finished(self) -> bool:
        return self.finished

    def is_halted(self, llm_chat: LLMChat) -> bool:
        return self.step_round > self.max_steps

    def __reset_agent(self) -> None:
        self.step_round = 1
        self.finished = False
        self.scratchpad: str = ""


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
    Correct format: `<action round="<num>">action_type[<argument>]</action>`.
    """
    pattern = r'<action round="\d">(\w+)\[(.+?)\]</action>'
    match = re.search(pattern, s)
    
    if match:
        action_type = match.group(1)
        argument = match.group(2)
        return action_type, argument
    else:
        raise ValueError(f"Action {s} cannot be parsed.")


def format_step(step: str) -> str:
    return step.strip("\n").strip().replace("\n", " ")
        