import abc
import logging
import re
from collections import Counter

import pandas as pd

from phantom_eval.llm import LLMChat, LLMChatResponse, InferenceGenerationConfig, aggregate_usage
from phantom_eval.data import Conversation, ContentTextMessage, Message
from phantom_eval.prompts import LLMPrompt
from phantom_eval.score import normalize_pred
import phantom_eval.constants as constants

from langchain_community.vectorstores import FAISS
from langchain_together import TogetherEmbeddings
from langchain_core.runnables import RunnablePassthrough
from langchain import hub
import os
from vllm import LLM
from .gpu_utils import get_gpu_count
import torch
import openai # from openai import OpenAI
import gc
from .gpu_utils import get_gpu_count
import subprocess
import time
import requests
import json
# from vllm.model_executor.parallel_utils.parallel_state import destroy_model_parallel


logger = logging.getLogger(__name__)


class Agent(abc.ABC):
    """
    Abstract class for an agent that implements an evaluation method by prompting an LLM.
    """
    def __init__(self, text_corpus: pd.DataFrame, llm_prompt: LLMPrompt):
        """
        Args:
            text_corpus (pd.DataFrame): The text corpus to search for answers.
                Must contain two columns: 'title' and 'article'.
            llm_prompt (LLMPrompt): The prompt to be used by the agent.
        """
        self.text_corpus = text_corpus
        self.llm_prompt = llm_prompt
        self.agent_interactions: Conversation | list[Conversation] = None

    @abc.abstractmethod
    def run(self, llm_chat: LLMChat, question: str, inf_gen_config: InferenceGenerationConfig) -> LLMChatResponse:
        """
        Run the agent with an LLM on a given question.
        """
        pass

    @abc.abstractmethod
    async def batch_run(self, llm_chat: LLMChat, questions: list[str], inf_gen_config: InferenceGenerationConfig) -> list[LLMChatResponse]:
        """
        Asynchronously run the agent with an LLM on a list of questions.
        """
        pass

    @abc.abstractmethod
    def _build_agent_prompt(self, question: str) -> str:
        """
        Returns the agent prompt with the given question.
        The prompt may depend on the agent's internal state.
        """
        pass

    def reset(self) -> None:
        """
        Reset the agent to its initial state.
        """
        pass


class NshotAgent(Agent):
    """
    Agent to implement Zeroshot and fewshot evaluation, 
    depending on the input `llm_prompt` on initialization.
    """
    def __init__(self, text_corpus: pd.DataFrame, llm_prompt: LLMPrompt, fewshot_examples: str = ""):
        """
        Args:
            fewshot_examples (str): Prompt examples to include in agent prompt.
                If "", the agent is zero-shot. Defaults to "".
        """
        super().__init__(text_corpus, llm_prompt)
        self.fewshot_examples = fewshot_examples

    def _build_agent_prompt(self, question: str) -> str:
        if self.embedding_model_name:
            evidence = self.get_RAG_evidence(question)
        else:
            evidence = _get_evidence(self.text_corpus)
        if self.fewshot_examples: # Few-shot
            return self.llm_prompt.get_prompt().format(
                evidence=evidence,
                examples=self.fewshot_examples,
                question=question
            )
        else: # Zero-shot
            return self.llm_prompt.get_prompt().format(
                evidence=evidence,
                question=question
            )

    def run(self, llm_chat: LLMChat, question: str, inf_gen_config: InferenceGenerationConfig) -> LLMChatResponse:
        logger.debug(f"\n\t>>> question: {question}\n")

        # Create a conversation with 1 user prompt and initialize agent interactions
        prompt = self._build_agent_prompt(question)
        conv = Conversation(messages=[Message(role="user", content=[ContentTextMessage(text=prompt)])])
        self.agent_interactions = conv
        
        # Generate response
        # Add "\n" to stop_sequences
        inf_gen_config = inf_gen_config.model_copy(update=dict(stop_sequences=["\n"]), deep=True)
        response = llm_chat.generate_response(conv, inf_gen_config)

        # Update agent's conversation
        self.agent_interactions.messages.append(
            Message(role="assistant", content=[ContentTextMessage(text=response.pred)])
        )
        
        return response
    
    async def batch_run(self, llm_chat: LLMChat, questions: list[str], inf_gen_config: InferenceGenerationConfig) -> list[LLMChatResponse]:
        logger.debug(f"\n\t>>> questions: {questions}\n")

        # Create a conversation for each user prompt, and initialize agent interactions
        prompts: list[str] = [self._build_agent_prompt(question) for question in questions]
        convs = [
            Conversation(messages=[Message(role="user", content=[ContentTextMessage(text=prompt)])])
            for prompt in prompts
        ]
        self.agent_interactions = convs
        
        # Generate response
        # Change stop_sequences to "\n"
        inf_gen_config = inf_gen_config.model_copy(update=dict(stop_sequences=["\n"]), deep=True)
        responses = await llm_chat.batch_generate_response(convs, inf_gen_config)

        # Add the responses to the agent's conversations
        for i, response in enumerate(responses):
            self.agent_interactions[i].messages.append(
                Message(role="assistant", content=[ContentTextMessage(text=response.pred)])
            )

        return responses


class SCMixin:
    def __init__(self, num_votes: int, sep: str):
        """
        Args:
            num_votes (int): The number of votes to take for the majority vote.
            sep (str): The separator used to split the prediction.
        """
        self.num_votes = num_votes
        self.sep = sep

    def take_majority_vote(self, responses: list[LLMChatResponse], sep: str) -> LLMChatResponse:
        """
        Take the majority vote over all answers from the response predictions.
        
        Args:
            responses (list[LLMChatResponse]): List of response predictions.
                Each response pred may contain multiple answers e.g. A, B, C.
                So response preds can be like [[A<sep>B], [A<sep>B<sep>C]] where [A<sep>B] is the first response pred
                and [A<sep>B<sep>C] is the second response pred.
            sep (str): The separator used to split the prediction.

        Returns:
            LLMChatResponse: the majority vote as a single string of answers separated by <sep>
                (the output string is in LLMChatResponse.pred).
        """
        n_preds = len(responses)
        preds: list[set[str]] = [normalize_pred(response.pred, sep) for response in responses]
        total_usage: dict = aggregate_usage([response.usage for response in responses])

        # Flatten the list of sets to a single list, e.g. becomes [A, B, A, B, C]
        all_answers: list[str] = [answer for pred in preds for answer in pred]
        vote_counts = Counter(all_answers)

        # Select all answers that have more than n_preds / 2 counts
        majority_responses = [answer for answer, count in vote_counts.items() if count > n_preds / 2]
        error = None if len(majority_responses) > 0 else f"<agent_error>No majority vote found in {vote_counts=}.</agent_error>"

        majority_responses_str = sep.join(majority_responses)
        return LLMChatResponse(pred=majority_responses_str, usage=total_usage, error=error)
    

