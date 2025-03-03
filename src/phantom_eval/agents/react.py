"""
This module implements various agentic evaluation methods for question answering tasks.
The module contains several agent classes:
- `ReactAgent`: Implements the ReAct (Thought, Action, Observation) evaluation pattern
- `ActAgent`: Implements a simpler Action-Observation evaluation pattern
- `React_CoTSCAgent`: Combines ReAct with Chain-of-Thought Self-Consistency, falling back to
    CoTSC if ReAct fails
- `CoTSC_ReactAgent`: Combines Chain-of-Thought Self-Consistency with ReAct, falling back to
    ReAct if CoTSC fails
"""

import logging
import re
import traceback

import pandas as pd

import phantom_eval.constants as constants
from phantom_eval._types import ContentTextMessage, Conversation, LLMChatResponse, Message
from phantom_eval.agents.common import Agent
from phantom_eval.agents.cot import CoTSCAgent
from phantom_eval.llm import InferenceGenerationConfig, LLMChat, aggregate_usage
from phantom_eval.prompts import LLMPrompt

logger = logging.getLogger(__name__)


def format_pred(pred: str) -> str:
    """
    Format the prediction by stripping newlines and spaces.
    """
    return pred.strip("\n").strip().replace("\n", " ")


class ReactAgent(Agent):
    """
    Agent that implements agentic react (thought, action, observation) evaluation.

    The LLM generates a thought based on the conversation history, then an action based on the thought.
    The agent then observes the result of the action and updates the conversation history.
    """

    def __init__(
        self,
        text_corpus: pd.DataFrame,
        llm_prompt: LLMPrompt,
        max_steps: int = 6,
        react_examples: str = "",
    ):
        """
        Args:
            text_corpus (pd.DataFrame): The text corpus to search for answers.
                Must contain two columns: 'title' and 'article'.
            llm_prompt (LLMPrompt): The prompt to be used by the agent.
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
            examples=self.react_examples, question=question, scratchpad=self.scratchpad
        )

    async def batch_run(
        self, llm_chat: LLMChat, questions: list[str], inf_gen_config: InferenceGenerationConfig
    ) -> list[LLMChatResponse]:
        raise NotImplementedError("Batch run is not supported for ReactAgent.")

    async def run(
        self, llm_chat: LLMChat, question: str, inf_gen_config: InferenceGenerationConfig
    ) -> LLMChatResponse:
        logger.debug(f"\n\t>>> question: {question}\n")

        # Add the initial prompt to agent's conversation
        self.agent_interactions.messages.append(
            Message(role="user", content=[ContentTextMessage(text=self._build_agent_prompt(question))])
        )

        total_usage: dict = {}
        while (self.step_round <= self.max_steps) and (not self.finished):
            try:
                response = await self._step_thought(llm_chat, question, inf_gen_config)
                total_usage = aggregate_usage([total_usage, response.usage])

                response = await self._step_action(llm_chat, question, inf_gen_config)
                total_usage = aggregate_usage([total_usage, response.usage])

                response = await self._step_observation(response)
                total_usage = aggregate_usage([total_usage, response.usage])
            except Exception:
                # If an error occurs, return the error message and empty pred
                response = LLMChatResponse(
                    pred="", usage=total_usage, error=f"<agent_error>{traceback.format_exc()}</agent_error>"
                )
                break

        if (self.step_round > self.max_steps) and (not self.finished):
            # If agent exceeds max steps without answer, return the error message and empty pred
            response = LLMChatResponse(
                pred="",
                usage=total_usage,
                error=f"<agent_error>Max react steps ({self.max_steps}) "
                "reached without finishing.</agent_error>",
            )

        return LLMChatResponse(pred=response.pred, usage=total_usage, error=response.error)

    async def _step_thought(
        self, llm_chat: LLMChat, question: str, inf_gen_config: InferenceGenerationConfig
    ) -> LLMChatResponse:
        """
        Run the thought step of the agent.
        Stop generating when seeing "Action" token from LLM (when thought is complete).

        Args:
            llm_chat (LLMChat): The LLMChat object to use for generating responses.
            question (str): The question to ask the agent.
            inf_gen_config (InferenceGenerationConfig): The inference generation config to use
                for generating responses.
        """
        # Stop generating when seeing "Action" (when thought is complete)
        leading_llm_prompt = f"Thought {self.step_round}: "
        inf_gen_config = inf_gen_config.model_copy(update=dict(stop_sequences=["Action"]), deep=True)
        response = await self._prompt_agent(llm_chat, question, leading_llm_prompt, inf_gen_config)
        response.pred = leading_llm_prompt + format_pred(response.pred)
        logger.debug(f"\n\t>>> {response.pred}\n")

        # Update scrachpad and agent's conversation
        self.scratchpad += "\n" + response.pred
        self.agent_interactions.messages.append(
            Message(role="assistant", content=[ContentTextMessage(text=response.pred)])
        )
        return response

    async def _step_action(
        self, llm_chat: LLMChat, question: str, inf_gen_config: InferenceGenerationConfig
    ) -> LLMChatResponse:
        """
        Run the action step of the agent.
        Stop generating when seeing "Observation" token from LLM (when thought is complete).

        Args:
            llm_chat (LLMChat): The LLMChat object to use for generating responses.
            question (str): The question to ask the agent.
            inf_gen_config (InferenceGenerationConfig): The inference generation config to use
                for generating responses.
        """
        # Stop generating when seeing "Observation" (when action is complete)
        leading_llm_prompt = f"Action {self.step_round}: "
        inf_gen_config = inf_gen_config.model_copy(update=dict(stop_sequences=["Observation"]), deep=True)
        response = await self._prompt_agent(llm_chat, question, leading_llm_prompt, inf_gen_config)
        response.pred = leading_llm_prompt + format_pred(response.pred)
        logger.debug(f"\n\t>>> {response.pred}\n")

        # Update scrachpad and agent's conversation
        self.scratchpad += "\n" + response.pred
        self.agent_interactions.messages.append(
            Message(role="assistant", content=[ContentTextMessage(text=response.pred)])
        )
        return response

    async def _step_observation(self, response_action: LLMChatResponse) -> LLMChatResponse:
        """
        Run the observation step of the agent depending on the action
        and increments the step round.
        NOTE: Usage in returned `LLMChatResponse.usage` is empty since the LLM is not called
        in this observation step.

        Args:
            response_action (LLMChatResponse): The response from the action step.
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
                    observation_str = (
                        "No article exists for the requested entity. "
                        "Please try retrieving article for another entity."
                    )
            case "Search":
                # Fetch all article titles that contain the requested attribute
                article_titles: list[str] = self.text_corpus.loc[
                    self.text_corpus["article"].str.lower().str.contains(action_arg.lower()), "title"
                ].tolist()
                if len(article_titles) == 0:
                    observation_str = (
                        "No articles contain the requested attribute. "
                        "Please try searching for another attribute."
                    )
                else:
                    enum_article_titles: str = "\n\n".join(
                        f"({i+1}) {title}" for i, title in enumerate(article_titles)
                    )
                    observation_str = format_pred(enum_article_titles)
            case _:
                observation_str = (
                    "Invalid action. Valid actions are RetrieveArticle[{{entity}}], "
                    "Search[{{attribute}}], and Finish[{{answer}}]."
                )
        observation_for_round = f"Observation {self.step_round}: {observation_str}"
        logger.debug(f"\n\t>>> {observation_for_round}\n")

        # Update scrachpad and agent's conversation
        self.scratchpad += "\n" + observation_for_round
        self.agent_interactions.messages.append(
            Message(role="user", content=[ContentTextMessage(text=observation_for_round)])
        )

        self.step_round += 1
        return LLMChatResponse(pred=observation_for_round, usage={})

    async def _prompt_agent(
        self,
        llm_chat: LLMChat,
        question: str,
        leading_llm_prompt: str,
        inf_gen_config: InferenceGenerationConfig,
    ) -> LLMChatResponse:
        """
        Prompts the LLM with the agent's current prompt (created from question, scratchpad,
        and `leading_llm_prompt`). The `leading_llm_prompt` is not part of the scratchpad,
        but is used to indicate the current step. For example, "Thought 1: " or "Action 2: ".

        Args:
            llm_chat (LLMChat): The LLMChat object to use for generating responses.
            question (str): The question to ask the agent.
            leading_llm_prompt (str): The prompt to indicate the current step.
            inf_gen_config (InferenceGenerationConfig): The inference generation config to use
                for generating responses.
        """
        # Put the full scratchpad in the prompt and ask the LLM to generate.
        # All of the back and forth conversation so far becomes the user prompt.
        user_message: str = self._build_agent_prompt(question)
        conv: Conversation = Conversation(
            messages=[
                Message(
                    role="user", content=[ContentTextMessage(text=user_message + "\n" + leading_llm_prompt)]
                )
            ]
        )
        response: LLMChatResponse = await llm_chat.generate_response(conv, inf_gen_config)
        return response

    @classmethod
    def parse_action(cls, action: str) -> tuple[str, str]:
        """
        Returns a tuple of the action type and the argument.
        Correct format: `action_type[<argument>]`.

        Raises:
            ValueError: If the action cannot be parsed.

        NOTE: This method is also able to handle Deepseek's outputs, because their models don't generate
        `action_type[<argument>]` action calls between <think>...</think> tags.
        """
        # Extract the action type (any word string) and argument (any string within square brackets)
        # argument can be empty as well
        pattern = r"(\w+)\[(.*?)\]"
        m = re.search(pattern, action)

        if m:
            action_type = m.group(1)
            action_arg = m.group(2)

            # Normalize the argument
            action_arg = action_arg.lower()
            return action_type, action_arg
        else:
            raise ValueError(f"Action '{action}' cannot be parsed.")


