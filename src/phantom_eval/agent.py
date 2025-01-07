import abc
import logging
import re
from collections import Counter
from copy import deepcopy

import pandas as pd

from phantom_eval.llm import LLMChat, LLMChatResponse, InferenceGenerationConfig
from phantom_eval.data import Conversation, ContentTextMessage, Message
from phantom_eval.prompts import LLMPrompt
from phantom_eval.score import normalize_pred
import phantom_eval.constants as constants

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
    def __init__(self, text_corpus: pd.DataFrame, llm_prompt: LLMPrompt):
        super().__init__(text_corpus, llm_prompt)

    def __get_evidence(self) -> str:
        """
        Returns all articles (concatenated as a string) in the text corpus as evidence.
        """
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

    def run(self, llm_chat: LLMChat, question: str, inf_gen_config: InferenceGenerationConfig) -> LLMChatResponse:
        logger.debug(f"\n\t>>> question: {question}\n")

        # Create a conversation with 1 user prompt
        prompt = self._build_agent_prompt(question)
        conv = Conversation(messages=[
            Message(role="user", content=[ContentTextMessage(text=prompt)])
        ])
        
        # Generate response
        # Add "\n" to stop_sequences
        inf_gen_config = inf_gen_config.model_copy(update=dict(stop_sequences=["\n"]), deep=True)
        response = llm_chat.generate_response(conv, inf_gen_config)
        return response
    
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
        
        # Generate response
        # Change stop_sequences to "\n"
        inf_gen_config = inf_gen_config.model_copy(update=dict(stop_sequences=["\n"]), deep=True)
        responses = await llm_chat.batch_generate_response(convs, inf_gen_config)
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
        usage: dict = self._aggregate_usage([response.usage for response in responses])

        # Flatten the list of sets to a single list, e.g. becomes [A, B, A, B, C]
        all_answers: list[str] = [answer for pred in preds for answer in pred]
        vote_counts = Counter(all_answers)

        # Select all answers that have more than n_preds / 2 counts
        majority_responses = [answer for answer, count in vote_counts.items() if count > n_preds / 2]
        majority_responses_str = sep.join(majority_responses)
        return LLMChatResponse(pred=majority_responses_str, usage=usage)
    
    def _aggregate_usage(self, usage_list: list[dict]) -> dict:
        """Recursively sum the values of the usage dict.

        NOTE: assumes that each usage dict shares a common schema.
        Otherwise, value errors may occur.

        Args:
            usage_list (list[dict]): List of usage dict objects.
        Returns:
            dict: The aggregated usage dict.
        """
        if len(usage_list) <= 0:
            return {}
        result = deepcopy(usage_list[0]) # use first usage dict as reference
        for key in result.keys():
            if isinstance(result[key], dict):
                result[key] = self._aggregate_usage([usage[key] for usage in usage_list])
            else:
                result[key] = sum([usage[key] for usage in usage_list])
        return result


