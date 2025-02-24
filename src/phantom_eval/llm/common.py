import abc
import asyncio
import logging
import time
from copy import deepcopy

from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_fixed
from tqdm import tqdm

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
        strict_model_name: bool = True,
    ):
        """
        Initialize the LLM chat object.

        Args:
            model_name (str): The model name to use.
            model_path (Optional[str]): Local path to the model.
                Defaults to None.
            strict_model_name (bool): Whether to check if the model name is supported.
                Defaults to True.
        """
        if strict_model_name:
            assert (
                model_name in self.SUPPORTED_LLM_NAMES
            ), f"Model name {model_name} must be one of {self.SUPPORTED_LLM_NAMES}."
        else:
            if model_name not in self.SUPPORTED_LLM_NAMES:
                logger.warning(
                    f"Model name {model_name} is not in the supported list {self.SUPPORTED_LLM_NAMES}."
                )
        self.model_name = model_name
        self.model_path = model_path

    @abc.abstractmethod
    def generate_response(
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
        model_path: str | None = None,
        strict_model_name: bool = True,
    ):
        super().__init__(model_name, model_path, strict_model_name)
        self.client = None

    def _update_rate_limits(self, usage_tier: int) -> None:
        usage_tier_str = f"usage_tier={usage_tier}"
        if usage_tier_str not in self.RATE_LIMITS[self.model_name]:
            raise ValueError(
                f"Usage tier {usage_tier} not supported for {self.model_name}, "
                f"please update the class for {self.model_name}."
            )
        rate_limit_for_usage_tier = self.RATE_LIMITS[self.model_name][f"usage_tier={usage_tier}"]
        self.RPM_LIMIT = rate_limit_for_usage_tier["RPM"]
        self.TPM_LIMIT = rate_limit_for_usage_tier["TPM"]

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

    def generate_response(
        self, conv: Conversation, inf_gen_config: InferenceGenerationConfig
    ) -> LLMChatResponse:
        assert self.client is not None, "Client is not initialized."

        # max_retries and wait_seconds are object attributes, and cannot be written around the
        # generate_response function
        # So we need to wrap the _call_api function with the retry decorator
        @retry(
            stop=stop_after_attempt(inf_gen_config.max_retries), wait=wait_fixed(inf_gen_config.wait_seconds)
        )
        def _call_api_wrapper() -> str:
            messages_api_format: list[dict] = self._convert_conv_to_api_format(conv)
            response = self._call_api(messages_api_format, inf_gen_config)
            parsed_response = self._parse_api_output(response)
            return parsed_response

        return _call_api_wrapper()

    async def _async_chat_completion(
        self, batch_messages_api_format: list[list[dict]], inf_gen_config: InferenceGenerationConfig
    ) -> list[object]:
        """
        Generate responses for a batch of formatted conversations using asynchronous API calls, and return a
        batch of response objects.
        Accounts for rate limits by sleeping between requests.
        """
        assert self.RPM_LIMIT >= 0, "RPM_LIMIT must be greater than 0 (or 0 if no rate limit)"
        assert self.TPM_LIMIT >= 0, "TPM_LIMIT must be greater than 0 (or 0 if no rate limit)"
        tasks = []

        start = time.time()
        token_usage_per_minute = 0  # NOTE: we estimate the number of used tokens in the current minute

        for i, messages_api_format in tqdm(
            enumerate(batch_messages_api_format), total=len(batch_messages_api_format)
        ):
            logger.debug(f"{time.time()-start}: Requesting message {i}")
            input_tokens = self._count_tokens(messages_api_format)
            logger.debug(f"Input tokens: {input_tokens}")
            token_usage_per_minute += input_tokens

            # check if we need to sleep to respect the TPM rate limit
            remaining = 60 - (time.time() - start)  # number of seconds remaining in the current minute
            if self.TPM_LIMIT and token_usage_per_minute > self.TPM_LIMIT and remaining > 0:
                logger.info(f"Token usage per minute: {token_usage_per_minute}")
                logger.info(f"Sleeping for {remaining} seconds to respect the TPM rate limit")
                await asyncio.sleep(
                    remaining + 1
                )  # NOTE: add an extra second so we definitely pass the minute

            # reset if we have passed the minute
            if time.time() - start > 60:
                start = time.time()
                token_usage_per_minute = 0

            t = self._call_api(messages_api_format, inf_gen_config, use_async=True)
            tasks.append(asyncio.create_task(t))
            # Sleep to respect the rate limit
            if self.RPM_LIMIT:
                await asyncio.sleep(60 / self.RPM_LIMIT)

        logger.debug(f"{time.time()-start}: Waiting for responses")
        responses = await asyncio.gather(*tasks)
        logger.debug(f"{time.time()-start}: Got all responses")
        return responses

    async def batch_generate_response(
        self, convs: list[Conversation], inf_gen_config: InferenceGenerationConfig
    ) -> list[LLMChatResponse]:
        batch_messages_api_format = [self._convert_conv_to_api_format(conv) for conv in convs]
        responses = await self._async_chat_completion(batch_messages_api_format, inf_gen_config)
        parsed_responses = [self._parse_api_output(response) for response in responses]
        return parsed_responses
