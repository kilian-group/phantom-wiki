import abc
from copy import deepcopy
import os
import time
import logging
import asyncio

import anthropic
from pydantic import BaseModel
import openai
import tiktoken
import together
import google.generativeai as gemini
from tenacity import retry, stop_after_attempt, wait_fixed
from vllm import (LLM, SamplingParams)
from .data import ContentTextMessage, Conversation
from transformers import AutoTokenizer
from .gpu_utils import get_gpu_count

logger = logging.getLogger(__name__)


class LLMChatResponse(BaseModel):
    pred: str
    usage: dict
    error: str | None = None


def aggregate_usage(usage_list: list[dict]) -> dict:
    """
    Recursively sum the values of the usage dict, using the first non-empty dict
    as reference schema for keys. 

    NOTE: assumes that each usage dict in the list shares a common schema.
    Otherwise, value errors may occur.

    NOTE: assumes that the usage values are summable.

    Args:
        usage_list (list[dict]): List of usage dict objects.

    Returns:
        dict: The aggregated usage dict.
    """
    if len(usage_list) == 0:
        return {}

    # Find the first non-empty dict in usage_list and assign it to result
    # Use that dict as reference schema for the aggregated usage dict
    for usage in usage_list:
        if usage:
            result = deepcopy(usage)
            break

    for key in result.keys():
        if isinstance(result[key], dict):
            # result[key] is a dict, nested within the usage dict
            # Since usage lists share a common schema, we can assume that 
            # the nested dicts are of the same schema
            # Recursively sum the values of the nested dicts
            # Use .get method to default to empty dict if key not present
            result[key] = aggregate_usage([usage.get(key, {}) for usage in usage_list])
        else:
            # Assume that the values are summable (default 0 if key not present)
            # key may exist in usage dict but have a None value, so convert that to 0
            # Otherwise sum() will complain that it cannot sum None with integer
            result[key] = sum([usage.get(key, 0) or 0 for usage in usage_list])
    return result


class InferenceGenerationConfig(BaseModel):
    """
    Inference generation configuration for LLMs.
    Some LLM providers may only support a subset of these params.

    Args:
        max_tokens (int): Maximum number of tokens to generate.
            Defaults to 4096.
        seed (int): Seed for random number generator, passed to the model.
            Defaults to 0.
        stop_sequences (list[str]): List of stop words to pause generating.
            Defaults to [].
        temperature (float): Temperature parameter for sampling.
            Defaults to 0.0.
        top_p (float): top-p parameter for sampling (between 0 and 1)
            Defaults to 0.7
        top_k (int): top-k parameter for sampling (> 1)
            Defaults to 50
        repetition_penalty (int): repetition parameter (between -1 and 1)
            Defaults to 1.0
        max_retries (int): Max number of API calls allowed before giving up.
            Defaults to 3.
        wait_seconds (int): Number of seconds to wait between API calls.
            Defaults to 2.
    """
    # LLM inference params
    max_tokens: int = 4096
    repetition_penalty: int = 1.0
    seed: int = 0
    stop_sequences: list[str] = []  # pydantic handles default values correctly
    temperature: float = 0.0
    top_p: float = 0.7
    top_k: int = 50
    # API retry params
    max_retries: int = 3
    wait_seconds: int = 2