class NshotSCAgent(NshotAgent, SCMixin):
    """
    Agent to implement Zeroshot and fewshot evaluation with majority vote.
    """
    def __init__(self, text_corpus: pd.DataFrame, llm_prompt: LLMPrompt, fewshot_examples: str = "", num_votes: int = 3, sep: str = constants.answer_sep):
        """
        Args:
            fewshot_examples (str): Prompt examples to include in agent prompt.
                If "", the agent is zero-shot. Defaults to "".
            num_votes (int): The number of votes to take for the majority vote.
                Defaults to 3.
            sep (str): The separator used to split the prediction.
                Defaults to `constants.answer_sep`.
        """
        NshotAgent.__init__(self, text_corpus, llm_prompt, fewshot_examples)
        SCMixin.__init__(self, num_votes, sep)

    def run(self, llm_chat: LLMChat, question: str, inf_gen_config: InferenceGenerationConfig) -> LLMChatResponse:
        # Relies on the implementation of run in the subclass
        responses: list[LLMChatResponse] = [
            super().run(llm_chat, question, inf_gen_config)
            for _ in range(self.num_votes)
        ]
        return self.take_majority_vote(responses, self.sep)

    async def batch_run(self, llm_chat: LLMChat, questions: list[str], inf_gen_config: InferenceGenerationConfig) -> list[LLMChatResponse]:
        # Relies on the implementation of batch_run in the subclass
        responses: list[list[LLMChatResponse]] = [
            await super().batch_run(llm_chat, questions, inf_gen_config)
            for _ in range(self.num_votes)
        ] # shape (num_votes, num_questions)
        # Take majority vote for each question, so transpose the responses list
        transposed_responses = [list(responses_each_question)
                                for responses_each_question in zip(*responses)]
        return [self.take_majority_vote(responses_each_question, self.sep) for responses_each_question in transposed_responses]


class CoTAgent(Agent):
    def __init__(
            self, 
            text_corpus: pd.DataFrame, 
            llm_prompt: LLMPrompt,
            cot_examples: str = ""
    ):
        """
        Args:
            cot_examples (str): Prompt examples to include in agent prompt.
        """
        super().__init__(text_corpus, llm_prompt)
        self.cot_examples = cot_examples

    def run(self, llm_chat: LLMChat, question: str, inf_gen_config: InferenceGenerationConfig) -> LLMChatResponse:
        logger.debug(f"\n\t>>> question: {question}\n")
        
        # Create a conversation with 1 user prompt and initialize agent interactions
        prompt = self._build_agent_prompt(question)
        conv = Conversation(messages=[Message(role="user", content=[ContentTextMessage(text=prompt)])])
        self.agent_interactions = conv
        
        # Generate response
        response = llm_chat.generate_response(conv, inf_gen_config)

        # Add the response to the agent's conversation
        self.agent_interactions.messages.append(
            Message(role="assistant", content=[ContentTextMessage(text=response.pred)])
        )
        
        # Parse the response to extract the answer
        try:
            pred = CoTAgent.parse_answer(response.pred)
            error = None
        except Exception as e:
            pred = ""
            error = f"<agent_error>{e}</agent_error>"
        return LLMChatResponse(pred=pred, usage=response.usage, error=error)
    
    async def batch_run(self, llm_chat: LLMChat, questions: list[str], inf_gen_config: InferenceGenerationConfig) -> list[LLMChatResponse]:
        logger.debug(f"\n\t>>> questions: {questions}\n")

        # Create a conversation for each user prompt, and initialize agent interactions
        prompts: list[str] = [self._build_agent_prompt(question) for question in questions]
        convs = [
            Conversation(messages=[Message(role="user", content=[ContentTextMessage(text=prompt)])])
            for prompt in prompts
        ]
        self.agent_interactions = convs

        # Generate response
        responses = await llm_chat.batch_generate_response(convs, inf_gen_config)

        # Add the responses to the agent's conversations
        for i, response in enumerate(responses):
            self.agent_interactions[i].messages.append(
                Message(role="assistant", content=[ContentTextMessage(text=response.pred)])
            )

        # Parse the responses to extract the answers
        parsed_responses: list[LLMChatResponse] = []
        for response in responses:
            # Try to parse the response, otherwise return an error
            try:
                pred = CoTAgent.parse_answer(response.pred)
                error = None
            except Exception as e:
                pred = ""
                error = f"<agent_error>{e}</agent_error>"
            parsed_responses.append(
                LLMChatResponse(pred=pred, usage=response.usage, error=error)
            )
        return parsed_responses
    
    def _build_agent_prompt(self, question: str) -> str:
        if self.embedding_model_name:
            evidence = self.get_RAG_evidence(question)
        else:
            evidence = _get_evidence(self.text_corpus)
        return self.llm_prompt.get_prompt().format(
            evidence=evidence,
            examples=self.cot_examples,
            question=question
        )
    
    @classmethod
    def parse_answer(cls, pred: str) -> tuple[str, str]:
        """
        Parse the response to extract the answer using regex.
        The prediction is of the form: "... The answer is <answer>."
        """
        pattern = r"[t|T]he answer is (.+)\.\s*$"
        m = re.search(pattern, pred)
        if m:
            return m.group(1)
        else:
            raise ValueError(f"Answer '{pred}' cannot be parsed.")

    def reset(self) -> None:
        self.agent_interactions: Conversation = Conversation(messages=[])


