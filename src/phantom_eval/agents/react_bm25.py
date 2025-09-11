"""
This module implements a more scalable version of the ReAct agent in `react.py` using BM25 retrieval.

Tools:
1. Search[entity]: Retrieve article by exact title match (case insensitive).
If multiple chunks with same title exist, merges them into single string. If no exact match is found,
search the entire corpus for the entity using BM25 retrieval.
2. Lookup[keyword]: Retrieve sentence containing the keyword in the current article.
Looks up the next occurrence of keyword in current article and returns
sentence and surrounding context (if get_contextual_sentences is True).
"""

import json
import logging
import re
import traceback
from collections import defaultdict
from pathlib import Path

import nltk
import pandas as pd
import tqdm
from flashrag.retriever import BM25Retriever
from joblib import Memory
from nltk.tokenize import PunktSentenceTokenizer

from phantom_eval._types import ContentTextMessage, Conversation, LLMChatResponse, Message
from phantom_eval.agents.common import Agent
from phantom_eval.llm import InferenceGenerationConfig, LLMChat, aggregate_usage
from phantom_eval.prompts import LLMPrompt

logger = logging.getLogger(__name__)

memory = Memory("cachedir")


def format_pred(pred: str) -> str:
    """
    Format the prediction by stripping newlines and spaces.
    """
    return pred.strip("\n").strip().replace("\n", " ")