class ActAgent(Agent):
    """
    Agent that implements agentic act evaluation (action, observation).

    The LLM generates an action based on the conversation history.
    The agent then observes the result of the action and updates the conversation history.
    """

    def __init__(
        self,
        text_corpus: pd.DataFrame,
        llm_prompt: LLMPrompt,
        max_steps: int = 6,
        act_examples: str = "",
    ):
        """
        Args:
            text_corpus (pd.DataFrame): The text corpus to search for answers.
                Must contain two columns: 'title' and 'article'.
            llm_prompt (LLMPrompt): The prompt to be used by the agent.
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
            examples=self.act_examples, question=question, scratchpad=self.scratchpad
        )

    async def batch_run(
        self, llm_chat: LLMChat, questions: list[str], inf_gen_config: InferenceGenerationConfig
    ) -> list[LLMChatResponse]:
        raise NotImplementedError("Batch run is not supported for ActAgent.")

    async def run(
        self, llm_chat: LLMChat, question: str, inf_gen_config: InferenceGenerationConfig
    ) -> LLMChatResponse:
        logger.debug(f"\n\t>>> question: {question}\n")

        # Add the initial prompt to agent's conversation
        self.agent_interactions.messages.append(
            Message(role="user", content=[ContentTextMessage(text=self._build_agent_prompt(question))])
        )

        total_usage: dict = {}
        while (self.step_round <= self.max_steps) and (not self.finished):
            try:
                response = await self._step_action(llm_chat, question, inf_gen_config)
                total_usage = aggregate_usage([total_usage, response.usage])

                response = await self._step_observation(response)
                total_usage = aggregate_usage([total_usage, response.usage])
            except Exception:
                response = LLMChatResponse(
                    pred="", usage=total_usage, error=f"<agent_error>{traceback.format_exc()}</agent_error>"
                )
                break

        if (self.step_round > self.max_steps) and (not self.finished):
            response = LLMChatResponse(
                pred="",
                usage=total_usage,
                error=f"<agent_error>Max act steps ({self.max_steps})"
                "reached without finishing.</agent_error>",
            )

        return LLMChatResponse(pred=response.pred, usage=total_usage, error=response.error)

    async def _step_action(
        self, llm_chat: LLMChat, question: str, inf_gen_config: InferenceGenerationConfig
    ) -> LLMChatResponse:
        """
        Run the action step of the agent.
        Stop generating when seeing "Observation" token from LLM (when thought is complete).

        Args:
            llm_chat (LLMChat): The LLMChat object to use for generating responses.
            question (str): The question to ask the agent.
            inf_gen_config (InferenceGenerationConfig): The inference generation config to use
                for generating responses.
        """
        # Stop generating when seeing "Observation" (when action is complete)
        leading_llm_prompt = f"Action {self.step_round}: "
        inf_gen_config = inf_gen_config.model_copy(update=dict(stop_sequences=["Observation"]), deep=True)
        response = await self._prompt_agent(llm_chat, question, leading_llm_prompt, inf_gen_config)
        response.pred = leading_llm_prompt + format_pred(response.pred)
        logger.debug(f"\n\t>>> {response.pred}\n")

        # Update scrachpad and agent's conversation
        self.scratchpad += "\n" + response.pred
        self.agent_interactions.messages.append(
            Message(role="assistant", content=[ContentTextMessage(text=response.pred)])
        )
        return response

    async def _step_observation(self, response_action: LLMChatResponse) -> LLMChatResponse:
        """
        Run the observation step of the agent depending on the action
        and increments the step round.
        NOTE: Usage in returned `LLMChatResponse.usage` is empty since the LLM is not called
        in this observation step.

        Args:
            response_action (LLMChatResponse): The response from the action step.
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
                    observation_str = (
                        "No article exists for the requested entity. "
                        "Please try retrieving article for another entity."
                    )
            case "Search":
                # Fetch all article titles that contain the requested attribute
                article_titles: list[str] = self.text_corpus.loc[
                    self.text_corpus["article"].str.lower().str.contains(action_arg.lower()), "title"
                ].tolist()
                if len(article_titles) == 0:
                    observation_str = (
                        "No articles contain the requested attribute. "
                        "Please try searching for another attribute."
                    )
                else:
                    enum_article_titles: str = "\n\n".join(
                        f"({i+1}) {title}" for i, title in enumerate(article_titles)
                    )
                    observation_str = format_pred(enum_article_titles)
            case _:
                observation_str = (
                    "Invalid action. Valid actions are RetrieveArticle[{{entity}}], "
                    "Search[{{attribute}}], and Finish[{{answer}}]."
                )
        observation_for_round = f"Observation {self.step_round}: {observation_str}"
        logger.debug(f"\n\t>>> {observation_for_round}\n")

        # Update scrachpad and agent's conversation
        self.scratchpad += "\n" + observation_for_round
        self.agent_interactions.messages.append(
            Message(role="user", content=[ContentTextMessage(text=observation_for_round)])
        )

        self.step_round += 1
        return LLMChatResponse(pred=observation_for_round, usage={})

    async def _prompt_agent(
        self,
        llm_chat: LLMChat,
        question: str,
        llm_leading_prompt: str,
        inf_gen_config: InferenceGenerationConfig,
    ) -> LLMChatResponse:
        """
        Prompts the LLM with the agent's current prompt (created from question, scratchpad,
        and `leading_llm_prompt`). The `leading_llm_prompt` is not part of the scratchpad,
        but is used to indicate the current step. For example, "Action 2: ".

        Args:
            llm_chat (LLMChat): The LLMChat object to use for generating responses.
            question (str): The question to ask the agent.
            leading_llm_prompt (str): The prompt to indicate the current step.
            inf_gen_config (InferenceGenerationConfig): The inference generation config to use
                for generating responses.
        """
        # Put the full scratchpad in the prompt and ask the LLM to generate.
        # All of the back and forth conversation so far becomes the user prompt.
        user_message: str = self._build_agent_prompt(question)
        conv: Conversation = Conversation(
            messages=[
                Message(role="user", content=[ContentTextMessage(text=user_message + llm_leading_prompt)])
            ]
        )
        response: LLMChatResponse = await llm_chat.generate_response(conv, inf_gen_config)
        return response