class CoTSCAgent(CoTAgent, SCMixin):
    """
    Agent to implement CoT evaluation with majority vote.
    """
    def __init__(
        self,
        text_corpus: pd.DataFrame,
        llm_prompt: LLMPrompt,
        cot_examples: str = "",
        num_votes: int = 3,
        sep: str = constants.answer_sep
    ):
        """
        Args:
            cot_examples (str): Prompt examples to include in agent prompt.
                Defaults to "".
            num_votes (int): The number of votes to take for the majority vote.
                Defaults to 3.
            sep (str): The separator used to split the prediction.
                Defaults to `constants.answer_sep`.
        """
        CoTAgent.__init__(self, text_corpus, llm_prompt, cot_examples)
        SCMixin.__init__(self, num_votes, sep)

    def run(self, llm_chat: LLMChat, question: str, inf_gen_config: InferenceGenerationConfig) -> LLMChatResponse:
        # Relies on the implementation of run in the subclass
        responses: list[LLMChatResponse] = [
            super().run(llm_chat, question, inf_gen_config)
            for _ in range(self.num_votes)
        ]
        return self.take_majority_vote(responses, self.sep)

    async def batch_run(self, llm_chat: LLMChat, questions: list[str], inf_gen_config: InferenceGenerationConfig) -> list[LLMChatResponse]:
        # Relies on the implementation of batch_run in the subclass
        responses: list[list[LLMChatResponse]] = [
            await super().batch_run(llm_chat, questions, inf_gen_config)
            for _ in range(self.num_votes)
        ] # shape (num_votes, num_questions)
        # Take majority vote for each question, so transpose the responses list
        transposed_responses = [list(responses_each_question)
                                for responses_each_question in zip(*responses)]
        return [self.take_majority_vote(responses_each_question, self.sep) for responses_each_question in transposed_responses]


