import abc
import asyncio
import logging
import os
import time
from copy import deepcopy
from typing import Any

import yaml
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_fixed

from phantom_eval._types import ContentTextMessage, Conversation, LLMChatResponse

logger = logging.getLogger(__name__)


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


API_LLMS_CONFIG_FILE = "api_llms_config.yaml"


def load_yaml_config(config_file: str) -> dict[str, Any]:
    """
    Load YAML configuration file.

    Args:
        config_file: Path to the configuration file (relative to this module).
            Defaults to "api_llms_config.yaml".

    Returns:
        Dictionary containing the configuration.
    """
    # Get directory of current file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, config_file)

    try:
        with open(config_path) as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"LLM config file not found at {config_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing LLM config YAML: {e}")


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
    def __init__(
        self,
        model_name: str,
    ):
        """
        Initialize the LLM chat object.

        Args:
            model_name (str): The model name to use.
        """
        self.model_name = model_name

    @abc.abstractmethod
    async def generate_response(
        self, conv: Conversation, inf_gen_config: InferenceGenerationConfig
    ) -> LLMChatResponse:
        """
        Generate a response for the conversation.

        Args:
            conv (Conversation): The conversation object.
            inf_gen_config (InferenceGenerationConfig): Instance of generation config.

        Returns:
            LLMChatResponse: The response generated by the model.
        """

    @abc.abstractmethod
    async def batch_generate_response(
        self, convs: list[Conversation], inf_gen_config: InferenceGenerationConfig
    ) -> list[LLMChatResponse]:
        """
        Generate responses for a batch of conversations.

        Args:
            convs (list[Conversation]): List of conversation objects.
            inf_gen_config (InferenceGenerationConfig): Instance of generation config.
                See `InferenceGenerationConfig` for the default values.

        Returns:
            list[LLMChatResponse]: List of responses generated by the model, one for each conversation.
        """


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
        enforce_rate_limits: bool = False,
    ):
        """
        Initialize the LLM chat object.
        Args:
            model_name (str): The model name to use.
            enforce_rate_limits (bool): Whether to enforce rate limits.
                Defaults to False.
        """
        super().__init__(model_name)
        self.client = None

        # Functionality for enforcing rate limiting on the client side
        self.enforce_rate_limits = enforce_rate_limits
        # end_rpm is incremented every interval and represents the next time a request can be made
        # end_tpm is incremented every minute and represents the next time a new minute starts
        self.start = self.end_rpm = self.end_tpm = time.time()
        # NOTE: we estimate the number of used tokens in the current minute
        self.token_usage_per_minute = 0
        # condition variable for rate limit
        self.cond = asyncio.Condition()

    def _update_rate_limits(self, server: str, model_name: str, usage_tier: int) -> None:
        """
        Load rate limits from config file based on server, model name, and usage tier.

        If the rate limits are not found, set `self.enforce_rate_limits` to False.
        """
        config = load_yaml_config(API_LLMS_CONFIG_FILE)
        tier_key = f"usage_tier={usage_tier}"

        try:
            # Access the configuration using the provider, model name, and usage tier
            rate_limits = config["openai"][model_name][tier_key]
            self.rpm_limit = rate_limits["RPM"]
            self.tpm_limit = rate_limits["TPM"]
        except KeyError:
            logging.info(
                f"Rate limits not found for {server} server, model name={self.model_name} with {tier_key}."
                " Rate limits will not be enforced."
            )
            self.enforce_rate_limits = False

    def _increment(self):
        """Increment the counter by interval = (60 / RPM) and reset token usage"""
        now = time.time()
        if now > self.end_rpm:
            self.end_rpm = now + 60 / self.RPM_LIMIT  # set the next rpm deadline to be 1 interval from now
        if now > self.end_tpm:
            self.end_tpm = now + 60  # set the next tpm deadline to be 1 minute
            self.token_usage_per_minute = 0

    async def _sleep_rpm(self):
        """Sleep if the RPM limit is exceeded"""
        remaining = max(self.end_rpm - time.time(), 0)
        logging.debug(f"Sleeping for {remaining} to satisfy RPM limit")
        return await asyncio.sleep(remaining)

    async def _sleep_tpm(self, input_tokens):
        """Sleep if the input_tokens will exceed the TPM limit"""
        if input_tokens + self.token_usage_per_minute > self.TPM_LIMIT:
            remaining = max(self.end_tpm - time.time(), 0)
            logging.debug(f"Sleeping for {remaining} to satisfy TPM limit")
            await asyncio.sleep(remaining)
            self.token_usage_per_minute = 0  # reset token_usage_per_minute if new minute has started

    def _check(self, input_tokens):
        """Check that the condition is satisfied"""
        now = time.time()
        logging.debug(
            f"checking: curr time={now-self.start}, rpm counter={self.end_rpm-self.start}, "
            f"tpm counter={self.end_tpm-self.start}, token_usage_per_minute={self.token_usage_per_minute}"
        )
        return now >= self.end_rpm and input_tokens + self.token_usage_per_minute <= self.TPM_LIMIT

    def _current(self):
        """Print the current time since start"""
        return f"curr time={time.time() - self.start}, tokens used={self.token_usage_per_minute}"

    @abc.abstractmethod
    def _call_api(
        self,
        messages_api_format: list[dict],
        inf_gen_config: InferenceGenerationConfig,
        use_async: bool = False,
    ) -> object:
        """
        Calls the API to generate a response for the messages. Expects messages ready for API.

        Args:
            messages_api_format (list[dict]): List of messages in the API format.
            inf_gen_config (InferenceGenerationConfig): Instance of generation config.
            use_async (bool): Whether to use the async version of the API. Defaults to False.

        Returns:
            object: The response object from the API.
        """

    @abc.abstractmethod
    def _parse_api_output(self, response: object) -> LLMChatResponse:
        """
        Parse the response from the API and return the prediction and usage statistics.
        """

    @abc.abstractmethod
    def _count_tokens(self, messages_api_format: list[dict]) -> int:
        """
        Returns the count of total tokens in the messages, which are in the common format.
        """

    def _convert_conv_to_api_format(self, conv: Conversation) -> list[dict]:
        """
        Converts the conversation object to a common format supported by various LLM providers.
        """
        formatted_messages = []
        for message in conv.messages:
            for content in message.content:
                match content:
                    case ContentTextMessage(text=text):
                        formatted_messages.append(
                            {"role": message.role, "content": [{"type": "text", "text": text}]}
                        )
        return formatted_messages

    async def generate_response_with_rate_limits(
        self, conv: Conversation, inf_gen_config: InferenceGenerationConfig
    ) -> LLMChatResponse:
        """Async version of generate_response that respects rate limits"""
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
            await self.cond.wait_for(lambda: self._check(input_tokens))
            # schedule _call_api to run concurrently
            logging.debug(f"{self._current()}: Calling API for {conv.uid}")
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

    async def generate_response(
        self, conv: Conversation, inf_gen_config: InferenceGenerationConfig
    ) -> LLMChatResponse:
        """Async version of generate_response that can be called concurrently to respect rate limits

        If self.enforce_rate_limits is True, this function will enforce the rate limits
        by acquiring a lock and waiting for the condition to be satisfied.
        Otherwise, it will call the API directly.
        """
        if self.enforce_rate_limits:
            return await self.generate_response_with_rate_limits(conv, inf_gen_config)
        else:
            # max_retries and wait_seconds are object attributes, and cannot be written around the
            # generate_response function
            # So we need to wrap the _call_api function with the retry decorator
            @retry(
                stop=stop_after_attempt(inf_gen_config.max_retries),
                wait=wait_fixed(inf_gen_config.wait_seconds),
            )
            def _call_api_wrapper() -> str:
                messages_api_format: list[dict] = self._convert_conv_to_api_format(conv)
                response = self._call_api(messages_api_format, inf_gen_config)
                parsed_response = self._parse_api_output(response)
                return parsed_response

            return _call_api_wrapper()

    async def batch_generate_response(
        self, convs: list[Conversation], inf_gen_config: InferenceGenerationConfig
    ) -> list[LLMChatResponse]:
        parsed_responses = await asyncio.gather(
            *[self.generate_response_with_rate_limits(conv, inf_gen_config) for conv in convs]
        )
        return parsed_responses