class TextCorpus:
    """Handles reading and searching JSONL corpus files.

    NOTE: Assumes the id field in the corpus is 0-indexed, so that we can use the id as the index.
    """

    _title_mappings = defaultdict(list)  # title -> list of ids
    _data = {}  # id -> data
    _retriever = None  # Static variable for BM25 retriever

    def __init__(self, corpus_path: str, index_path: str):
        if not Path(corpus_path).exists():
            raise FileNotFoundError(f"Corpus file not found: {Path(corpus_path)}")
        if not Path(index_path).exists():
            raise FileNotFoundError(f"Index file not found: {Path(index_path)}")

        # Initialize NLTK sentence tokenizer
        try:
            nltk.data.find("tokenizers/punkt")
        except LookupError:
            nltk.download("punkt")

        self.sentence_tokenizer = PunktSentenceTokenizer()

        # State for lookup operations
        self.current_sentences = None
        self.lookup_state = {"keyword": None, "last_match_index": -1}  # Index of last matched sentence

        # Build title_mappings and data dictionary if not already done
        if TextCorpus._title_mappings == {} and TextCorpus._data == {}:
            TextCorpus._title_mappings, TextCorpus._data = TextCorpus.load_corpus(corpus_path, index_path)

        # Initialize the BM25 retriever if not already done
        if TextCorpus._retriever is None:
            bm25_config = {
                "retrieval_method": "bm25",
                "retrieval_topk": 4,  # default param here
                "index_path": index_path,
                "corpus_path": corpus_path,
                "silent_retrieval": True,
                "bm25_backend": "bm25s",
                # Additional retriever features
                # See https://github.com/bogoliubon/FlashRAG/blob/
                # 5f6eeafbf86c959475c4989b699666e5ccaa1a21/docs/
                # original_docs/basic_usage.md#additional-features-of-the-retriever
                "save_retrieval_cache": False,
                "retrieval_cache_path": "~",
                "use_retrieval_cache": False,
                "use_reranker": False,
            }
            logger.info("Initializing BM25 retriever...")
            TextCorpus._retriever = BM25Retriever(config=bm25_config)

    @classmethod
    @memory.cache
    def load_corpus(cls, corpus_path: str, index_path: str) -> None:
        # Count lines for tqdm total
        with open(corpus_path) as f:
            num_lines = sum(1 for _ in f)

        # Build title_mappings and data dictionary
        corpus_data = []
        title_mappings = defaultdict(list)
        data = {}
        with open(corpus_path) as f, tqdm.tqdm(f, total=num_lines, desc="Loading corpus") as pbar:
            for line in pbar:
                entry = json.loads(line)
                corpus_data.append(entry)
                article_id = entry.get("id")
                content = entry.get("contents", "")

                # Extract title: first line, strip quotes and whitespace
                title = content.split("\n", 1)[0].strip().strip('"').lower()
                article = content.split("\n", 1)[1].strip()
                title_mappings[title].append(article_id)
                data[article_id] = article

        return title_mappings, data

    @classmethod
    @memory.cache
    def _get_title_mappings(cls, corpus_path: str, index_path: str) -> None:
        """
        Construct the title mappings for the corpus.

        This function is only called once, then cached in local disk for future use.
        """
        corpus = cls._retriever.corpus

        # create a pandas dataframe with optimized types
        df = pd.DataFrame(
            {
                "id": pd.Series(corpus["id"], dtype="int32"),
                "title": pd.Series(corpus["title"], dtype="category"),
            }
        )
        # Optimized groupby operation
        return (
            df.groupby("title", sort=False, as_index=False)
            .agg({"id": list})
            .set_index("title")["id"]
            .to_dict()
        )

    def _split_into_sentences(self, text: str) -> list[str]:
        """
        Split text into sentences using NLTK's Punkt tokenizer.

        This tokenizer handles:
        - Common abbreviations (Mr., Dr., Prof., etc.)
        - Common technical abbreviations (e.g., i.e., etc.)
        - Organizations (Corp., Inc., Ltd.)
        - Multiple dots (...)
        - Brackets and quotes

        Args:
            text (str): Text to split into sentences

        Returns:
            list[str]: List of sentences, with whitespace stripped
        """
        # Remove excessive whitespace and normalize line endings
        text = " ".join(text.split())

        # Tokenize into sentences
        sentences = self.sentence_tokenizer.tokenize(text)

        # Clean up sentences
        return [s.strip() for s in sentences if s.strip()]

    def search_title_exact_match(self, title: str) -> str | None:
        """
        Retrieve article by exact title match (case insensitive).
        If multiple chunks with same title exist, merges them into single string.
        Also updates current_sentences for lookup operations.
        """
        # Normalize title to match how it's stored in title_mappings
        title = title.strip().strip('"').lower()
        article_ids = TextCorpus._title_mappings.get(title)
        if article_ids:
            # Use self.data for fast lookup
            if True:
                article_chunks = [
                    TextCorpus._data[article_id]
                    for article_id in article_ids
                    if article_id in TextCorpus._data
                ]
            else:
                # article_chunks = [
                #     TextCorpus._retriever.corpus["article"][article_id] for article_id in article_ids
                # ]
                article_chunks = TextCorpus._retriever.corpus.select(article_ids)["article"]

            # Merge all chunks and update state
            article = "\n".join(article_chunks)
            self.current_sentences = self._split_into_sentences(article)
            self.lookup_state = {"keyword": None, "last_match_index": -1}
            return article
        else:
            self.current_sentences = None
            self.lookup_state = {"keyword": None, "last_match_index": -1}
            return None

    def search_title_bm25(self, title: str, k: int = 2) -> str | None:
        results = TextCorpus._retriever.search(title, num=k)
        if len(results) > 0:
            article_ids = [result["id"] for result in results]
            if True:
                article_chunks = [
                    TextCorpus._data[article_id]
                    for article_id in article_ids
                    if article_id in TextCorpus._data
                ]
            else:
                # article_chunks = [
                #     TextCorpus._retriever.corpus["article"][article_id] for article_id in article_ids
                # ]
                article_chunks = TextCorpus._retriever.corpus.select(article_ids)["article"]

            # Merge all chunks and update state
            article = "\n".join(article_chunks)
            self.current_sentences = self._split_into_sentences(article)
            self.lookup_state = {"keyword": None, "last_match_index": -1}
            return article
        else:
            self.current_sentences = None
            self.lookup_state = {"keyword": None, "last_match_index": -1}
            return None

    def lookup_keyword(self, keyword: str, get_contextual_sentences: bool = True) -> tuple[str | None, str]:
        """
        Looks up the next occurrence of keyword in current article and returns
        sentence and surrounding context (if get_contextual_sentences is True).

        Args:
            keyword (str): The keyword to search for (case insensitive)
            get_contextual_sentences (bool): Whether to return the contextual sentences
                (sentence before and after)

        Returns:
            tuple[str | None, str]: (context_window, status_message)
            - context_window: String containing the matching sentence and surrounding context
                            or None if no match/error
            - status_message: Description of the result or error message
        """
        # Check if we have an article loaded
        if not self.current_sentences:
            return None, "No article currently loaded. Please search for an article first."

        # Reset state if new keyword
        if keyword != self.lookup_state["keyword"]:
            self.lookup_state = {"keyword": keyword, "last_match_index": -1}

        # Find next sentence containing the keyword (case insensitive)
        keyword_lower = keyword.lower()

        for i in range(self.lookup_state["last_match_index"] + 1, len(self.current_sentences)):
            if keyword_lower in self.current_sentences[i].lower():
                self.lookup_state["last_match_index"] = i
                if get_contextual_sentences:
                    # Get context window (2 sentences before and after)
                    start_idx = max(0, i - 2)
                    end_idx = min(len(self.current_sentences), i + 3)
                    context = " ".join(self.current_sentences[start_idx:end_idx])

                    return context, f"Found match in sentence {i + 1} of {len(self.current_sentences)}"
                else:
                    # Return only the sentence containing the keyword
                    return (
                        self.current_sentences[i],
                        f"Found match in sentence {i + 1} of {len(self.current_sentences)}",
                    )
        # If we get here, no more matches were found
        if self.lookup_state["last_match_index"] == -1:
            return None, f"No occurrences of '{keyword}' found in the current article."
        else:
            return (
                None,
                (
                    f"No more occurrences of '{keyword}' found after "
                    f"sentence {self.lookup_state['last_match_index'] + 1}."
                ),
            )