class ActAgent(Agent):
    def __init__(
        self,
        text_corpus: pd.DataFrame,
        llm_prompt: LLMPrompt,
        max_steps: int = 6,
        act_examples: str = "",
    ):
        """
        Args:
            max_steps (int): The maximum number of steps the agent can take.
                Defaults to 6.
            act_examples (str): Prompt examples to include in agent prompt.
                Defaults to "".
        """
        super().__init__(text_corpus, llm_prompt)
        self.max_steps = max_steps
        self.act_examples = act_examples

        self.reset()

    def reset(self) -> None:
        self.step_round = 1
        self.finished = False
        self.scratchpad: str = ""
        self.agent_interactions: Conversation = Conversation(messages=[])

    def _build_agent_prompt(self, question: str) -> str:
        return self.llm_prompt.get_prompt().format(
            examples=self.act_examples,
            question=question,
            scratchpad=self.scratchpad
        )
    
    async def batch_run(self, llm_chat: LLMChat, questions: list[str], inf_gen_config: InferenceGenerationConfig) -> list[LLMChatResponse]:
        raise NotImplementedError("Batch run is not supported for ActAgent.")

    def run(self, llm_chat: LLMChat, question: str, inf_gen_config: InferenceGenerationConfig) -> LLMChatResponse:
        logger.debug(f"\n\t>>> question: {question}\n")

        # Add the initial prompt to agent's conversation
        self.agent_interactions.messages.append(
            Message(role="user", content=[ContentTextMessage(text=self._build_agent_prompt(question))])
        )

        total_usage: dict = {}
        while (self.step_round <= self.max_steps) and (not self.finished):
            try:
                response = self._step_action(llm_chat, question, inf_gen_config)
                total_usage = aggregate_usage([total_usage, response.usage])

                response = self._step_observation(response)
                total_usage = aggregate_usage([total_usage, response.usage])
            except Exception as e:
                response = LLMChatResponse(
                    pred="", usage=total_usage, error=f"<agent_error>{e}</agent_error>"
                )
                break

        if (self.step_round > self.max_steps) and (not self.finished):
            response = LLMChatResponse(
                pred="", usage=total_usage, error=f"<agent_error>Max act steps ({self.max_steps}) reached without finishing.</agent_error>"
            )

        return LLMChatResponse(pred=response.pred, usage=total_usage, error=response.error)

    def _step_action(self, llm_chat: LLMChat, question: str, inf_gen_config: InferenceGenerationConfig) -> LLMChatResponse:
        """
        Run the action step of the agent.
        """
        # Stop generating when seeing "Observation" (when action is complete)
        leading_llm_prompt = f"Action {self.step_round}: "
        inf_gen_config = inf_gen_config.model_copy(update=dict(stop_sequences=["Observation"]), deep=True)
        response = self._prompt_agent(llm_chat, question, leading_llm_prompt, inf_gen_config)
        response.pred = leading_llm_prompt + format_pred(response.pred)
        logger.debug(f"\n\t>>> {response.pred}\n")

        # Update scrachpad and agent's conversation
        self.scratchpad += "\n" + response.pred
        self.agent_interactions.messages.append(
            Message(role="assistant", content=[ContentTextMessage(text=response.pred)])
        )
        return response

    def _step_observation(self, response_action: LLMChatResponse) -> LLMChatResponse:
        """
        Run the observation step of the agent and increments the step round.
        NOTE: Returned usage is empty since the LLM is not called.
        """
        action_type, action_arg = ReactAgent.parse_action(response_action.pred)
        match action_type:
            case "Finish":
                self.step_round += 1
                self.finished = True
                return LLMChatResponse(pred=action_arg, usage={})
            case "RetrieveArticle":
                try:
                    # Fetch the article for the requested entity by looking up the title
                    # Indexing 0 raises IndexError if search is empty, i.e. no article found
                    article: str = self.text_corpus.loc[
                        self.text_corpus["title"].str.lower() == action_arg.lower(), "article"
                    ].values[0]
                    observation_str = format_pred(article)
                except IndexError:
                    observation_str = f"No article exists for the requested entity. Please try retrieving article for another entity."
            case "Search":
                # Fetch all article titles that contain the requested attribute
                article_titles: list[str]  = self.text_corpus.loc[
                    self.text_corpus["article"].str.lower().str.contains(action_arg.lower()), "title"
                ].tolist()
                if len(article_titles) == 0:
                    observation_str = f"No articles contain the requested attribute. Please try searching for another attribute."
                else:
                    enum_article_titles: str = "\n\n".join(f"({i+1}) {title}" for i, title in enumerate(article_titles))
                    observation_str = format_pred(enum_article_titles)
            case _:
                observation_str = "Invalid action. Valid actions are RetrieveArticle[{{entity}}], Search[{{attribute}}], and Finish[{{answer}}]."
        observation_for_round = f"Observation {self.step_round}: {observation_str}"
        logger.debug(f"\n\t>>> {observation_for_round}\n")

        # Update scrachpad and agent's conversation
        self.scratchpad += "\n" + observation_for_round
        self.agent_interactions.messages.append(
            Message(role="user", content=[ContentTextMessage(text=observation_for_round)])
        )

        self.step_round += 1
        return LLMChatResponse(pred=observation_for_round, usage={})

    def _prompt_agent(self, llm_chat: LLMChat, question: str, llm_leading_prompt: str, inf_gen_config: InferenceGenerationConfig) -> LLMChatResponse:
        """
        Prompt the LLM with the agent's current prompt and the given question.
        `inf_gen_config` is passed to the LLM's generation function.
        """
        # Put the full scratchpad in the prompt and ask the LLM to generate.
        # All of the back and forth conversation so far becomes the user prompt.
        user_message: str = self._build_agent_prompt(question)
        conv: Conversation = Conversation(messages=[
            Message(role="user", content=[ContentTextMessage(text=user_message + llm_leading_prompt)])
        ])
        response: LLMChatResponse = llm_chat.generate_response(conv, inf_gen_config)
        return response


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
            max_steps (int): The maximum number of steps the agent can take.
                Defaults to 6.
            react_examples (str): Prompt examples to include in agent prompt.
                Defaults to "".
        """
        super().__init__(text_corpus, llm_prompt)
        self.max_steps = max_steps
        self.react_examples = react_examples

        self.reset()

    def reset(self) -> None:
        self.step_round = 1
        self.finished = False
        self.scratchpad: str = ""
        self.agent_interactions: Conversation = Conversation(messages=[])

    def _build_agent_prompt(self, question: str) -> str:
        return self.llm_prompt.get_prompt().format(
            examples=self.react_examples,
            question=question,
            scratchpad=self.scratchpad
        )
    
    async def batch_run(self, llm_chat: LLMChat, questions: list[str], inf_gen_config: InferenceGenerationConfig) -> list[LLMChatResponse]:
        raise NotImplementedError("Batch run is not supported for ReactAgent.")

    def run(self, llm_chat: LLMChat, question: str, inf_gen_config: InferenceGenerationConfig) -> LLMChatResponse:
        logger.debug(f"\n\t>>> question: {question}\n")

        # Add the initial prompt to agent's conversation
        self.agent_interactions.messages.append(
            Message(role="user", content=[ContentTextMessage(text=self._build_agent_prompt(question))])
        )

        total_usage: dict = {}
        while (self.step_round <= self.max_steps) and (not self.finished):
            try:
                response = self._step_thought(llm_chat, question, inf_gen_config)
                total_usage = aggregate_usage([total_usage, response.usage])

                response = self._step_action(llm_chat, question, inf_gen_config)
                total_usage = aggregate_usage([total_usage, response.usage])

                response = self._step_observation(response)
                total_usage = aggregate_usage([total_usage, response.usage])
            except Exception as e:
                # If an error occurs, return the error message and empty pred
                response = LLMChatResponse(
                    pred="", usage=total_usage, error=f"<agent_error>{e}</agent_error>"
                )
                break

        if (self.step_round > self.max_steps) and (not self.finished):
            # If agent exceeds max steps without answer, return the error message and empty pred
            response = LLMChatResponse(
                pred="", usage=total_usage, error=f"<agent_error>Max react steps ({self.max_steps}) reached without finishing.</agent_error>"
            )

        return LLMChatResponse(pred=response.pred, usage=total_usage, error=response.error)

    def _step_thought(self, llm_chat: LLMChat, question: str, inf_gen_config: InferenceGenerationConfig) -> LLMChatResponse:
        """
        Run the thought step of the agent.
        """
        # Stop generating when seeing "Action" (when thought is complete)
        leading_llm_prompt = f"Thought {self.step_round}: "
        inf_gen_config = inf_gen_config.model_copy(update=dict(stop_sequences=["Action"]), deep=True)
        response = self._prompt_agent(llm_chat, question, leading_llm_prompt, inf_gen_config)
        response.pred = leading_llm_prompt + format_pred(response.pred)
        logger.debug(f"\n\t>>> {response.pred}\n")

        # Update scrachpad and agent's conversation
        self.scratchpad +=  "\n" + response.pred
        self.agent_interactions.messages.append(
            Message(role="assistant", content=[ContentTextMessage(text=response.pred)])
        )
        return response
    
    def _step_action(self, llm_chat: LLMChat, question: str, inf_gen_config: InferenceGenerationConfig) -> LLMChatResponse:
        """
        Run the action step of the agent.
        """
        # Stop generating when seeing "Observation" (when action is complete)
        leading_llm_prompt = f"Action {self.step_round}: "
        inf_gen_config = inf_gen_config.model_copy(update=dict(stop_sequences=["Observation"]), deep=True)
        response = self._prompt_agent(llm_chat, question, leading_llm_prompt, inf_gen_config)
        response.pred = leading_llm_prompt + format_pred(response.pred)
        logger.debug(f"\n\t>>> {response.pred}\n")

        # Update scrachpad and agent's conversation
        self.scratchpad += "\n" + response.pred
        self.agent_interactions.messages.append(
            Message(role="assistant", content=[ContentTextMessage(text=response.pred)])
        )
        return response

    def _step_observation(self, response_action: LLMChatResponse) -> LLMChatResponse:
        """
        Run the observation step of the agent and increments the step round.
        NOTE: Returned usage is empty since the LLM is not called.
        """
        action_type, action_arg = ReactAgent.parse_action(response_action.pred)
        match action_type:
            case "Finish":
                self.step_round += 1
                self.finished = True
                return LLMChatResponse(pred=action_arg, usage={})
            case "RetrieveArticle":
                try:
                    # Fetch the article for the requested entity by looking up the title
                    # Indexing 0 raises IndexError if search is empty, i.e. no article found
                    article: str = self.text_corpus.loc[
                        self.text_corpus["title"].str.lower() == action_arg.lower(), "article"
                    ].values[0]
                    observation_str = format_pred(article)
                except IndexError:
                    observation_str = f"No article exists for the requested entity. Please try retrieving article for another entity."
            case "Search":
                # Fetch all article titles that contain the requested attribute
                article_titles: list[str]  = self.text_corpus.loc[
                    self.text_corpus["article"].str.lower().str.contains(action_arg.lower()), "title"
                ].tolist()
                if len(article_titles) == 0:
                    observation_str = f"No articles contain the requested attribute. Please try searching for another attribute."
                else:
                    enum_article_titles: str = "\n\n".join(f"({i+1}) {title}" for i, title in enumerate(article_titles))
                    observation_str = format_pred(enum_article_titles)
            case _:
                observation_str = "Invalid action. Valid actions are RetrieveArticle[{{entity}}], Search[{{attribute}}], and Finish[{{answer}}]."
        observation_for_round = f"Observation {self.step_round}: {observation_str}"
        logger.debug(f"\n\t>>> {observation_for_round}\n")

        # Update scrachpad and agent's conversation
        self.scratchpad += "\n" + observation_for_round
        self.agent_interactions.messages.append(
            Message(role="user", content=[ContentTextMessage(text=observation_for_round)])
        )

        self.step_round += 1
        return LLMChatResponse(pred=observation_for_round, usage={})

    def _prompt_agent(self, llm_chat: LLMChat, question: str, leading_llm_prompt: str, inf_gen_config: InferenceGenerationConfig) -> LLMChatResponse:
        """
        Prompt the LLM with the agent's current prompt and the given question.
        `inf_gen_config` is passed to the LLM's generation function.
        """
        # Put the full scratchpad in the prompt and ask the LLM to generate.
        # All of the back and forth conversation so far becomes the user prompt.
        user_message: str = self._build_agent_prompt(question)
        conv: Conversation = Conversation(messages=[
            Message(role="user", content=[ContentTextMessage(text=user_message + "\n" + leading_llm_prompt)])
        ])
        response: LLMChatResponse = llm_chat.generate_response(conv, inf_gen_config)
        return response

    @classmethod
    def parse_action(cls, action: str) -> tuple[str, str]:
        """
        Returns a tuple of the action type and the argument.
        Correct format: `action_type[<argument>]`.

        Raises:
            ValueError: If the action cannot be parsed.
        """
        # Extract the action type (any word string) and argument (any string within square brackets)
        # argument can be empty as well
        pattern = r'(\w+)\[(.*?)\]'
        m = re.search(pattern, action)
        
        if m:
            action_type = m.group(1)
            action_arg = m.group(2)

            # Normalize the argument
            action_arg = action_arg.lower()
            return action_type, action_arg
        else:
            raise ValueError(f"Action '{action}' cannot be parsed.")




class React_CoTSCAgent(Agent):
    """
    Agent to implement React->CoTSC evaluation.
    If React agent reaches max steps, run CoTSC agent.
    """
    def __init__(
        self,
        text_corpus: pd.DataFrame,
        react_llm_prompt: LLMPrompt,
        max_steps: int = 6,
        react_examples: str = "",
        cot_llm_prompt: LLMPrompt | None = None,
        cot_examples: str = "",
        num_votes: int = 3,
        sep: str = constants.answer_sep,
        cotsc_inf_temperature: float = constants.inf_temperature_hi,
    ):
        """
        Takes 2 LLM Prompts. Pass the first prompt to the React agent
        and the second prompt to the CoTSC agent.
        Must provide the CoTSC agent prompt, otherwise the agent is not initialized.

        Args:
            max_steps (int): The maximum number of steps the agent can take.
                Defaults to 6.
            react_examples (str): Prompt examples to include in agent prompt.
                Defaults to "".
            cot_llm_prompt (LLMPrompt): The prompt to be used by the CoTSC agent.
                Must be provided.
            cot_examples (str): Prompt examples to include in agent prompt.
                Defaults to "".
            num_votes (int): The number of votes to take for the majority vote.
                Defaults to 3.
            sep (str): The separator used to split the prediction.
                Defaults to `constants.answer_sep`.
            cotsc_inf_temperature (float): The inference temperature to use for CoTSC agent.
                Defaults to `constants.inf_temperature_hi`.
        """
        assert cot_llm_prompt is not None, "CoTSC agent prompt is required."
        super().__init__(text_corpus, react_llm_prompt)
        self.cotsc_inf_temperature = cotsc_inf_temperature
        self.react_agent = ReactAgent(text_corpus, react_llm_prompt, max_steps, react_examples)
        self.cotsc_agent = CoTSCAgent(text_corpus, cot_llm_prompt, cot_examples, num_votes, sep)

        self.reset()

    def reset(self) -> None:
        self.react_agent.reset()
        self.cotsc_agent.reset()
        self.agent_interactions: Conversation = Conversation(messages=[])

    def _build_agent_prompt(self, question: str) -> str:
        # Join the prompts of the React and CoTSC agents
        return self.react_agent._build_agent_prompt(question) + "\n\n" + self.cotsc_agent._build_agent_prompt(question)

    async def batch_run(self, llm_chat: LLMChat, questions: list[str], inf_gen_config: InferenceGenerationConfig) -> list[LLMChatResponse]:
        raise NotImplementedError("Batch run is not supported for React->CoTSCAgent.")

    def run(self, llm_chat: LLMChat, question: str, inf_gen_config: InferenceGenerationConfig) -> LLMChatResponse:
        logger.debug(f"\n\t>>> question: {question}\n")

        # Run the React agent. If the React agent reaches max steps, run the CoTSC agent.
        react_response = self.react_agent.run(llm_chat, question, inf_gen_config)
        self.agent_interactions = self.react_agent.agent_interactions
        match react_response.error:
            case None:
                # No error occurred, return the React agent's response
                # None case must be before error_msg case, because "in" operator is used in error_msg case
                return react_response
            case error_msg if "<agent_error>Max react steps" in error_msg:
                # If the React agent reaches max steps, run the CoTSC agent
                cotsc_inf_gen_config = inf_gen_config.model_copy(update=dict(temperature=self.cotsc_inf_temperature), deep=True)
                cotsc_response = self.cotsc_agent.run(llm_chat, question, cotsc_inf_gen_config)
                self.agent_interactions.messages.extend(self.cotsc_agent.agent_interactions.messages)

                total_usage = aggregate_usage([react_response.usage, cotsc_response.usage])
                return LLMChatResponse(pred=cotsc_response.pred, usage=total_usage, error=cotsc_response.error)
            case _:
                # Error msg is not related to max steps, return react's response and abort
                return react_response


class CoTSC_ReactAgent(Agent):
    """
    Agent to implement CoTSC->React evaluation.
    If CoTSC agent does not get any majority vote answer, run React agent.
    """
    def __init__(
        self,
        text_corpus: pd.DataFrame,
        cot_llm_prompt: LLMPrompt,
        cot_examples: str = "",
        num_votes: int = 3,
        sep: str = constants.answer_sep,
        cotsc_inf_temperature: float = constants.inf_temperature_hi,
        react_llm_prompt: LLMPrompt | None = None,
        max_steps: int = 6,
        react_examples: str = "",
    ):
        """
        Takes 2 LLM Prompts. Pass the first prompt to the CoTSC agent
        and the second prompt to the React agent.
        Must provide the React agent prompt, otherwise the agent is not initialized.

        Args:
            cot_examples (str): Prompt examples to include in agent prompt.
                Defaults to "".
            num_votes (int): The number of votes to take for the majority vote.
                Defaults to 3.
            sep (str): The separator used to split the prediction.
                Defaults to `constants.answer_sep`.
            cotsc_inf_temperature (float): The inference temperature to use for CoTSC agent.
                Defaults to `constants.inf_temperature_hi`.
            react_llm_prompt (LLMPrompt): The prompt to be used by the React agent.
                Must be provided.
            max_steps (int): The maximum number of steps the agent can take.
                Defaults to 6.
            react_examples (str): Prompt examples to include in agent prompt.
                Defaults to "".
        """
        assert react_llm_prompt is not None, "React agent prompt is required."
        super().__init__(text_corpus, cot_llm_prompt)
        self.cotsc_inf_temperature = cotsc_inf_temperature
        self.cotsc_agent = CoTSCAgent(text_corpus, cot_llm_prompt, cot_examples, num_votes, sep)
        self.react_agent = ReactAgent(text_corpus, react_llm_prompt, max_steps, react_examples)

        self.reset()

    def reset(self) -> None:
        self.cotsc_agent.reset()
        self.react_agent.reset()
        self.agent_interactions: Conversation = Conversation(messages=[])

    def _build_agent_prompt(self, question: str) -> str:
        # Join the prompts of the CoTSC and React agents
        return self.cotsc_agent._build_agent_prompt(question) + "\n\n" + self.react_agent._build_agent_prompt(question)
    
    async def batch_run(self, llm_chat: LLMChat, questions: list[str], inf_gen_config: InferenceGenerationConfig) -> list[LLMChatResponse]:
        raise NotImplementedError("Batch run is not supported for CoTSC->ReactAgent.")

    def run(self, llm_chat: LLMChat, question: str, inf_gen_config: InferenceGenerationConfig) -> LLMChatResponse:
        logger.debug(f"\n\t>>> question: {question}\n")

        # Run the CoTSC agent. If the CoTSC agent does not get any majority vote answer, run the React agent.
        cotsc_inf_gen_config = inf_gen_config.model_copy(update=dict(temperature=self.cotsc_inf_temperature), deep=True)
        cotsc_response = self.cotsc_agent.run(llm_chat, question, cotsc_inf_gen_config)
        self.agent_interactions = self.cotsc_agent.agent_interactions
        match cotsc_response.error:
            case None:
                # No error occurred, return the CoTSC agent's response
                # None case must be before error_msg case, because "in" operator is used in error_msg case
                return cotsc_response
            case error_msg if "<agent_error>No majority vote" in error_msg:
                # The CoTSC agent does not get any majority vote answer, run the React agent
                react_response = self.react_agent.run(llm_chat, question, inf_gen_config)
                self.agent_interactions.messages.extend(self.react_agent.agent_interactions.messages)

                total_usage = aggregate_usage([cotsc_response.usage, react_response.usage])
                return LLMChatResponse(pred=react_response.pred, usage=total_usage, error=react_response.error)
            case _:
                # Error msg is not related to majority vote, return CoTSC's response and abort
                return cotsc_response

from typing import List
from langchain_core.embeddings import Embeddings
class CustomEmbeddings(Embeddings):
    def __init__(self, client):
        self.client = client
        self.model = self.client.models.list().data[0].id

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed search docs."""
        return [obj.embedding for obj in self.client.embeddings.create(input=texts, model=self.model).data]

    def embed_query(self, text: str) -> List[float]:
        """Embed query text."""
        return self.embed_documents([text])[0]

