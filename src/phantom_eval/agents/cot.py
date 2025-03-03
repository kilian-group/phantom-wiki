"""
This module implements Chain of Thought agents for phantom_eval, i.e. the cot method.
The module contains three main agent classes:

- `CoTAgent`: Base agent implementing the standard Chain of Thought evaluation method
- `CoTSCAgent`: CoT agent with self-consistency using majority voting
- `CoTRAGAgent`: CoT agent with Retrieval Augmented Generation (RAG)
"""

import logging
import re
import traceback

import pandas as pd

import phantom_eval.constants as constants
from phantom_eval._types import ContentTextMessage, Conversation, LLMChatResponse, Message
from phantom_eval.agents.common import (
    REASONING_LLM_NAMES,
    Agent,
    RAGMixin,
    SCMixin,
    get_all_evidence,
    parse_prolog_query,
)
from phantom_eval.llm import InferenceGenerationConfig, LLMChat
from phantom_eval.prompts import LLMPrompt

logger = logging.getLogger(__name__)


class CoTAgent(Agent):
    """
    Agent that implements the cot (Chain of Thought) evaluation method.
    """

    def __init__(
        self,
        text_corpus: pd.DataFrame,
        llm_prompt: LLMPrompt,
        cot_examples: str = "",
        prolog_query: bool = False,
    ):
        """
        Args:
            text_corpus (pd.DataFrame): The text corpus to search for answers.
                Must contain two columns: 'title' and 'article'.
            llm_prompt (LLMPrompt): The prompt to be used by the agent.
            cot_examples (str): Prompt examples to include in agent prompt.
                Defaults to "".
            prolog_query (bool): Whether to use the prompt for eliciting prolog queries from LLMs.
                Passed on to `LLMPrompt.get_prompt()`. Defaults to False.
        """
        super().__init__(text_corpus, llm_prompt)
        self.cot_examples = cot_examples
        self.prolog_query = prolog_query

    def combine_evidence_and_question(self, evidence: str, question: str) -> str:
        return self.llm_prompt.get_prompt(prolog_query=self.prolog_query).format(
            evidence=evidence, examples=self.cot_examples, question=question
        )

    def _build_agent_prompt(self, question: str) -> str:
        evidence = get_all_evidence(self.text_corpus)
        return self.combine_evidence_and_question(evidence, question)

    async def run(
        self, llm_chat: LLMChat, question: str, inf_gen_config: InferenceGenerationConfig
    ) -> LLMChatResponse:
        logger.debug(f"\n\t>>> question: {question}\n")

        # Create a conversation with 1 user prompt and initialize agent interactions
        prompt = self._build_agent_prompt(question)
        conv = Conversation(messages=[Message(role="user", content=[ContentTextMessage(text=prompt)])])
        self.agent_interactions = conv

        # Generate response
        inf_gen_config = inf_gen_config.model_copy(
            update=dict(stop_sequences=[]), deep=True
        )  # remove \n from stop sequences
        response = await llm_chat.generate_response(conv, inf_gen_config)

        # Add the response to the agent's conversation
        self.agent_interactions.messages.append(
            Message(role="assistant", content=[ContentTextMessage(text=response.pred)])
        )

        if self.prolog_query:
            response.pred = parse_prolog_query(response.pred)
            return response

        # Parse the response to extract the answer
        try:
            if llm_chat.model_name in REASONING_LLM_NAMES:
                pred = CoTAgent.parse_thinking_answer(response.pred)
            else:
                pred = CoTAgent.parse_answer(response.pred)
            error = None
        except Exception as e:
            pred = ""
            error = f"<agent_error>{traceback.format_exc()}</agent_error>"
            error = f"<agent_error>{e}</agent_error>"
        return LLMChatResponse(pred=pred, usage=response.usage, error=error)

    async def batch_run(
        self, llm_chat: LLMChat, questions: list[str], inf_gen_config: InferenceGenerationConfig
    ) -> list[LLMChatResponse]:
        logger.debug(f"\n\t>>> questions: {questions}\n")

        # Create a conversation for each user prompt, and initialize agent interactions
        prompts: list[str] = [self._build_agent_prompt(question) for question in questions]
        convs = [
            Conversation(messages=[Message(role="user", content=[ContentTextMessage(text=prompt)])])
            for prompt in prompts
        ]
        self.agent_interactions = convs

        # Generate response
        inf_gen_config = inf_gen_config.model_copy(
            update=dict(stop_sequences=[]), deep=True
        )  # remove \n from stop sequences
        responses = await llm_chat.batch_generate_response(convs, inf_gen_config)

        # Add the responses to the agent's conversations
        for i, response in enumerate(responses):
            self.agent_interactions[i].messages.append(
                Message(role="assistant", content=[ContentTextMessage(text=response.pred)])
            )
            if self.prolog_query:
                responses[i].pred = parse_prolog_query(response.pred)

        # Parse the responses to extract the answers
        parsed_responses: list[LLMChatResponse] = []
        for response in responses:
            # Try to parse the response, otherwise return an error
            try:
                if llm_chat.model_name in REASONING_LLM_NAMES:
                    pred = CoTAgent.parse_thinking_answer(response.pred)
                else:
                    pred = CoTAgent.parse_answer(response.pred)
                error = None
            except Exception:
                pred = ""
                error = f"<agent_error>{traceback.format_exc()}</agent_error>"
            parsed_responses.append(LLMChatResponse(pred=pred, usage=response.usage, error=error))
        return parsed_responses

    @classmethod
    def parse_answer(cls, pred: str) -> str:
        """
        Parse the response to extract the answer using regex.
        The prediction should be of the form: "... The answer is <answer>." otherwise a ValueError is raised.
        """
        pattern = r"[t|T]he answer is (.+)\.\s*$"
        m = re.search(pattern, pred)
        if m:
            return m.group(1)
        else:
            raise ValueError(f"Answer '{pred}' cannot be parsed.")

    @classmethod
    def parse_thinking_answer(cls, pred: str) -> str:
        """
        Parse the response to extract the answer using regex.
        The prediction should be of the form: "</think>... The answer is <answer>."
        otherwise a ValueError is raised.
        """
        pattern = r"</think>.*[tT]he answer is \s*(.+)\."
        m = re.search(pattern, pred, re.DOTALL)  # re.DOTALL to match newlines as well
        if m:
            return m.group(1)
        else:
            raise ValueError(f"Answer '{pred}' cannot be parsed.")

    def reset(self) -> None:
        self.agent_interactions: Conversation = Conversation(messages=[])