class LLMChat(abc.ABC):
    SUPPORTED_LLM_NAMES: list[str] = []

    def __init__(
        self,
        model_name: str,
        model_path: str | None = None,
    ):
        """
        Initialize the LLM chat object.

        Args:
            model_name (str): The model name to use.
            model_path (Optional[str]): Local path to the model.
                Defaults to None.
        """
        assert (
            model_name in self.SUPPORTED_LLM_NAMES
        ), f"Model name {model_name} must be one of {self.SUPPORTED_LLM_NAMES}."
        self.model_name = model_name
        self.model_path = model_path

    @abc.abstractmethod
    def generate_response(self, conv: Conversation, inf_gen_config: InferenceGenerationConfig) -> LLMChatResponse:
        """
        Generate a response for the conversation.

        Args:
            conv (Conversation): The conversation object.
            inf_gen_config (InferenceGenerationConfig): Instance of generation config.

        Returns:
            LLMChatResponse: The response generated by the model.
        """
        pass

    @abc.abstractmethod
    async def batch_generate_response(self, convs: list[Conversation], inf_gen_config: InferenceGenerationConfig) -> list[LLMChatResponse]:
        """
        Generate responses for a batch of conversations.

        Args:
            convs (list[Conversation]): List of conversation objects.
            inf_gen_config (InferenceGenerationConfig): Instance of generation config.
                See `InferenceGenerationConfig` for the default values.

        Returns:
            list[LLMChatResponse]: List of responses generated by the model, one for each conversation.
        """
        pass