class RAGAgent(Agent):
    def __init__(self, 
                text_corpus: pd.DataFrame, 
                llm_prompt: LLMPrompt, 
                embedding: str="together", 
                vector_store: str="faiss",
                embedding_model_name: str="meta-llama/llama-3.1-8b-instruct",#"intfloat/e5-mistral-7b-instruct"
                use_api: bool | None = True,
                max_model_len: int | None = None,
                tensor_parallel_size: int | None = None,
                use_async: bool = False,
                embedding_port: int=8001,
                ):
        """
        Args:
            embedding (str): The embedding method for the vector database. Defaults to TogetherEmbeddings. Supported options are: ["together"].
            vector_store (str): The vector store for the vector database. Defaults to FAISS. Supported options are: ["faiss"].
        """
        super().__init__(text_corpus, llm_prompt)
        self.use_async = use_async

        texts = self.text_corpus['article'].tolist()#[:20]
        torch.cuda.empty_cache() 
        if(True):
            # # API implements OpenAI API interface but doesn't need to call OpenAI's API
            # client = OpenAI(
            #     api_key="token-abc123", 
            #     base_url="http://0.0.0.0:8000/v1",
            # )
            # responses = client.embeddings.create(
            #     input=texts,
            #     model=embedding_model_name,
            # )
            logging.info("Using vLLM server for inference")
            try:
                BASE_URL = f"http://0.0.0.0:{embedding_port}/v1" # TODO: allow this to be specified by the user
                # print(BASE_URL)
                API_KEY="token-abc123" # TODO: allow this to be specified by the user
                self.client = openai.OpenAI(
                    base_url=BASE_URL,
                    api_key=API_KEY,
                )
                self.async_client = openai.AsyncOpenAI(
                    base_url=BASE_URL,
                    api_key=API_KEY,
                )
            except openai.APIConnectionError as e:
                logging.error(
                    f"Make sure to launch the vllm server using " \
                    "vllm serve MODEL_NAME --api-key token-abc123 --tensor_parallel_size NUM_GPUS"
                )
                raise e
                
            client = self.async_client if self.use_async else self.client
   
            # https://platform.openai.com/docs/guides/embeddings
            # https://docs.vllm.ai/en/latest/getting_started/examples/openai_embedding_client.html
            # logger.info(client.models.list().data[0].id) 2025-01-17 11:27:37,531 - phantom_eval.agent - INFO - meta-llama/llama-3.1-8b-instruct
            # print(client.models.list().data[0].id)
            # responses = client.embeddings.create(
            #     input=texts,
            #     model=client.models.list().data[0].id#client_cur_model,
            # )
            # models = client.models.list()
            # model = models.data[0].id

            # responses = client.embeddings.create(
            #     input=[
            #         "Hello my name is",
            #         "The best thing about vLLM is that it supports many different models"
            #     ],
            #     model=model,
            # )

            # logging.info("Responses:")
            # logging.info(responses)
            # embeddings = responses.data
            embeddings = CustomEmbeddings(client)
        
        else:
            embeddings = TogetherEmbeddings()
            vectors = embeddings.embed_documents(texts)

            # if tensor_parallel_size is None:
            #     tensor_parallel_size = get_gpu_count()
            # else:
            #     tensor_parallel_size = tensor_parallel_size

            # # destroy_model_parallel()
            # # del llm.llm_engine.model_executor.driver_worker
            # # del llm # Isn't necessary for releasing memory, but why not
            # # gc.collect()
            # # os.environ["CUDA_VISIBLE_DEVICES"] = "3,4"
            # # torch.cuda.empty_cache()

            # embedding_model = LLM(
            #     model=embedding_model_name, 
            #     task="embed", 
            #     # enforce_eager=True,
            #     max_model_len=max_model_len,
            #     tensor_parallel_size=2#tensor_parallel_size,
            # )
            # embedding_outputs = embedding_model.embed(texts)
            # embeddings = [output.outputs.embedding for output in embedding_outputs]
        
        # embeddings = TogetherEmbeddings(api_key=os.getenv("TOGETHER_API_KEY"))
        # vectors = embeddings.embed_documents(texts)

        vectorstore = FAISS.from_texts(texts, embeddings)
        self.retriever = vectorstore.as_retriever()
        self.format_docs = lambda docs: "\n================\n\n".join(doc.page_content for doc in docs)


    def __get_evidence(self, question:str) -> str:
        """
        Returns retrieved articles in the text corpus as evidence.
        """
        if False: # NOTE: the zeroshot prompt already includes the begin/end evidence headers
            evidence = "Given the following evidence:\n"
            evidence += "========BEGIN EVIDENCE========\n"
            # evidence += "\n================\n\n".join(self.rag_chain.invoke(question))
            evidence += self.format_docs(self.retriever.invoke(question))
            evidence += "========END EVIDENCE========\n"
            # print(evidence)
            return evidence
        else:
            evidence = self.format_docs(self.retriever.invoke(question))
            return evidence

    def _build_agent_prompt(self, question: str) -> str:
        evidence = self.__get_evidence(question)
        return self.llm_prompt.get_prompt().format(
            evidence=evidence,
            question=question
        )

    def _parse_answer(cls, pred: str) -> tuple[str, str]:
        """
        Parse the response to extract the answer using regex.
        The prediction is of the form: "... The answer is <answer>."
        """
        pattern = r"answer is (.+)\.\s*$"
        m = re.search(pattern, pred)
        if m:
            return m.group(1)
        else:
            return ""

    def run(self, llm_chat: LLMChat, question: str, inf_gen_config: InferenceGenerationConfig) -> LLMChatResponse:
        logger.debug(f"\n\t>>> question: {question}\n")

        # Create a conversation with 1 user prompt
        prompt = self._build_agent_prompt(question)
        print(prompt)
        # print(prompt)
        conv = Conversation(messages=[
            Message(role="user", content=[ContentTextMessage(text=prompt)])
        ])
        self.agent_interactions = conv
        
        # Generate response
        # Add "\n" to stop_sequences
        # inf_gen_config = inf_gen_config.model_copy(update=dict(stop_sequences=["\n"]), deep=True)
        response = llm_chat.generate_response(conv, inf_gen_config)

        # Update agent's conversation
        self.agent_interactions.messages.append(
            Message(role="assistant", content=[ContentTextMessage(text=response.pred)])
        )
        return response.pred # return self._parse_answer(response.pred)
    
    async def batch_run(self, llm_chat: LLMChat, questions: list[str], inf_gen_config: InferenceGenerationConfig) -> list[LLMChatResponse]:
        logger.debug(f"\n\t>>> questions: {questions}\n")

        # Create a conversation with 1 user prompt
        prompts = [self._build_agent_prompt(question) for question in questions]
        convs = [
            Conversation(messages=[
                Message(role="user", content=[ContentTextMessage(text=prompt)])
            ])
            for prompt in prompts
        ]
        self.agent_interactions = convs
        
        # Generate response
        # Change stop_sequences to "\n"
        # inf_gen_config = inf_gen_config.model_copy(update=dict(stop_sequences=["\n"]), deep=True)
        responses = await llm_chat.batch_generate_response(convs, inf_gen_config)

        # Add the responses to the agent's conversations
        for i, response in enumerate(responses):
            self.agent_interactions[i].messages.append(
                Message(role="assistant", content=[ContentTextMessage(text=response.pred)])
            )
        return [
            LLMChatResponse(
                pred=response.pred,#self._parse_answer(response.pred),
                usage=response.usage,
                error=response.error,
            ) 
            for response in responses
        ]
        # return [self._parse_answer(r.pred) for r in responses]

