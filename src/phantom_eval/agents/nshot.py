import logging
import re
import traceback

import pandas as pd

import phantom_eval.constants as constants
from phantom_eval._types import ContentTextMessage, Conversation, LLMChatResponse, Message
from phantom_eval.agents.common import REASONING_LLM_NAMES, Agent, RAGMixin, SCMixin, get_evidence
from phantom_eval.llm.common import InferenceGenerationConfig, LLMChat
from phantom_eval.prompts import LLMPrompt

logger = logging.getLogger(__name__)


class NshotAgent(Agent):
    """
    Agent to implement Zeroshot and fewshot evaluation,
    depending on the input `llm_prompt` on initialization.
    """

    def __init__(
        self,
        text_corpus: pd.DataFrame,
        llm_prompt: LLMPrompt,
        fewshot_examples: str = "",
        prolog_query: bool = False,
    ):
        """
        Args:
            fewshot_examples (str): Prompt examples to include in agent prompt.
                If "", the agent is zero-shot. Defaults to "".
        """
        super().__init__(text_corpus, llm_prompt)
        self.fewshot_examples = fewshot_examples
        self.prolog_query = prolog_query

    def _build_agent_prompt(self, question: str) -> str:
        if hasattr(self, "embedding_model_name") and self.embedding_model_name is not None:
            # TODO this should be moved to the NshotRAGAgent class, which should override _build_agent_prompt
            evidence = self.get_RAG_evidence(question)
        else:
            evidence = get_evidence(self.text_corpus)
        if self.fewshot_examples:  # Few-shot
            return self.llm_prompt.get_prompt(self.prolog_query).format(
                evidence=evidence, examples=self.fewshot_examples, question=question
            )
        else:  # Zero-shot
            return self.llm_prompt.get_prompt(self.prolog_query).format(evidence=evidence, question=question)

    def run(
        self, llm_chat: LLMChat, question: str, inf_gen_config: InferenceGenerationConfig
    ) -> LLMChatResponse:
        logger.debug(f"\n\t>>> question: {question}\n")

        # Create a conversation with 1 user prompt and initialize agent interactions
        prompt = self._build_agent_prompt(question)
        conv = Conversation(messages=[Message(role="user", content=[ContentTextMessage(text=prompt)])])
        self.agent_interactions = conv

        # Generate response
        inf_gen_config = inf_gen_config.model_copy(update=dict(stop_sequences=[]), deep=True)
        response = llm_chat.generate_response(conv, inf_gen_config)

        # Update agent's conversation
        self.agent_interactions.messages.append(
            Message(role="assistant", content=[ContentTextMessage(text=response.pred)])
        )

        if llm_chat.model_name in REASONING_LLM_NAMES:
            try:
                pred = NshotAgent.parse_thinking_answer(response.pred)
                error = None
            except Exception as e:
                pred = ""
                error = f"<agent_error>{traceback.format_exc()}</agent_error>"
                error = f"<agent_error>{e}</agent_error>"
            return LLMChatResponse(pred=pred, usage=response.usage, error=error)

        return response

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
        inf_gen_config = inf_gen_config.model_copy(update=dict(stop_sequences=[]), deep=True)
        responses = await llm_chat.batch_generate_response(convs, inf_gen_config)

        # Add the responses to the agent's conversations
        for i, response in enumerate(responses):
            self.agent_interactions[i].messages.append(
                Message(role="assistant", content=[ContentTextMessage(text=response.pred)])
            )

        if llm_chat.model_name in REASONING_LLM_NAMES:
            parsed_responses: list[LLMChatResponse] = []
            for response in responses:
                # Try to parse the response, otherwise return an error
                try:
                    pred = NshotAgent.parse_thinking_answer(response.pred)
                    error = None
                except Exception:
                    pred = ""
                    error = f"<agent_error>{traceback.format_exc()}</agent_error>"
                parsed_responses.append(LLMChatResponse(pred=pred, usage=response.usage, error=error))
            return parsed_responses

        return responses

    @classmethod
    def parse_thinking_answer(cls, pred: str) -> str:
        """
        Parse the response to extract the answer using regex.
        The prediction is of the form: "</think> ..."
        """
        pattern = r"</think>\s*(.+)"
        m = re.search(pattern, pred)
        if m:
            return m.group(
                1
            )  # return first subgroup of the match https://docs.python.org/3/library/re.html#re.Match
        else:
            raise ValueError(f"Answer '{pred}' cannot be parsed.")


class NshotSCAgent(NshotAgent, SCMixin):
    """
    Agent to implement Zeroshot and fewshot evaluation with majority vote.
    """

    def __init__(
        self,
        text_corpus: pd.DataFrame,
        llm_prompt: LLMPrompt,
        fewshot_examples: str = "",
        num_votes: int = 3,
        sep: str = constants.answer_sep,
    ):
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

    def run(
        self, llm_chat: LLMChat, question: str, inf_gen_config: InferenceGenerationConfig
    ) -> LLMChatResponse:
        # Relies on the implementation of run in the subclass
        responses: list[LLMChatResponse] = [
            super().run(llm_chat, question, inf_gen_config) for _ in range(self.num_votes)
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


class NshotRAGAgent(NshotAgent, RAGMixin):
    """
    Agent to implement Zeroshot and fewshot evaluation with majority vote.
    """

    def __init__(
        self,
        text_corpus: pd.DataFrame,
        llm_prompt: LLMPrompt,
        fewshot_examples: str = "",
        embedding_model_name: str = "WhereIsAI/UAE-Code-Large-V",
        retriever_num_documents: int = 4,
        tensor_parallel_size: int | None = 1,
        port: int = 8001,
    ):
        """
        Args:
            fewshot_examples (str): Prompt examples to include in agent prompt.
                If "", the agent is zero-shot. Defaults to "".
            sep (str): The separator used to split the prediction.
                Defaults to `constants.answer_sep`.
        """
        NshotAgent.__init__(self, text_corpus, llm_prompt, fewshot_examples)
        RAGMixin.__init__(self, text_corpus, embedding_model_name, retriever_num_documents, port)

    def run(
        self, llm_chat: LLMChat, question: str, inf_gen_config: InferenceGenerationConfig
    ) -> LLMChatResponse:
        # Relies on the implementation of run in the subclass
        return super().run(llm_chat, question, inf_gen_config)

    async def batch_run(
        self, llm_chat: LLMChat, questions: list[str], inf_gen_config: InferenceGenerationConfig
    ) -> list[LLMChatResponse]:
        # Relies on the implementation of batch_run in the subclass
        return await super().batch_run(llm_chat, questions, inf_gen_config)