class CommonLLMChat(LLMChat):
    """
    Common class for LLM providers that share a common messages format for API calls.
    E.g. OpenAI, TogetherAI, Anthropic.

    Common format is:
    ```
    [
        {"role": role1, "content": [{"type": "text", "text": text1}],
        {"role": role2, "content": [{"type": "text", "text": text2}],
        {"role": role3, "content": [{"type": "text", "text": text3}],
    ]
    ```
    Use `_convert_conv_to_api_format` to convert a `Conversation` into such a list.
    """
    # Rate limits: Requests per minute (RPM) and Tokens per minute (TPM)
    RATE_LIMITS = {
        "model_name": {
            "usage_tier=1": {"RPM": 0, "TPM": 0},
        },
    }
    # NOTE: RPM and TPM limits are set to 0 by default, and should be overridden by the subclass
    # value of 0 indicates no rate limit
    RPM_LIMIT: int = 0
    TPM_LIMIT: int = 0

    def __init__(
        self,
        model_name: str,
        model_path: str | None = None,
    ):
        super().__init__(model_name, model_path)
        self.client = None

        # Utils for rate limiting
        # value is incremented every interval and represents the next time a request can be made
        # value_slow is incremented every minute and represents the next time a new minute starts
        self.start = self.end_rpm = self.end_tpm = time.time()
        # NOTE: we estimate the number of used tokens in the current minute
        self.token_usage_per_minute = 0
        # condition variable for rate limit
        self.cond = asyncio.Condition()

    def _update_rate_limits(self, usage_tier: int) -> None:
        usage_tier_str = f"usage_tier={usage_tier}"
        if usage_tier_str not in self.RATE_LIMITS[self.model_name]:
            raise ValueError(f"Usage tier {usage_tier} not supported for {self.model_name}, please update the class for {self.model_name}.")
        rate_limit_for_usage_tier = self.RATE_LIMITS[self.model_name][f"usage_tier={usage_tier}"]
        self.RPM_LIMIT = rate_limit_for_usage_tier["RPM"]
        self.TPM_LIMIT = rate_limit_for_usage_tier["TPM"]
    def _increment(self):
        """Increment the counter by interval = (60 / RPM) and reset token usage
        """
        now = time.time()
        if now > self.end_rpm:
            self.end_rpm = now + 60 / self.RPM_LIMIT # set the next rpm deadline to be 1 interval from now
        if now > self.end_tpm:
            self.end_tpm = now + 60 # set the next tpm deadline to be 1 minute
            self.token_usage_per_minute = 0
    async def _sleep_rpm(self):
        """Sleep if the RPM limit is exceeded
        """
        remaining = max(self.end_rpm - time.time(), 0)
        logging.debug(f"Sleeping for {remaining} to satisfy RPM limit")
        return await asyncio.sleep(remaining)
    async def _sleep_tpm(self, input_tokens):
        """Sleep if the input_tokens will exceed the TPM limit
        """
        if input_tokens + self.token_usage_per_minute > self.TPM_LIMIT:
            remaining = max(self.end_tpm - time.time(), 0)
            logging.debug(f"Sleeping for {remaining} to satisfy TPM limit")
            await asyncio.sleep(remaining)
            self.token_usage_per_minute = 0 # reset token_usage_per_minute if new minute has started
    def _check(self, input_tokens):
        """Check that the condition is satisfied
        """
        now = time.time()
        logging.debug(f"checking: curr time={now-self.start}, rpm counter={self.end_rpm-self.start}, tpm counter={self.end_tpm-self.start}, token_usage_per_minute={self.token_usage_per_minute}")
        return now >= self.end_rpm and input_tokens + self.token_usage_per_minute <= self.TPM_LIMIT
    def _current(self):
        """Print the current time since start
        """
        return f"curr time={time.time() - self.start}, tokens used={self.token_usage_per_minute}"
    @abc.abstractmethod
    def _count_tokens(self, messages_api_format: list[dict]) -> int:
        """Returns the count of total tokens in the messages, which are in the common format.
        """
        pass

    @abc.abstractmethod
    def _call_api(
        self,
        messages_api_format: list[dict],
        inf_gen_config: InferenceGenerationConfig,
        use_async: bool = False,
    ) -> object:
        """Calls the API to generate a response for the messages. Expects messages ready for API.

        Args:
            messages_api_format (list[dict]): List of messages in the API format.
            inf_gen_config (InferenceGenerationConfig): Instance of generation config.
            use_async (bool): Whether to use the async version of the API. Defaults to False.
        
        Returns:
            object: The response object from the API.
        """
        pass
    @abc.abstractmethod
    def _parse_api_output(self, response: object) -> LLMChatResponse:
        """Parse the response from the API and return the prediction and usage statistics.
        """
        pass
    def _convert_conv_to_api_format(self, conv: Conversation) -> list[dict]:
        """Converts the conversation object to a common format supported by various LLM providers.
        """
        formatted_messages = []
        for message in conv.messages:
            for content in message.content:
                match content:
                    case ContentTextMessage(text=text):
                        formatted_messages.append({"role": message.role, "content": [{"type": "text", "text": text}]})
        return formatted_messages
    
    async def generate_response(self, conv: Conversation, inf_gen_config: InferenceGenerationConfig) -> LLMChatResponse:
        """Async version of generate_response that can be called concurrently while respecting rate limits"""
        messages_api_format: list[dict] = self._convert_conv_to_api_format(conv)
        input_tokens = self._count_tokens(messages_api_format)
        logger.debug(f"Input tokens: {input_tokens}")
        if input_tokens > self.TPM_LIMIT:
            raise ValueError(f"Input tokens {input_tokens} exceed TPM limit {self.TPM_LIMIT}")

        # acquire the lock for the counter
        await self.cond.acquire()
        logging.debug(f"{self._current()}: Acquired lock for {conv.uid}")
        # ensure that counter.check(input_tokens) will be satisfied
        await self._sleep_rpm()
        await self._sleep_tpm(input_tokens)
        try:
            # yield to other threads until condition is true
            await self.cond.wait_for(lambda : self._check(input_tokens))
            # schedule _call_api to run concurrently
            t = asyncio.create_task(self._call_api(messages_api_format, inf_gen_config, use_async=True))
            logging.debug(f"{self._current()}: Done with {conv.uid}")
            self._increment()
            self.token_usage_per_minute += input_tokens
            logging.debug(f"{self._current()}: Updated counter")
            # release underlying lock and wake up 1 waiting task
            self.cond.notify()
            logging.debug(f"{self._current()}: Notified 1")
        finally:
            self.cond.release()
            logging.debug(f"{self._current()}: Released lock for {conv.uid}")
        # wait for the task to complete
        response = await t
        parsed_response = self._parse_api_output(response)
        return parsed_response
    async def batch_generate_response(self, convs: list[Conversation], inf_gen_config: InferenceGenerationConfig) -> list[LLMChatResponse]:
        parsed_responses = await asyncio.gather(*[
            self.generate_response(conv, inf_gen_config) 
            for conv in convs
        ])
        return parsed_responses

