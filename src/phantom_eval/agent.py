import abc
import logging
import re

import pandas as pd

from phantom_eval.llm import LLMChat, LLMChatResponse
from phantom_eval.data import Conversation, ContentTextMessage, Message
from phantom_eval.prompts import LLMPrompt

logger = logging.getLogger(__name__)


class Agent(abc.ABC):
    def __init__(self, text_corpus: pd.DataFrame, llm_prompt: LLMPrompt):
        """
        Args:
            text_corpus (pd.DataFrame): The text corpus to search for answers.
                Must contain two columns: 'title' and 'article'.
            llm_prompt (LLMPrompt): The prompt to be used by the agent.
        """
        self.text_corpus = text_corpus
        self.llm_prompt = llm_prompt

    @abc.abstractmethod
    def run(self, llm_chat: LLMChat, seed: int) -> LLMChatResponse:
        pass

    @abc.abstractmethod
    async def batch_run(self, llm_chat: LLMChat, questions: list[str], seed: int) -> list[LLMChatResponse]:
        pass

    def reset(self) -> None:
        pass


class NshotAgent(Agent):
    """
    Agent to implement Zeroshot and fewshot evaluation, 
    depending on the given `llm_prompt` on initialization.
    """
    def __init__(
        self,
        text_corpus: pd.DataFrame,
        llm_prompt: LLMPrompt,
    ):
        super().__init__(text_corpus, llm_prompt)

    def __get_evidence(self) -> str:
        evidence = "Given the following evidence:\n"
        evidence += "========BEGIN EVIDENCE========\n"
        evidence += "\n================\n\n".join(self.text_corpus["article"])
        evidence += "========END EVIDENCE========\n"
        return evidence
    
    def _build_agent_prompt(self, question: str) -> str:
        evidence = self.__get_evidence()
        return self.llm_prompt.get_prompt().format(
            evidence=evidence,
            question=question
        )

    def run(self, llm_chat: LLMChat, question: str, seed: int) -> LLMChatResponse:
        logger.debug(f"\n\t>>> question: {question}\n")

        # Create a conversation with 1 user prompt
        prompt = self._build_agent_prompt(question)
        conv = Conversation(messages=[
            Message(role="user", content=[ContentTextMessage(text=prompt)])
        ])
        
        # Generate response
        response = llm_chat.generate_response(
            conv,
            stop_sequences=["\n"],
            seed=seed,
        )
        return response
    
    async def batch_run(self, llm_chat: LLMChat, questions: list[str], seed: int) -> list[LLMChatResponse]:
        logger.debug(f"\n\t>>> questions: {questions}\n")

        # Create a conversation with 1 user prompt
        prompts = [self._build_agent_prompt(question) for question in questions]
        convs = [
            Conversation(messages=[
                Message(role="user", content=[ContentTextMessage(text=prompt)])
            ])
            for prompt in prompts
        ]
        
        # Generate response
        responses = await llm_chat.batch_generate_response(
            convs=convs,
            stop_sequences=["\n"],
            seed=seed,
        )
        return responses