class RAGMixin:
    def __init__(self, 
                text_corpus: pd.DataFrame, 
                embedding_model_name: str="WhereIsAI/UAE-Code-Large-V1",
                use_api: bool | None = True,
                tensor_parallel_size: int | None = 1,
                port:int = 8001,
                ):
        """
        Args:
            embedding_model_name (str): The embedding method for the vector database. Defaults to WhereIsAI/UAE-Code-Large-V. All VLLM models are supported.
        """

        self.embedding_model_name = embedding_model_name
        texts = self.text_corpus['article'].tolist()
        if(use_api):
            # launch server
            subprocess.call(["./src/phantom_eval/launch_embedding_server.sh", 
                            embedding_model_name, 
                            str(port), 
                            str(get_gpu_count()-1)
                            ])

            # build retriever
            BASE_URL = f"http://0.0.0.0:{port}/v1" 
            API_KEY="token-abc123" 
            client = openai.OpenAI(
                base_url=BASE_URL,
                api_key=API_KEY,
            )
            embeddings = CustomEmbeddings(client)
            vectorstore = FAISS.from_texts(texts, embeddings)
            self.retriever = vectorstore.as_retriever()
        else:
            raise NotImplementedError("Not implemented yet")

        # subprocess.call(["./src/phantom_eval/launch_embedding_server.sh", 
        #                     embedding_model_name, 
        #                     str(port), 
        #                     str(get_gpu_count()-1)
        #                     ])
        # self.use_async = False

        # texts = self.text_corpus['article'].tolist()#[:20]
        # torch.cuda.empty_cache() 
        # if(True):
        #     logging.info("Using vLLM server for inference")
        #     try:
        #         BASE_URL = f"http://0.0.0.0:{port}/v1" # TODO: allow this to be specified by the user
        #         API_KEY="token-abc123" # TODO: allow this to be specified by the user
        #         self.client = openai.OpenAI(
        #             base_url=BASE_URL,
        #             api_key=API_KEY,
        #         )
        #         self.async_client = openai.AsyncOpenAI(
        #             base_url=BASE_URL,
        #             api_key=API_KEY,
        #         )
        #     except openai.APIConnectionError as e:
        #         logging.error(
        #             f"Make sure to launch the vllm server using " \
        #             "vllm serve MODEL_NAME --api-key token-abc123 --tensor_parallel_size NUM_GPUS"
        #         )
        #         raise e
                
        #     client = self.async_client if self.use_async else self.client
        #     embeddings = CustomEmbeddings(client)
        
        # vectorstore = FAISS.from_texts(texts, embeddings)
        # self.retriever = vectorstore.as_retriever()
        # self.format_docs = lambda docs: "\n================\n\n".join(doc.page_content for doc in docs)
    
    def get_RAG_evidence(self, question:str) -> str:
        """
        Returns retrieved articles in the text corpus as evidence.
        """
        self.format_RAG_docs = lambda docs: "\n================\n\n".join(doc.page_content for doc in docs)
        evidence = self.format_RAG_docs(self.retriever.invoke(question))
        return evidence
    