class OpenAIChat(CommonLLMChat):
    # https://platform.openai.com/docs/guides/rate-limits/usage-tiers
    RATE_LIMITS = {
        "gpt-4o-mini-2024-07-18": {
            "usage_tier=0": {"RPM": 3, "TPM": 40_000},  # free tier
            "usage_tier=1": {"RPM": 500, "TPM": 200_000},
            "usage_tier=2": {"RPM": 5_000, "TPM": 2_000_000},
            "usage_tier=3": {"RPM": 5_000, "TPM": 4_000_000},
        },
        "gpt-4o-2024-11-20": {
            "usage_tier=1": {"RPM": 500, "TPM": 30_000},
            "usage_tier=2": {"RPM": 5_000, "TPM": 450_000},
            "usage_tier=3": {"RPM": 5_000, "TPM": 800_000},
        },
    }
    SUPPORTED_LLM_NAMES: list[str] = list(RATE_LIMITS.keys())
    
    def __init__(
        self,
        model_name: str,
        model_path: str | None = None,
        usage_tier: int = 1,
    ):
        super().__init__(model_name, model_path)
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.async_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.encoding = tiktoken.encoding_for_model(model_name)
        self._update_rate_limits(usage_tier)

    def _call_api(
        self,
        messages_api_format: list[dict],
        inf_gen_config: InferenceGenerationConfig,
        use_async: bool = False,
    ) -> object:
        # https://platform.openai.com/docs/api-reference/introduction
        # https://platform.openai.com/docs/api-reference/chat
        # https://github.com/openai/openai-python
        client = self.async_client if use_async else self.client
        response = client.chat.completions.create(
            model=self.model_name,
            messages=messages_api_format,
            temperature=inf_gen_config.temperature,
            top_p=inf_gen_config.top_p,
            max_completion_tokens=inf_gen_config.max_tokens,
            seed=inf_gen_config.seed,
            stop=inf_gen_config.stop_sequences,
            # NOTE: top_k is not supported by OpenAI's API
            # NOTE: repetition_penalty is not supported by OpenAI's API
        )
        return response

    def _parse_api_output(self, response: object) -> LLMChatResponse:
        return LLMChatResponse(
            pred=response.choices[0].message.content,
            usage=response.usage.model_dump(),
        )

    def _count_tokens(self, messages_api_format: list[dict]) -> int:
        """
        NOTE: this only counts the tokens in raw string message, 
        not the tokens in the actual prompt to the model,
        which may be different depending on the server-side implementation.
        Compared to the actual token count returned by the API responses, this is a systematic overestimate.

        https://cookbook.openai.com/examples/how_to_count_tokens_with_tiktoken
        """
        texts = [msg["content"][0]["text"] for msg in messages_api_format]
        num_tokens = len(self.encoding.encode("\n".join(texts)))
        return num_tokens
    