class ReactAgent(Agent):
    def __init__(
        self,
        text_corpus: pd.DataFrame,
        llm_prompt: LLMPrompt,
        max_steps: int = 6,
        react_examples: str = "",
    ):
        """
        Args:
            question (str): The question to be answered.
            max_steps (int): The maximum number of steps the agent can take.
            react_examples (str): Prompt examples to include in agent prompt.
        """
        super().__init__(text_corpus, llm_prompt)
        self.max_steps = max_steps
        self.react_examples = react_examples

        self.reset()

    def reset(self) -> None:
        self.step_round = 1
        self.finished = False
        self.scratchpad: str = ""

    def _build_agent_prompt(self, question: str) -> str:
        return self.llm_prompt.get_prompt().format(
            examples=self.react_examples,
            question=question,
            scratchpad=self.scratchpad
        )
    
    async def batch_run(self, llm_chat: LLMChat, questions: list[str], seed: int) -> list[LLMChatResponse]:
        raise NotImplementedError("Batch run is not supported for ReactAgent.")

    def run(self, llm_chat: LLMChat, question: str, seed: int) -> LLMChatResponse:
        logger.debug(f"\n\t>>> question: {question}\n")

        while (self.step_round <= self.max_steps) and (not self.finished):
            try:
                response = self._step(llm_chat, question, seed)
            except:
                response = LLMChatResponse(pred="<agent_error>", usage={})
                break
        return response
    
    def _step(self, llm_chat: LLMChat, question: str, seed: int = 1) -> LLMChatResponse:
        # Stop generating when end tag encountered. Add the end tag if not present in response
        # Think
        response = self._prompt_agent(llm_chat, question, stop_sequences=["</thought>"], seed=seed)
        pred = format_pred(response.pred)
        pred = f"{pred}</thought>"
        logger.debug(f"\n\t>>> {pred}\n")
        thought = get_tag_at_round(pred, tag_type="thought", step_round=self.step_round)
        self.scratchpad +=  "\n" + thought
        logger.debug(thought)

        # Act
        response = self._prompt_agent(llm_chat, question, stop_sequences=["</action>"], seed=seed)
        pred = format_pred(response.pred)
        pred = f"{pred}</action>"
        logger.debug(f"\n\t>>> {pred}\n")
        action = get_tag_at_round(pred, tag_type="action", step_round=self.step_round)
        self.scratchpad += "\n" + action
        action_type, argument = parse_action(action)
        argument = argument.lower() # Normalize the argument
        logger.debug(action)

        # Observe
        match action_type:
            case "Finish":
                self.step_round += 1
                self.finished = True
                # TODO aggregate usage in a full step
                return LLMChatResponse(pred=argument, usage={})
            case "RetrieveArticle":
                try:
                    article: str = self.text_corpus.loc[self.text_corpus["title"] == argument, "article"].values[0]
                    observation_str = format_pred(article)
                except IndexError:
                    observation_str += f"No article exists for the requested entity. Please try retrieving article for another entity."
            case "Search":
                try:
                    articles: list[str]  = self.text_corpus.loc[self.text_corpus["article"].str.contains(argument), "article"].tolist()
                    enum_articles: str = "\n\n".join(f"{i+1}: {article}" for i, article in enumerate(articles))
                    observation_str = format_pred(enum_articles)
                except IndexError:
                    observation_str += f"No articles contain the requested attribute. Please try searching for another attribute."
            case _:
                observation_str += "Invalid action. Valid actions are RetrieveArticle[{{entity}}], Search[{{attribute}}], and Finish[{{answer}}]."
        observation_for_round = f"<observation round=\"{self.step_round}\">{observation_str}</observation>"
        self.scratchpad += "\n" + observation_for_round
        logger.debug(observation_for_round)

        # TODO aggregate usage in a full step
        self.step_round += 1
        return LLMChatResponse(pred=observation_str, usage={})

    def _prompt_agent(self, llm_chat: LLMChat, question: str, stop_sequences: list[str] | None = None, seed: int = 1) -> LLMChatResponse:
        # No turn-style conversation. All of the back and forth conversation so far becomes the user prompt.
        user_message: str = self._build_agent_prompt(question)
        conv: Conversation = Conversation(messages=[
            Message(role="user", content=[ContentTextMessage(text=user_message)])
        ])
        response: LLMChatResponse = llm_chat.generate_response(
            conv, stop_sequences=stop_sequences, seed=seed
        )
        return response
    

def get_tag_at_round(pred: str, tag_type: str, step_round: int) -> str:
    if tag_type in ["thought", "action"]:
        pattern = f"(<{tag_type} round=\"{step_round}\">.+?</{tag_type}>)"
        match = re.search(pattern, pred)
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


def format_pred(pred: str) -> str:
    return pred.strip("\n").strip().replace("\n", " ")
        

def get_agent(
    method: str,
    text_corpus: pd.DataFrame,
    llm_prompt: LLMPrompt,
    agent_kwargs: dict,
) -> Agent:
    match method:
        case "zeroshot" | "fewshot":
            return NshotAgent(text_corpus, llm_prompt)
        case "CoT":
            raise NotImplementedError("CoT evaluation is not supported yet.")
        case "react":
            return ReactAgent(text_corpus, llm_prompt, **agent_kwargs)
        case _:
            raise ValueError(f"Invalid method: {method}")