class NshotRAGAgent(NshotAgent, RAGMixin):
    """
    Agent to implement Zeroshot and fewshot evaluation with majority vote.
    """
    def __init__(self, 
                text_corpus: pd.DataFrame, 
                llm_prompt: LLMPrompt, 
                fewshot_examples: str = "", 
                embedding_model_name: str="WhereIsAI/UAE-Code-Large-V",
                use_api: bool | None = True,
                tensor_parallel_size: int | None = 1,
                port:int = 8001,
                ):
        """
        Args:
            fewshot_examples (str): Prompt examples to include in agent prompt.
                If "", the agent is zero-shot. Defaults to "".
            sep (str): The separator used to split the prediction.
                Defaults to `constants.answer_sep`.
        """
        NshotAgent.__init__(self, text_corpus, llm_prompt, fewshot_examples)
        RAGMixin.__init__(self, text_corpus, embedding_model_name, use_api, tensor_parallel_size, port)

    def run(self, 
            llm_chat: LLMChat, 
            question: str, 
            inf_gen_config: InferenceGenerationConfig
            ) -> LLMChatResponse:
        # Relies on the implementation of run in the subclass
        return super().run(llm_chat, question, inf_gen_config)

    async def batch_run(self, 
                        llm_chat: LLMChat, 
                        questions: list[str], 
                        inf_gen_config: InferenceGenerationConfig
                        ) -> list[LLMChatResponse]:
        # Relies on the implementation of batch_run in the subclass
        return await super().batch_run(llm_chat, questions, inf_gen_config)