class TogetherChat(CommonLLMChat):
    SUPPORTED_LLM_NAMES: list[str] = [
        "meta-llama/meta-llama-3.1-8b-instruct-turbo",
        "meta-llama/meta-llama-3.1-70b-instruct-turbo",
        "meta-llama/llama-3.3-70b-instruct-turbo",
        "meta-llama/meta-llama-3.1-405b-instruct-turbo",
        "meta-llama/llama-vision-free",
        "meta-llama/llama-3.3-70b-instruct-turbo-free",
    ]
    RATE_LIMITS = {
        llm_name: {
            "usage_tier=0": {"RPM": 20, "TPM": 500_000},
            "usage_tier=1": {"RPM": 600, "TPM": 500_000}
        } 
        for llm_name in SUPPORTED_LLM_NAMES
    }

    def __init__(
        self,
        model_name: str,
        model_path: str | None = None,
        usage_tier: int = 1,
    ):
        logging.info("Using TogetherAI for inference")
        super().__init__(model_name, model_path)
        self.client = together.Together(api_key=os.getenv("TOGETHER_API_KEY"))
        self.async_client = together.AsyncTogether(api_key=os.getenv("TOGETHER_API_KEY"))
        self._update_rate_limits(usage_tier)

    def _convert_conv_to_api_format(self, conv: Conversation) -> list[dict]:
        """
        Converts the conversation object to a format supported by Together.
        """
        formatted_messages = []
        for message in conv.messages:
            for content in message.content:
                match content:
                    case ContentTextMessage(text=text):
                        formatted_messages.append({"role": message.role, "content": text})
        return formatted_messages

    def _call_api(
        self,
        messages_api_format: list[dict],
        inf_gen_config: InferenceGenerationConfig,
        use_async: bool = False,
    ) -> object:
        # https://github.com/togethercomputer/together-python
        # https://docs.together.ai/reference/completions-1
        client = self.async_client if use_async else self.client
        response = client.chat.completions.create(
            model=self.model_name,
            messages=messages_api_format,
            temperature=inf_gen_config.temperature,
            top_p=inf_gen_config.top_p,
            top_k=inf_gen_config.top_k,
            repetition_penalty=inf_gen_config.repetition_penalty,
            seed=inf_gen_config.seed,
            max_tokens=inf_gen_config.max_tokens,
            stop=inf_gen_config.stop_sequences,
        )
        return response

    def _parse_api_output(self, response: object) -> LLMChatResponse:
        return LLMChatResponse(
            pred=response.choices[0].message.content,
            usage=response.usage.model_dump(),
        )

    def _count_tokens(self, messages_api_format: list[dict]) -> int:
        # TODO: implement count tokens for llama models
        return 0
        

class AnthropicChat(CommonLLMChat):
    RATE_LIMITS = {
        "claude-3-5-sonnet-20241022": {
            "usage_tier=1": {"RPM": 50, "TPM": 40_000},
            "usage_tier=2": {"RPM": 1_000, "TPM": 80_000},
        },
        "claude-3-5-haiku-20241022": {
            "usage_tier=1": {"RPM": 50, "TPM": 50_000},
            "usage_tier=2": {"RPM": 1_000, "TPM": 100_000},
        },
    }
    SUPPORTED_LLM_NAMES: list[str] = list(RATE_LIMITS.keys())

    def __init__(
        self,
        model_name: str,
        model_path: str | None = None,
        usage_tier: int = 2,
    ):
        super().__init__(model_name, model_path)
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.async_client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self._update_rate_limits(usage_tier)

    def _call_api(
        self,
        messages_api_format: list[dict],
        inf_gen_config: InferenceGenerationConfig,
        use_async: bool = False,
    ) -> object:
        # https://docs.anthropic.com/en/api/migrating-from-text-completions-to-messages
        # https://github.com/anthropics/anthropic-sdk-python?tab=readme-ov-file#async-usage
        # https://docs.anthropic.com/en/api/messages
        client = self.async_client if use_async else self.client

        if isinstance(inf_gen_config.stop_sequences, list) and "\n" in inf_gen_config.stop_sequences:
            # Claude does not accept whitespace stop sequences like "\n".
            # By default, the model will stop at the end of the turn
            inf_gen_config.stop_sequences.remove("\n")

        response = client.messages.create(
            model=self.model_name,
            messages=messages_api_format,
            max_tokens=inf_gen_config.max_tokens,
            temperature=inf_gen_config.temperature,
            top_p=inf_gen_config.top_p,
            top_k=inf_gen_config.top_k,
            stop_sequences=inf_gen_config.stop_sequences,
            # NOTE: repetition_penalty is not supported by Anthropic's API
            # NOTE: seed is not supported by Anthropic's API
        )
        return response

    def _parse_api_output(self, response: object) -> LLMChatResponse:
        return LLMChatResponse(
            pred=response.content[0].text,
            usage=response.usage.model_dump(),
        )

    def _count_tokens(self, messages_api_format: list[dict]) -> int:
        response = self.client.beta.messages.count_tokens(
            model=self.model_name,
            messages=messages_api_format,
        )
        return response.input_tokens