class React_CoTSCAgent(Agent):
    """
    Agent to implement React->CoTSC evaluation, as described in the paper
    https://arxiv.org/abs/2210.03629.
    If React sub-agent reaches max steps, this agent runs CoTSC sub-agent method
    (chain of thought with self-consistency).
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
        Takes 2 LLM Prompts. The first prompt is passed to the React agent
        and the second prompt to the CoTSC agent.
        Must provide the CoTSC agent prompt (even though the default is None),
        otherwise the agent is not initialized.

        Args:
            text_corpus (pd.DataFrame): The text corpus to search for answers.
                Must contain two columns: 'title' and 'article'.
            react_llm_prompt (LLMPrompt): The prompt to be used by the React agent.
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
                This temperature is not used for the react agent, but only for the CoTSC agent.
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
        logger.warning(
            "React_CoTSCAgent._build_agent_prompt() joins prompts of"
            "React and CoTSC agents. Each agent should used only the prompts meant for them."
        )
        # Join the prompts of the React and CoTSC agents
        return (
            self.react_agent._build_agent_prompt(question)
            + "\n\n"
            + self.cotsc_agent._build_agent_prompt(question)
        )

    async def batch_run(
        self, llm_chat: LLMChat, questions: list[str], inf_gen_config: InferenceGenerationConfig
    ) -> list[LLMChatResponse]:
        raise NotImplementedError("Batch run is not supported for React->CoTSCAgent.")

    async def run(
        self, llm_chat: LLMChat, question: str, inf_gen_config: InferenceGenerationConfig
    ) -> LLMChatResponse:
        logger.debug(f"\n\t>>> question: {question}\n")

        # Run the React agent. If the React agent reaches max steps, run the CoTSC agent.
        react_response = await self.react_agent.run(llm_chat, question, inf_gen_config)
        self.agent_interactions = self.react_agent.agent_interactions
        match react_response.error:
            case None:
                # No error occurred, return the React agent's response
                # None case must be before error_msg case, because "in" operator is used in error_msg case
                return react_response
            case error_msg if "<agent_error>Max react steps" in error_msg:
                # If the React agent reaches max steps, run the CoTSC agent
                cotsc_inf_gen_config = inf_gen_config.model_copy(
                    update=dict(temperature=self.cotsc_inf_temperature), deep=True
                )
                cotsc_response = await self.cotsc_agent.run(llm_chat, question, cotsc_inf_gen_config)
                self.agent_interactions.messages.extend(self.cotsc_agent.agent_interactions.messages)

                total_usage = aggregate_usage([react_response.usage, cotsc_response.usage])
                return LLMChatResponse(
                    pred=cotsc_response.pred, usage=total_usage, error=cotsc_response.error
                )
            case _:
                # Error msg is not related to max steps, return react's response and abort
                return react_response


class CoTSC_ReactAgent(Agent):
    """
    Agent to implement CoTSC->React evaluation, as described in the paper https://arxiv.org/abs/2210.03629.
    If CoTSC sub-agent finds that no answer attains a majority vote, this agent runs React sub-agent method.
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
        Takes 2 LLM Prompts. The first prompt is passed to the CoTSC agent
        and the second prompt to the React agent.
        Must provide the React agent prompt (even though the default is None),
        otherwise the agent is not initialized.

        Args:
            text_corpus (pd.DataFrame): The text corpus to search for answers.
                Must contain two columns: 'title' and 'article'.
            cot_llm_prompt (LLMPrompt): The prompt to be used by the CoTSC agent.
            cot_examples (str): Prompt examples to include in agent prompt.
                Defaults to "".
            num_votes (int): The number of votes to take for the majority vote.
                Defaults to 3.
            sep (str): The separator used to split the prediction.
                Defaults to `constants.answer_sep`.
            cotsc_inf_temperature (float): The inference temperature to use for CoTSC agent.
                This temperature is not used for the react agent, but only for the CoTSC agent.
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
        logger.warning(
            "CoTSC_ReactAgent._build_agent_prompt() joins prompts of"
            "CoTSC and React agents. Each agent should used only the prompts meant for them."
        )
        # Join the prompts of the CoTSC and React agents
        return (
            self.cotsc_agent._build_agent_prompt(question)
            + "\n\n"
            + self.react_agent._build_agent_prompt(question)
        )

    async def batch_run(
        self, llm_chat: LLMChat, questions: list[str], inf_gen_config: InferenceGenerationConfig
    ) -> list[LLMChatResponse]:
        raise NotImplementedError("Batch run is not supported for CoTSC->ReactAgent.")

    async def run(
        self, llm_chat: LLMChat, question: str, inf_gen_config: InferenceGenerationConfig
    ) -> LLMChatResponse:
        logger.debug(f"\n\t>>> question: {question}\n")

        # Run the CoTSC agent. If the CoTSC agent does not get any majority vote answer, run the React agent.
        cotsc_inf_gen_config = inf_gen_config.model_copy(
            update=dict(temperature=self.cotsc_inf_temperature), deep=True
        )
        cotsc_response = await self.cotsc_agent.run(llm_chat, question, cotsc_inf_gen_config)
        self.agent_interactions = self.cotsc_agent.agent_interactions
        match cotsc_response.error:
            case None:
                # No error occurred, return the CoTSC agent's response
                # None case must be before error_msg case, because "in" operator is used in error_msg case
                return cotsc_response
            case error_msg if "<agent_error>No majority vote" in error_msg:
                # The CoTSC agent does not get any majority vote answer, run the React agent
                react_response = await self.react_agent.run(llm_chat, question, inf_gen_config)
                self.agent_interactions.messages.extend(self.react_agent.agent_interactions.messages)

                total_usage = aggregate_usage([cotsc_response.usage, react_response.usage])
                return LLMChatResponse(
                    pred=react_response.pred, usage=total_usage, error=react_response.error
                )
            case _:
                # Error msg is not related to majority vote, return CoTSC's response and abort
                return cotsc_response