class ReactBM25Agent(Agent):
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
        index_path: str = None,
        corpus_path: str = None,
        prolog_query: bool = False,
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
            index_path (str): Path to a JSONL index file. Defaults to None.
            corpus_path (str): Path to a JSONL corpus file. Defaults to None.
            prolog_query (bool): Whether to use prolog query. Defaults to False. Is not used in this agent.
        """
        text_corpus = TextCorpus(corpus_path, index_path)

        super().__init__(text_corpus, llm_prompt)
        self.max_steps = max_steps
        self.react_examples = react_examples
        self.prolog_query = prolog_query

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
        self,
        llm_chat: LLMChat,
        questions: list[str],
        inf_gen_config: InferenceGenerationConfig,
        *args,
        **kwargs,
    ) -> list[LLMChatResponse]:
        raise NotImplementedError("Batch run is not supported for ReactAgent.")

    async def run(
        self,
        llm_chat: LLMChat,
        question: str,
        inf_gen_config: InferenceGenerationConfig,
        *args,
        **kwargs,
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
        action_type, action_arg = self.parse_action(response_action.pred)
        match action_type:
            case "Finish":
                self.step_round += 1
                self.finished = True
                x = LLMChatResponse(pred=action_arg, usage={})
                return x
            case "Search":
                # First, try fetching the article by exact match on the title
                try:
                    article = self.text_corpus.search_title_exact_match(action_arg)
                    if article is None:
                        observation_str = (
                            "No article found with exact title match. " "Attempting BM25 search..."
                        )
                        article = self.text_corpus.search_title_bm25(action_arg)
                        if article is None:
                            observation_str = "No article found with BM25 search."
                        else:
                            observation_str = format_pred(article)
                    else:
                        observation_str = format_pred(article)
                except Exception as e:
                    logger.error(f"Error during Search action with arg '{action_arg}': {e}")
                    observation_str = "An error occurred during the search operation."
            case "Lookup":
                sentence, observation_str = self.text_corpus.lookup_keyword(action_arg)
                observation_str = format_pred(observation_str)
            case _:
                observation_str = (
                    "Invalid action. Valid actions are Search[{{attribute}}], "
                    "Lookup[{{keyword}}], and Finish[{{answer}}]."
                )
        observation_for_round = f"Observation {self.step_round}: {observation_str}"
        logger.debug(f"\n\t>>> {observation_for_round}\n")

        # Update scratchpad and agent's conversation
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