class GeminiChat(CommonLLMChat):
    """
    Overrides the common messages format with the Gemini format:
    ```
    [
        {"role": role1, "parts": text1},
        {"role": role2, "parts": text2},
        {"role": role3, "parts": text3},
    ]
    ```
    """
    RATE_LIMITS = {
        "gemini-1.5-flash-002": {
            "usage_tier=0": {"RPM": 15, "TPM": 1_000_000},  # free tier
            "usage_tier=1": {"RPM": 2_000, "TPM": 4_000_000},
        },
        "gemini-1.5-pro-002": {
            "usage_tier=0": {"RPM": 2, "TPM": 32_000}, # free tier
            "usage_tier=1": {"RPM": 1_000, "TPM": 4_000_000},
        },
        "gemini-1.5-flash-8b-001": {
            "usage_tier=0": {"RPM": 15, "TPM": 1_000_000},  # free tier
            "usage_tier=1": {"RPM": 4_000, "TPM": 4_000_000},
        },
        "gemini-2.0-flash-exp": {
            "usage_tier=0": {"RPM": 10, "TPM": 4_000_000},  # free tier: https://ai.google.dev/gemini-api/docs/models/gemini#gemini-2.0-flash
        }
    }
    SUPPORTED_LLM_NAMES: list[str] = list(RATE_LIMITS.keys())

    def __init__(
        self,
        model_name: str,
        model_path: str | None = None,
        usage_tier: int = 1,
    ):
        super().__init__(model_name, model_path)

        gemini.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.client = gemini.GenerativeModel(self.model_name)
        self._update_rate_limits(usage_tier)

    def _convert_conv_to_api_format(self, conv: Conversation) -> list[dict]:
        # https://ai.google.dev/gemini-api/docs/models/gemini
        # https://github.com/google-gemini/generative-ai-python/blob/main/docs/api/google/generativeai/GenerativeModel.md
        formatted_messages = []
        for message in conv.messages:
            for content in message.content:
                match content:
                    case ContentTextMessage(text=text):
                        role = "model" if message.role == "assistant" else message.role
                        formatted_messages.append({"role": role, "parts": text})
        return formatted_messages

    def _call_api(
        self,
        messages_api_format: list[dict],
        inf_gen_config: InferenceGenerationConfig,
        use_async: bool = False,
    ) -> object:
        client_function = self.client.generate_content_async if use_async else self.client.generate_content
        response = client_function(
            contents=messages_api_format,
            generation_config=gemini.types.GenerationConfig(
                temperature=inf_gen_config.temperature,
                top_p=inf_gen_config.top_p,
                max_output_tokens=inf_gen_config.max_tokens,
                stop_sequences=inf_gen_config.stop_sequences,
                # NOTE: API does not suport topK>40
            ),
        )
        return response

    def _parse_api_output(self, response: object) -> LLMChatResponse:
        # Try to get response text. If failed due to any reason, output empty prediction
        # Example instance why Gemini can fail to return response.text:
        # "The candidate's [finish_reason](https://ai.google.dev/api/generate-content#finishreason) is 4. Meaning that the model was reciting from copyrighted material."
        try:
            pred = response.text
            error = None
        except Exception as e:
            pred = ""
            error = str(e)
        return LLMChatResponse(
            pred=pred,
            usage={
                "prompt_token_count": response.usage_metadata.prompt_token_count,
                "response_token_count": response.usage_metadata.candidates_token_count,
                "total_token_count": response.usage_metadata.total_token_count,
                "cached_content_token_count": response.usage_metadata.cached_content_token_count,
            },
            error=error
        )

    def _count_tokens(self, messages_api_format: list[dict]) -> int:
        response = self.client.count_tokens(messages_api_format)
        return response.total_tokens

    