class CoTSCAgent(CoTAgent, SCMixin):
    """
    Agent to implement cot-sc evaluation with majority vote (self-consistency).
    """

    def __init__(
        self,
        text_corpus: pd.DataFrame,
        llm_prompt: LLMPrompt,
        cot_examples: str = "",
        num_votes: int = 3,
        sep: str = constants.answer_sep,
    ):
        """
        Args:
            text_corpus (pd.DataFrame): The text corpus to search for answers.
                Must contain two columns: 'title' and 'article'.
            llm_prompt (LLMPrompt): The prompt to be used by the agent.
            cot_examples (str): CoT prompt examples to include in agent prompt.
                Defaults to "".
            num_votes (int): The number of votes to take for the majority vote.
                Defaults to 3.
            sep (str): The separator used to split the prediction.
                Defaults to `constants.answer_sep`.
        """
        CoTAgent.__init__(self, text_corpus, llm_prompt, cot_examples)
        SCMixin.__init__(self, num_votes, sep)

    async def run(
        self, llm_chat: LLMChat, question: str, inf_gen_config: InferenceGenerationConfig
    ) -> LLMChatResponse:
        # Relies on the implementation of run in the subclass
        responses: list[LLMChatResponse] = [
            await super().run(llm_chat, question, inf_gen_config) for _ in range(self.num_votes)
        ]
        return self.take_majority_vote(responses, self.sep)

    async def batch_run(
        self, llm_chat: LLMChat, questions: list[str], inf_gen_config: InferenceGenerationConfig
    ) -> list[LLMChatResponse]:
        # Relies on the implementation of batch_run in the subclass
        responses: list[list[LLMChatResponse]] = [
            await super().batch_run(llm_chat, questions, inf_gen_config) for _ in range(self.num_votes)
        ]  # shape (num_votes, num_questions)
        # Take majority vote for each question, so transpose the responses list
        transposed_responses = [list(responses_each_question) for responses_each_question in zip(*responses)]
        return [
            self.take_majority_vote(responses_each_question, self.sep)
            for responses_each_question in transposed_responses
        ]


class CoTRAGAgent(CoTAgent, RAGMixin):
    """
    Agent to implement cot-rag evaluation where the agent uses retriever to create evidence.
    """

    def __init__(
        self,
        text_corpus: pd.DataFrame,
        llm_prompt: LLMPrompt,
        cot_examples: str = "",
        embedding_model_name: str = "whereisai/uae-large-v1",
        retriever_num_documents: int = 4,
        port: int = 8001,
    ):
        """
        Args:
            text_corpus (pd.DataFrame): The text corpus to search for answers.
                Must contain two columns: 'title' and 'article'.
            llm_prompt (LLMPrompt): The prompt to be used by the agent.
            cot_examples (str): Prompt examples to include in agent prompt.
                Defaults to "".
            embedding_model_name (str): The name of the embedding model to use for retrieval.
                Defaults to "whereisai/uae-large-v1".
            retriever_num_documents (int): The number of documents to retrieve.
                Defaults to 4.
            port (int): The port to use for the retriever.
                Defaults to 8001.
        """
        CoTAgent.__init__(self, text_corpus, llm_prompt, cot_examples)
        RAGMixin.__init__(self, text_corpus, embedding_model_name, retriever_num_documents, port)

    def _build_agent_prompt(self, question):
        evidence = self.get_RAG_evidence(question)
        return self.combine_evidence_and_question(evidence, question)