class NshotSCAgent(NshotAgent, SCMixin):
    """
    Agent to implement Zeroshot and fewshot evaluation with majority vote.
    """
    def __init__(self, text_corpus: pd.DataFrame, llm_prompt: LLMPrompt, num_votes: int = 3, sep: str = constants.answer_sep):
        """
        Args:
            num_votes (int): The number of votes to take for the majority vote.
                Defaults to 3.
            sep (str): The separator used to split the prediction.
                Defaults to `config.answer_sep`.
        """
        NshotAgent.__init__(self, text_corpus, llm_prompt)
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

        while (self.step_round <= self.max_steps) and (not self.finished):
            try:
                response = self._step_thought(llm_chat, question, inf_gen_config)

                response = self._step_action(llm_chat, question, inf_gen_config)

                response = self._step_observation(response)
            except Exception as e:
                # If an error occurs, return the error message and empty pred
                response = LLMChatResponse(
                    pred="", usage={}, error=f"<agent_error>{e}</agent_error>"
                )
                break

        if (self.step_round > self.max_steps) and (not self.finished):
            # If agent exceeds max steps without answer, return the error message and empty pred
            response = LLMChatResponse(
                pred="", usage={}, error=f"<agent_error>Max react steps ({self.max_steps}) reached without finishing.</agent_error>"
            )

        return response

    def _step_thought(self, llm_chat: LLMChat, question: str, inf_gen_config: InferenceGenerationConfig) -> LLMChatResponse:
        """
        Run the thought step of the agent.
        """
        # Add "</thought>" to stop_sequences
        inf_gen_config = inf_gen_config.model_copy(update=dict(stop_sequences=["</thought>"]), deep=True)
        response = self._prompt_agent(llm_chat, question, inf_gen_config)
        response.pred = f"{format_pred(response.pred)}</thought>"
        logger.debug(f"\n\t>>> {response.pred}\n")
        response.pred = get_tag_at_round(response.pred, tag_type="thought", step_round=self.step_round)

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
        # Add "</action>" to stop_sequences
        inf_gen_config = inf_gen_config.model_copy(update=dict(stop_sequences=["</action>"]), deep=True)
        response = self._prompt_agent(llm_chat, question, inf_gen_config)
        response.pred = f"{format_pred(response.pred)}</action>"
        logger.debug(f"\n\t>>> {response.pred}\n")
        response.pred = get_tag_at_round(response.pred, tag_type="action", step_round=self.step_round)

        # Update scrachpad and agent's conversation
        self.scratchpad += "\n" + response.pred
        self.agent_interactions.messages.append(
            Message(role="assistant", content=[ContentTextMessage(text=response.pred)])
        )
        return response

    def _step_observation(self, response_action: LLMChatResponse) -> LLMChatResponse:
        """
        Run the observation step of the agent and increments the step round.
        Returned usage is empty since the LLM is not called.
        """
        action_type, action_arg = parse_action(response_action.pred)
        match action_type:
            case "Finish":
                self.step_round += 1
                self.finished = True
                return LLMChatResponse(pred=action_arg, usage={})
            case "RetrieveArticle":
                try:
                    # Fetch the article for the requested entity by looking up the title
                    article: str = self.text_corpus.loc[self.text_corpus["title"] == action_arg, "article"].values[0]
                    observation_str = format_pred(article)
                except IndexError:
                    observation_str = f"No article exists for the requested entity. Please try retrieving article for another entity."
            case "Search":
                try:
                    # Fetch all articles that contain the requested attribute
                    articles: list[str]  = self.text_corpus.loc[self.text_corpus["article"].str.contains(action_arg), "article"].tolist()
                    enum_articles: str = "\n\n".join(f"{i+1}: {article}" for i, article in enumerate(articles))
                    observation_str = format_pred(enum_articles)
                except IndexError:
                    observation_str = f"No articles contain the requested attribute. Please try searching for another attribute."
            case _:
                observation_str = "Invalid action. Valid actions are RetrieveArticle[{{entity}}], Search[{{attribute}}], and Finish[{{answer}}]."
        observation_for_round = f"<observation round=\"{self.step_round}\">{observation_str}</observation>"
        logger.debug(f"\n\t>>> {observation_for_round}\n")

        # Update scrachpad and agent's conversation
        self.scratchpad += "\n" + observation_for_round
        self.agent_interactions.messages.append(
            Message(role="user", content=[ContentTextMessage(text=observation_for_round)])
        )

        self.step_round += 1
        return LLMChatResponse(pred=observation_for_round, usage={})

    def _prompt_agent(self, llm_chat: LLMChat, question: str, inf_gen_config: InferenceGenerationConfig) -> LLMChatResponse:
        """
        Prompt the LLM with the agent's current prompt and the given question.
        `inf_gen_config` is passed to the LLM's generation function.
        """
        # Put the full scratchpad in the prompt and ask the LLM to generate.
        # All of the back and forth conversation so far becomes the user prompt.
        user_message: str = self._build_agent_prompt(question)
        conv: Conversation = Conversation(messages=[
            Message(role="user", content=[ContentTextMessage(text=user_message)])
        ])
        response: LLMChatResponse = llm_chat.generate_response(conv, inf_gen_config)
        return response


def get_tag_at_round(pred: str, tag_type: str, step_round: int) -> str:
    """
    Performs a regex match on the prediction to extract the tag.
    Tag is of the form: `<tag_type round="<step_round>">...</tag_type>`.

    Returns:
        str: `"<tag_type round="<step_round>">...</tag_type>"`.

    Raises:
        ValueError: If the tag cannot be parsed.
    """
    pattern = f"(<{tag_type} round=\"{step_round}\">.+?</{tag_type}>)"
    m = re.search(pattern, pred)

    if m:
        return m.group(1)
    else:
        raise ValueError(f"Tag '{pred}' cannot be parsed with {tag_type=} and {step_round=}.")


def parse_action(s: str) -> tuple[str, str] | None:
    """
    Returns a tuple of the action type and the argument, else None if the string s is not in correct format.
    Correct format: `<action round="<num>">action_type[<argument>]</action>`.

    Raises:
        ValueError: If the action cannot be parsed.
    """
    # Extract the action type (any word string) and argument (any string within square brackets)
    # argument can be empty as well
    pattern = r'<action round="\d">(\w+)\[(.*?)\]</action>'
    m = re.search(pattern, s)
    
    if m:
        action_type = m.group(1)
        action_arg = m.group(2)

        # Normalize the argument
        action_arg = action_arg.lower()
        return action_type, action_arg
    else:
        raise ValueError(f"Action '{s}' cannot be parsed.")


def format_pred(pred: str) -> str:
    """
    Format the prediction by stripping newlines and spaces.
    """
    return pred.strip("\n").strip().replace("\n", " ")


SUPPORTED_METHOD_NAMES: list[str] = [
    "zeroshot",
    "fewshot",
    "zeroshot-sc",
    "fewshot-sc",
    "CoT",
    "react"
]


def get_agent(
    method: str,
    text_corpus: pd.DataFrame,
    llm_prompt: LLMPrompt,
    agent_kwargs: dict,
) -> Agent:
    match method:
        case "zeroshot" | "fewshot":
            return NshotAgent(text_corpus, llm_prompt)
        case "zeroshot-sc" | "fewshot-sc":
            return NshotSCAgent(text_corpus, llm_prompt, **agent_kwargs)
        case "CoT":
            raise NotImplementedError("CoT evaluation is not supported yet.")
        case "react":
            return ReactAgent(text_corpus, llm_prompt, **agent_kwargs)
        case _:
            raise ValueError(f"Invalid method: {method}")