class VLLMChat(CommonLLMChat):
    SUPPORTED_LLM_NAMES: list[str] = [
        "meta-llama/llama-3.1-8b-instruct", 
        "meta-llama/llama-3.1-70b-instruct", 
        "meta-llama/llama-3.2-1b-instruct",
        "meta-llama/llama-3.2-3b-instruct",
        "meta-llama/llama-3.3-70b-instruct", 
        "microsoft/phi-3.5-mini-instruct",
        "microsoft/phi-3.5-moe-instruct",
        "google/gemma-2-2b-it",
        "google/gemma-2-9b-it",
        "google/gemma-2-27b-it",
        "mistralai/mistral-7b-instruct-v0.3",
        "deepseek-ai/deepseek-r1-distill-qwen-32b",
    ]

    def __init__(
        self,
        model_name: str,
        model_path: str | None = None,
        max_model_len: int | None = None,
        tensor_parallel_size: int | None = None,
        use_api: bool = True,
        port: int = 8000,
    ):
        """
        Args:
            max_model_len (int): Maximum model length for vLLM models.
                Defaults to None.
            tensor_parallel_size (int): Number of GPUs to use for tensor parallelism.
                Defaults to None (uses all available GPUs).
            use_api (bool): Whether to use the vllm server or offline inference
                Defaults to True.
                NOTE: offline inference only works for batch_generate_response
                To maximize performance, set `use_server=False` when running Nshot and CoT agents
            port (int): Port number for the vllm server.
                Defaults to 8000.
        """
        super().__init__(model_name, model_path)
        
        # additional stop token for llama models
        # NOTE: eot = end-of-turn
        if(model_name == "deepseek-ai/deepseek-r1-distill-qwen-32b"):
            self.ADDITIONAL_STOP = ["<｜end▁of▁sentence｜>",]
        else:
            self.ADDITIONAL_STOP = ["<|eot_id|>",]
        
        self.use_api = use_api
        if self.use_api:
            logging.info("Using vLLM server for inference")
            try:
                BASE_URL = f"http://0.0.0.0:{port}/v1"
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
        else:
            logging.info("Using vLLM batched offline inference")
            # vLLM configs
            self.max_model_len = max_model_len
            if tensor_parallel_size is None:
                # NOTE: the reason why we can't use torch.cuda.device_count() is because of some weird bug between torch and vllm,
                # where we can't call `import torch` before instantiating the LLM object
                self.tensor_parallel_size = get_gpu_count()
            else:
                self.tensor_parallel_size = tensor_parallel_size
            # instead of initializing a client, we initialize the LLM object
            # os.environ["CUDA_VISIBLE_DEVICES"] = "1,2" #to avoid bug
            self.llm = LLM(
                model=self.model_name,
                max_model_len=self.max_model_len,
                tensor_parallel_size=self.tensor_parallel_size, 
            )
            # get tokenizer for constructing prompt
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)

    def _convert_conv_to_api_format(self, conv: Conversation) -> list[dict]:
        formatted_messages = []
        for message in conv.messages:
            for content in message.content:
                match content:
                    case ContentTextMessage(text=text):
                        formatted_messages.append({"role": "user", "content": text})
        return formatted_messages

    def _parse_api_output(self, response: object) -> LLMChatResponse:
        """Parse the output of vllm server when using the OpenAI compatible server
        """
        return LLMChatResponse(
            pred=response.choices[0].message.content,
            usage=response.usage.model_dump(),
        )
    
    def _parse_vllm_output(self, response: object) -> LLMChatResponse:
        """Parse output of vllm offline inference when using (batch) offline inference
        """
        return LLMChatResponse(
            pred=response.outputs[0].text,
            usage={
                "prompt_tokens": len(response.prompt_token_ids),
                "completion_tokens": len(response.outputs[0].token_ids),
                "total_tokens": len(response.prompt_token_ids) + len(response.outputs[0].token_ids),
                "cached_tokens": response.num_cached_tokens,
            }
        )

    def _call_api(
        self,
        messages_api_format: list[dict],
        inf_gen_config: InferenceGenerationConfig,
        use_async: bool = False,
    ) -> object:
        # NOTE: vllm implements an OpenAI compatible server
        # https://github.com/openai/openai-python
        assert self.use_api, \
            "This function should not be called when using vllm batched offline inference"
        client = self.async_client if use_async else self.client
        response = client.chat.completions.create(
            model=self.model_name,
            messages=messages_api_format,
            temperature=inf_gen_config.temperature,
            top_p=inf_gen_config.top_p,
            max_completion_tokens=inf_gen_config.max_tokens,
            seed=inf_gen_config.seed,
            stop=inf_gen_config.stop_sequences,
            # NOTE: top_k is not supported by OpenAI's API
            # NOTE: repetition_penalty is not supported by OpenAI's API
        )
        return response

    def generate_response(self, conv: Conversation, inf_gen_config: InferenceGenerationConfig) -> LLMChatResponse:
        assert self.client is not None, "Client is not initialized."
        messages_api_format: list[dict] = self._convert_conv_to_api_format(conv)
        response = self._call_api(messages_api_format, inf_gen_config)
        parsed_response = self._parse_api_output(response)
        return parsed_response

    async def batch_generate_response(self, convs: list[Conversation], inf_gen_config: InferenceGenerationConfig) -> list[LLMChatResponse]:
        if self.use_api:
            # When using api, we can use the parent class implementation
            return await super().batch_generate_response(convs, inf_gen_config)
        else:
            sampling_params = SamplingParams(
                temperature=inf_gen_config.temperature,
                top_p=inf_gen_config.top_p,
                top_k=inf_gen_config.top_k,
                repetition_penalty=inf_gen_config.repetition_penalty,
                stop=inf_gen_config.stop_sequences + self.ADDITIONAL_STOP,
                max_tokens=inf_gen_config.max_tokens,
                seed=inf_gen_config.seed,
            )
            prompts = [
                self.tokenizer.apply_chat_template(
                    self._convert_conv_to_api_format(conv), 
                    tokenize=False, 
                    add_generation_prompt=True
                )
                for conv in convs
            ]
            # save prompts to json file for debugging purposes
            # import json
            # with open(os.path.join('out-test-1220-2', 'prompts.json'), 'w') as f:
            #     json.dump(prompts, f, indent=4)
            responses = self.llm.generate(prompts, sampling_params)
            parsed_responses = [self._parse_vllm_output(response) for response in responses]
            return parsed_responses

    def _count_tokens(self, messages_api_format: list[dict]) -> int:
        """No need to count tokens for vLLM models"""
        return 0


