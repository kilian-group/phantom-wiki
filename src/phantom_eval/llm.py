import abc
import os
import time
from tqdm import tqdm
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


class LLMChat(abc.ABC):
    SUPPORTED_LLM_NAMES: list[str] = []

    def __init__(
        self,
        model_name: str,
        model_path: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        top_p: float = 0.7,
        top_k: int = 50,
        repetition_penalty: float = 1.0,
        max_retries: int = 3,
        wait_seconds: int = 2,
    ):
        """
        Initialize the LLM chat object.

        Args:
            model_name (str): The model name to use.
            model_path (Optional[str]): Local path to the model.
                Defaults to None.
            max_tokens (int): Maximum number of tokens to generate.
                Defaults to 4096.
            temperature (Optional[float]): Temperature parameter for sampling.
                Defaults to 0.0.
            top_p (Optional[float]): top-p parameter for sampling (between 0 and 1)
                Defaults to 0.7
            top_k (Optional[int]): top-k parameter for sampling (> 1)
                Defaults to 50
            repetition_penalty (Optional[int]): repetition parameter (between -1 and 1)
                NOTE: Only supported for some models
                Defaults to 1.0
            max_retries (Optional[int]): Max number of API calls allowed before giving up.
                Defaults to 3.
            wait_seconds (Optional[int]): Number of seconds to wait between API calls.
                Defaults to 2.
        """
        assert (
            model_name in self.SUPPORTED_LLM_NAMES
        ), f"Model name {model_name} must be one of {self.SUPPORTED_LLM_NAMES}."
        self.model_name = model_name
        self.model_path = model_path
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.repetition_penalty = repetition_penalty
        self.max_retries = max_retries
        self.wait_seconds = wait_seconds

        self.model_kwargs = dict(
            model_path=model_path,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            repetition_penalty=repetition_penalty,
            max_retries=max_retries,
            wait_seconds=wait_seconds,
        )

    @abc.abstractmethod
    def generate_response(self, conv: Conversation, stop_sequences: list[str] | None = None, seed: int = 1) -> LLMChatResponse:
        """
        Generate a response for the conversation.

        Args:
            conv (Conversation): The conversation object.
            stop_sequences (Optional[list[str]]): List of stop words to pause generating. Used if the API supports it.
                Defaults to None.
            seed (int): Seed for random number generator, passed to the model if applicable.
                Defaults to 1.

        Returns:
            LLMChatResponse: The response generated by the model.
        """
        pass

    @abc.abstractmethod
    async def batch_generate_response(self, convs: list[Conversation], stop_sequences: list[str] | None = None, seed: int = 1) -> list[LLMChatResponse]:
        """
        Generate responses for a batch of conversations.

        Args:
            convs (list[Conversation]): List of conversation objects.
            stop_sequences (Optional[list[str]]): List of stop words to pause generating. Used if the API supports it.
                Defaults to None.
            seed (int): Seed for random number generator, passed to the model if applicable.
                Defaults to 1.

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
    RPM_LIMIT: int = 0
    TPM_LIMIT: int = 0

    def __init__(
        self,
        model_name: str,
        model_path: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        top_p: float = 0.7,
        top_k: int = 50,
        repetition_penalty: float = 1.0,
        max_retries: int = 3,
        wait_seconds: int = 2,
    ):
        super().__init__(model_name, model_path, max_tokens, temperature, top_p, top_k, repetition_penalty, max_retries, wait_seconds)
        self.client = None

    def _update_rate_limits(self, usage_tier: int) -> None:
        rate_limit_for_usage_tier = self.RATE_LIMITS[self.model_name][f"usage_tier={usage_tier}"]
        self.RPM_LIMIT = rate_limit_for_usage_tier["RPM"]
        self.TPM_LIMIT = rate_limit_for_usage_tier["TPM"]

    @abc.abstractmethod
    def _call_api(
        self,
        messages_api_format: list[dict],
        stop_sequences: list[str] | None = None,
        use_async: bool = False,
        seed: int = 1
    ) -> object:
        """
        Calls the API to generate a response for the messages. Expects messages ready for API.

        Args:
            messages_api_format (list[dict]): List of messages in the API format.
            stop_sequences (Optional[list[str]]): List of stop words to pause generating. Used if the API supports it.
                Defaults to None.
            use_async (bool): Whether to use the async version of the API. Defaults to False.
            seed (int): Seed for random number generator, passed to the model if applicable.
                Defaults to 1.
        
        Returns:
            object: The response object from the API.
        """
        pass
    
    @abc.abstractmethod
    def _parse_api_output(self, response: object) -> LLMChatResponse:
        """
        Parse the response from the API and return the prediction and usage statistics.
        """
        pass

    @abc.abstractmethod
    def _count_tokens(self, messages_api_format: list[dict]) -> int:
        """
        Returns the count of total tokens in the messages, which are in the common format.
        """
        pass

    def _convert_conv_to_api_format(self, conv: Conversation) -> list[dict]:
        """
        Converts the conversation object to a common format supported by various LLM providers.
        """
        formatted_messages = []
        for message in conv.messages:
            for content in message.content:
                match content:
                    case ContentTextMessage(text=text):
                        formatted_messages.append({"role": message.role, "content": [{"type": "text", "text": text}]})
        return formatted_messages

    def generate_response(self, conv: Conversation, stop_sequences: list[str] | None = None, seed: int = 1) -> LLMChatResponse:
        assert self.client is not None, "Client is not initialized."

        # max_retries and wait_seconds are object attributes, and cannot be written around the generate_response function
        # So we need to wrap the _call_api function with the retry decorator
        @retry(stop=stop_after_attempt(self.max_retries), wait=wait_fixed(self.wait_seconds))
        def _call_api_wrapper() -> str:
            messages_api_format: list[dict] = self._convert_conv_to_api_format(conv)
            response = self._call_api(messages_api_format, stop_sequences=stop_sequences, seed=seed)
            parsed_response = self._parse_api_output(response)
            return parsed_response

        return _call_api_wrapper()
    
    async def _async_chat_completion(self, batch_messages_api_format: list[list[dict]], stop_sequences: list[str] | None = None, seed: int = 1) -> list[object]:
        """
        Generate responses for a batch of formatted conversations using asynchronous API calls, and return a batch of response objects.
        Accounts for rate limits by sleeping between requests.
        """
        assert self.RPM_LIMIT > 0, "RPM_LIMIT must be greater than 0"
        assert self.TPM_LIMIT > 0, "TPM_LIMIT must be greater than 0"
        tasks = []

        start = time.time()
        token_usage_per_minute = 0 # NOTE: we estimate the number of used tokens in the current minute
        
        for i, messages_api_format in tqdm(enumerate(batch_messages_api_format), total=len(batch_messages_api_format)):
            logger.debug(f"{time.time()-start}: Requesting message {i}")
            input_tokens = self._count_tokens(messages_api_format)
            logger.debug(f"Input tokens: {input_tokens}")
            token_usage_per_minute += input_tokens

            # check if we need to sleep to respect the TPM rate limit
            remaining = 60 - (time.time() - start) # number of seconds remaining in the current minute
            if token_usage_per_minute > self.TPM_LIMIT and remaining > 0:
                logger.info(f"Token usage per minute: {token_usage_per_minute}")
                logger.info(f"Sleeping for {remaining} seconds to respect the TPM rate limit")
                await asyncio.sleep(remaining + 1) # NOTE: add an extra second so we definitely pass the minute
            
            # reset if we have passed the minute
            if time.time() - start > 60:
                start = time.time()
                token_usage_per_minute = 0

            t = self._call_api(
                messages_api_format=messages_api_format, 
                stop_sequences=stop_sequences, 
                use_async=True, 
                seed=seed, 
            )
            tasks.append(asyncio.create_task(t))
            # Sleep to respect the rate limit
            await asyncio.sleep(60 / self.RPM_LIMIT)
        
        logger.debug(f"{time.time()-start}: Waiting for responses")
        responses = await asyncio.gather(*tasks)
        logger.debug(f"{time.time()-start}: Got all responses")
        return responses
    
    async def batch_generate_response(self, convs: list[Conversation], stop_sequences: list[str] | None = None, seed: int = 1) -> list[LLMChatResponse]:
        batch_messages_api_format = [self._convert_conv_to_api_format(conv) for conv in convs]
        responses = await self._async_chat_completion(batch_messages_api_format, stop_sequences=stop_sequences, seed=seed)
        parsed_responses = [self._parse_api_output(response) for response in responses]
        return parsed_responses


class OpenAIChat(CommonLLMChat):
    RATE_LIMITS = {
        "gpt-4o-mini-2024-07-18": {
            "usage_tier=1": {"RPM": 500, "TPM": 200_000},
        },
        "gpt-4o-2024-11-20": {
            "usage_tier=1": {"RPM": 500, "TPM": 30_000},
        },
    }
    SUPPORTED_LLM_NAMES: list[str] = list(RATE_LIMITS.keys())
    
    def __init__(
        self,
        model_name: str,
        model_path: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        top_p: float = 0.7,
        top_k: int = 50,
        repetition_penalty: float = 1.0,
        max_retries: int = 3,
        wait_seconds: int = 2,
        usage_tier: int = 1,
        use_api: bool = True,
    ):
        super().__init__(model_name, model_path, max_tokens, temperature, top_p, top_k, repetition_penalty, max_retries, wait_seconds)
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.async_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.encoding = tiktoken.encoding_for_model(model_name)
        self._update_rate_limits(usage_tier)

    def _call_api(self, messages_api_format: list[dict], stop_sequences: list[str] | None = None, use_async: bool = False, seed: int = 1) -> object:
        # https://platform.openai.com/docs/api-reference/introduction
        # https://platform.openai.com/docs/api-reference/chat
        # https://github.com/openai/openai-python
        client = self.async_client if use_async else self.client
        response = client.chat.completions.create(
            model=self.model_name,
            messages=messages_api_format,
            temperature=self.temperature,
            top_p=self.top_p,
            max_completion_tokens=self.max_tokens,
            seed=seed,
            stop=stop_sequences,
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
        "together:meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        "together:meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        "together:meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
        "together:meta-llama/Llama-Vision-Free",
    ]
    RATE_LIMITS = {llm_name: {"usage_tier=1": {"RPM": 20, "TPM": 500_000}} for llm_name in SUPPORTED_LLM_NAMES}

    def __init__(
        self,
        model_name: str,
        model_path: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        top_p: float = 0.7,
        top_k: int = 50,
        repetition_penalty: float = 1.0,
        max_retries: int = 3,
        wait_seconds: int = 2,
        usage_tier: int = 1,
        use_api: bool = True,
    ):
        assert model_name.startswith("together:"), "model_name must start with 'together:'"
        super().__init__(model_name, model_path, max_tokens, temperature, top_p, top_k, repetition_penalty, max_retries, wait_seconds)
        self.client = together.Together(api_key=os.getenv("TOGETHER_API_KEY"))
        self.async_client = together.AsyncTogether(api_key=os.getenv("TOGETHER_API_KEY"))
        self._update_rate_limits(usage_tier)

    def _call_api(self, messages_api_format: list[dict], stop_sequences: list[str] | None = None, use_async: bool = False, seed: int = 1) -> str:
        # https://github.com/togethercomputer/together-python
        # https://docs.together.ai/reference/completions-1
        # Remove the "together:" prefix before setting up the client
        client = self.async_client if use_async else self.client
        response = client.chat.completions.create(
            model=self.model_name[len("together:") :],
            messages=messages_api_format,
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            repetition_penalty=self.repetition_penalty,
            seed=seed,
            max_tokens=self.max_tokens,
            stop=stop_sequences,
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
            "usage_tier=2": {"RPM": 1_000, "TPM": 80_000},
        },
        "claude-3-5-haiku-20241022": {
            "usage_tier=2": {"RPM": 1_000, "TPM": 100_000},
        },
    }
    SUPPORTED_LLM_NAMES: list[str] = list(RATE_LIMITS.keys())

    def __init__(
        self,
        model_name: str,
        model_path: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        top_p: float = 0.7,
        top_k: int = 50,
        repetition_penalty: float = 1.0,
        max_retries: int = 3,
        wait_seconds: int = 2,
        usage_tier: int = 2,
        use_api: bool = True,
    ):
        super().__init__(model_name, model_path, max_tokens, temperature, top_p, top_k, repetition_penalty, max_retries, wait_seconds)
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.async_client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self._update_rate_limits(usage_tier)

    def _call_api(self, messages_api_format: list[dict], stop_sequences: list[str] | None = None, use_async: bool = False, seed: int = 1) -> object:
        # https://docs.anthropic.com/en/api/migrating-from-text-completions-to-messages
        # https://github.com/anthropics/anthropic-sdk-python?tab=readme-ov-file#async-usage
        # https://docs.anthropic.com/en/api/messages
        client = self.async_client if use_async else self.client

        if isinstance(stop_sequences, list) and '\n' in stop_sequences:
            # Claude does not accept whitespace stop sequences like "\n".
            # By default, the model will stop at the end of the turn
            raise ValueError("Anthropic's API does not support '\n' in stop_sequences.")

        response = client.messages.create(
            model=self.model_name,
            messages=messages_api_format,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            stop_sequences=stop_sequences,
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
            betas=["token-counting-2024-11-01"],
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
            "usage_tier=1": {"RPM": 15, "TPM": 1_000_000},
        },
        "gemini-1.5-pro-002": {
            "usage_tier=1": {"RPM": 2, "TPM": 32_000},
        },
        "gemini-1.5-flash-8b-001": {
            "usage_tier=1": {"RPM": 15, "TPM": 1_000_000},
        },
        "gemini-2.0-flash-exp": {
            "usage_tier=1": {"RPM": 10, "TPM": 4_000_000}, # https://ai.google.dev/gemini-api/docs/models/gemini#gemini-2.0-flash
        }
    }
    SUPPORTED_LLM_NAMES: list[str] = list(RATE_LIMITS.keys())

    def __init__(
        self,
        model_name: str,
        model_path: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        top_p: float = 0.7,
        top_k: int = 50,
        repetition_penalty: float = 1.0,
        max_retries: int = 3,
        wait_seconds: int = 2,
        usage_tier: int = 1,
        use_api: bool = True,
    ):
        super().__init__(model_name, model_path, max_tokens, temperature, top_p, top_k, repetition_penalty, max_retries, wait_seconds)

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

    def _call_api(self, messages_api_format: list[dict], stop_sequences: list[str] | None = None, use_async: bool = False, seed: int = 1) -> object:
        client_function = self.client.generate_content_async if use_async else self.client.generate_content
        response = client_function(
            contents=messages_api_format,
            generation_config=gemini.types.GenerationConfig(
                temperature=self.temperature,
                top_p=self.top_p,
                # NOTE: API does not suport topK>40
                max_output_tokens=self.max_tokens,
                stop_sequences=stop_sequences,
            ),
        )
        return response

    def _parse_api_output(self, response: object) -> LLMChatResponse:
        return LLMChatResponse(
            pred=response.text,
            usage={
                "prompt_token_count": response.usage_metadata.prompt_token_count,
                "response_token_count": response.usage_metadata.candidates_token_count,
                "total_token_count": response.usage_metadata.total_token_count,
                "cached_content_token_count": response.usage_metadata.cached_content_token_count,
            },
        )

    def _count_tokens(self, messages_api_format: list[dict]) -> int:
        response = self.client.count_tokens(messages_api_format)
        return response.total_tokens

    
class VLLMChat(CommonLLMChat):
    SUPPORTED_LLM_NAMES: list[str] = [
        "meta-llama/llama-3.1-8b-instruct", 
        "meta-llama/llama-3.1-70b-instruct", 
        "microsoft/phi-3.5-mini-instruct",
        "microsoft/phi-3.5-moe-instruct",
        "google/gemma-2-2b-it",
        "google/gemma-2-9b-it",
        "google/gemma-2-27b-it",
        "mistralai/mistral-7b-instruct-v0.3",
    ]
    # additional stop token for llama models
    # NOTE: eot = end-of-turn
    ADDITIONAL_STOP = ["<|eot_id|>",]

    def __init__(
        self,
        model_name: str,
        model_path: str | None = None,
        max_tokens: int = 512,
        temperature: float = 0.0,
        top_p: float = 0.7,
        top_k: int = 50,
        repetition_penalty: float = 1.0,
        max_retries: int = 3,
        wait_seconds: int = 2,
        max_model_len: int | None = None,
        tensor_parallel_size: int | None = None,
        use_api: bool = True,
    ):
        """
        Additional args:
            use_api: whether to use the vllm server or offline inference
                NOTE: offline inference only works for batch_generate_response
                To maximize performance, set `use_server=False` when running Nshot and CoT agents
        """
        super().__init__(model_name, model_path, max_tokens, temperature, top_p, top_k, repetition_penalty, max_retries, wait_seconds)
        
        self.use_api = use_api
        if use_api:
            logging.info("Using vLLM server for inference")
            try:
                BASE_URL = "http://0.0.0.0:8000/v1", # TODO: allow this to be specified by the user
                API_KEY="token-abc123", # TODO: allow this to be specified by the user
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
            self.llm = LLM(
                model=model_name,
                max_model_len=max_model_len,
                tensor_parallel_size=self.tensor_parallel_size,
            )
            # get tokenizer for constructing prompt
            self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

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

    def _call_api(self, messages_api_format: list[dict], stop_sequences: list[str] | None = None, use_async: bool = False, seed: int = 1) -> object:
        # NOTE: vllm implements an OpenAI compatible server
        # https://github.com/openai/openai-python
        assert self.use_api, \
            "This function should not be called when using vllm batched offline inference"
        client = self.async_client if use_async else self.client
        response = client.chat.completions.create(
            model=self.model_name,
            messages=messages_api_format,
            temperature=self.temperature,
            top_p=self.top_p,
            max_completion_tokens=self.max_tokens,
            seed=seed,
            stop=stop_sequences,
            # NOTE: top_k is not supported by OpenAI's API
            # NOTE: repetition_penalty is not supported by OpenAI's API
        )
        return response

    def generate_response(self, conv: Conversation, stop_sequences: list[str] | None = None, seed: int = 1) -> LLMChatResponse:
        assert self.client is not None, "Client is not initialized."
        messages_api_format: list[dict] = self._convert_conv_to_api_format(conv)
        response = self._call_api(messages_api_format, stop_sequences=stop_sequences, seed=seed)
        parsed_response = self._parse_api_output(response)
        return parsed_response

    async def batch_generate_response(self, convs: list[Conversation], stop_sequences: list[str] | None = None, seed: int = 1) -> list[LLMChatResponse]:
        if self.use_api:
            # When using api, we can use the parent class implementation
            return super().batch_generate_response(convs, stop_sequences, seed)
        else:
            sampling_params = SamplingParams(
                temperature=self.temperature,
                top_p=self.top_p,
                top_k=self.top_k,
                repetition_penalty=self.repetition_penalty,
                stop=stop_sequences + self.ADDITIONAL_STOP,
                max_tokens=self.max_tokens,
                seed=seed,
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
            import json
            with open(os.path.join('out-test-1220-2', 'prompts.json'), 'w') as f:
                json.dump(prompts, f, indent=4)
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
SUPPORTED_LOCAL_LLM_NAMES: list[str] = VLLMChat.SUPPORTED_LLM_NAMES


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