class CoTRAGAgent(CoTAgent, RAGMixin):
    """
    Agent to implement Zeroshot and fewshot evaluation with majority vote.
    """
    def __init__(self, 
                text_corpus: pd.DataFrame, 
                llm_prompt: LLMPrompt, 
                cot_examples: str = "",
                embedding_model_name: str="WhereIsAI/UAE-Code-Large-V",
                use_api: bool | None = True,
                tensor_parallel_size: int | None = 1,
                port:int = 8001,
                ):
        """
        Args:
            cot_examples (str): Prompt examples to include in agent prompt.
        """
        CoTAgent.__init__(self, text_corpus, llm_prompt, cot_examples)
        RAGMixin.__init__(self, text_corpus, embedding_model_name, use_api, tensor_parallel_size, port)

    def run(self, 
            llm_chat: LLMChat, 
            question: str, 
            inf_gen_config: InferenceGenerationConfig
            ) -> LLMChatResponse:
        # Relies on the implementation of run in the subclass
        return super().run(llm_chat, question, inf_gen_config)

    async def batch_run(self, 
                        llm_chat: LLMChat, 
                        questions: list[str], 
                        inf_gen_config: InferenceGenerationConfig
                        ) -> list[LLMChatResponse]:
        # Relies on the implementation of batch_run in the subclass
        return await super().batch_run(llm_chat, questions, inf_gen_config)

#### Utils ####

def format_pred(pred: str) -> str:
    """
    Format the prediction by stripping newlines and spaces.
    """
    return pred.strip("\n").strip().replace("\n", " ")


def _get_evidence(text_corpus: pd.DataFrame) -> str:
    """Utility for constructing evidence
    Returns all articles (concatenated as a string) in the text corpus as evidence.
    """
    return "\n================\n\n".join(text_corpus["article"])


SUPPORTED_METHOD_NAMES: list[str] = [
    "zeroshot",
    "fewshot",
    "zeroshot-sc",
    "fewshot-sc",
    "cot",
    "cot-sc",
    "react",
    "act",
    "react->cot-sc",
    "cot-sc->react",
    "retriever",
    "fewshot-retriever",
    "cot-retriever",
]


def get_agent(
    method: str,
    text_corpus: pd.DataFrame,
    llm_prompt: LLMPrompt,
    agent_kwargs: dict,
) -> Agent:
    match method:
        case "zeroshot" | "fewshot":
            return NshotAgent(text_corpus, llm_prompt, **agent_kwargs)
        case "zeroshot-sc" | "fewshot-sc":
            return NshotSCAgent(text_corpus, llm_prompt, **agent_kwargs)
        case "cot":
            return CoTAgent(text_corpus, llm_prompt, **agent_kwargs)
        case "cot-sc":
            return CoTSCAgent(text_corpus, llm_prompt, **agent_kwargs)
        case "react":
            return ReactAgent(text_corpus, llm_prompt, **agent_kwargs)
        case "act":
            return ActAgent(text_corpus, llm_prompt, **agent_kwargs)
        case "react->cot-sc":
            return React_CoTSCAgent(text_corpus, llm_prompt, **agent_kwargs)
        case "cot-sc->react":
            return CoTSC_ReactAgent(text_corpus, llm_prompt, **agent_kwargs)
        case "retriever" | "fewshot-retriever":
            # return RAGAgent(text_corpus, llm_prompt, **agent_kwargs)
            return NshotRAGAgent(text_corpus, llm_prompt, **agent_kwargs)
        case "cot-retriever":
            return CoTRAGAgent(text_corpus, llm_prompt, **agent_kwargs)
        case _:
            raise ValueError(f"Invalid method: {method}")