SUPPORTED_LLM_NAMES: list[str] = (
    OpenAIChat.SUPPORTED_LLM_NAMES
    + TogetherChat.SUPPORTED_LLM_NAMES
    + AnthropicChat.SUPPORTED_LLM_NAMES
    + GeminiChat.SUPPORTED_LLM_NAMES
    + VLLMChat.SUPPORTED_LLM_NAMES
)


def get_llm(model_name: str, model_kwargs: dict) -> LLMChat:
    match model_name:
        case model_name if model_name in OpenAIChat.SUPPORTED_LLM_NAMES:
            return OpenAIChat(model_name=model_name, **model_kwargs)
        case model_name if model_name in TogetherChat.SUPPORTED_LLM_NAMES:
            return TogetherChat(model_name=model_name, **model_kwargs)
        case model_name if model_name in GeminiChat.SUPPORTED_LLM_NAMES:
            return GeminiChat(model_name=model_name, **model_kwargs)
        case model_name if model_name in AnthropicChat.SUPPORTED_LLM_NAMES:
            return AnthropicChat(model_name=model_name, **model_kwargs)
        case model_name if model_name in VLLMChat.SUPPORTED_LLM_NAMES:
            return VLLMChat(model_name=model_name, **model_kwargs)
        case _:
            raise ValueError(f"Model name {model_name} must be one of {SUPPORTED_LLM_NAMES}.")
