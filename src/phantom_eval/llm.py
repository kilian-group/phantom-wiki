import abc
import os

import anthropic
import openai
import together
import google.generativeai as gemini
from tenacity import retry, stop_after_attempt, wait_fixed

from .data import ContentTextMessage, Conversation


class LLMChat(abc.ABC):
    SUPPORTED_LLM_NAMES: list[str] = []

    def __init__(
        self,
        model_name: str,
        model_path: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        seed: int = 0,
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
            seed (Optional[int]): Seed for random number generator, passed to the model if applicable.
                Defaults to 0.
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
        self.seed = seed
        self.max_retries = max_retries
        self.wait_seconds = wait_seconds

        self.model_kwargs = dict(
            model_path=model_path,
            max_tokens=max_tokens,
            temperature=temperature,
            seed=seed,
            max_retries=max_retries,
            wait_seconds=wait_seconds,
        )

    @abc.abstractmethod
    def generate_response(self, conv: Conversation, stop_sequences: list[str] | None = None) -> str:
        """
        Generate a response for the conversation.

        Args:
            conv (Conversation): The conversation object.
            stop_sequences (Optional[list[str]]): List of stop words to pause generating. Used if the API supports it.
                Defaults to None.

        Returns:
            str: The response generated by the model.
        """
        pass


class CommonLLMChat(LLMChat):
    def __init__(
        self,
        model_name: str,
        model_path: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        seed: int = 0,
        max_retries: int = 3,
        wait_seconds: int = 2,
    ):
        super().__init__(model_name, model_path, max_tokens, temperature, seed, max_retries, wait_seconds)
        self.client = None

    @abc.abstractmethod
    def _call_api(self, messages_api_format: list[dict], stop_sequences: list[str] | None = None) -> str:
        """
        Expects messages ready for API. Use `convert_conv_to_api_format` to convert a conversation
        into such a list.
        """
        pass

    def _convert_conv_to_api_format(self, conv: Conversation) -> list[dict]:
        """
        Converts the conversation object to a common format supported by various LLM providers.
        Common format is:
        ```
        [
            {"role": role1, "content": [{"type": "text", "text": text1},
            {"role": role2, "content": [{"type": "text", "text": text2},
            {"role": role3, "content": [{"type": "text", "text": text3},
        ]
        ```
        """
        formatted_messages = []
        for message in conv.messages:
            for content in message.content:
                match content:
                    case ContentTextMessage(text=text):
                        formatted_messages.append({"role": message.role, "content": [{"type": "text", "text": text}]})
        return formatted_messages

    def generate_response(self, conv: Conversation, stop_sequences: list[str] | None = None) -> str:
        """
        Generate response for the conversation.
        """
        assert self.client is not None, "Client is not initialized."

        # max_retries and wait_seconds are object attributes, and cannot be written around the generate_response function
        # So we need to wrap the _call_api function with the retry decorator
        @retry(stop=stop_after_attempt(self.max_retries), wait=wait_fixed(self.wait_seconds))
        def _call_api_wrapper(conv: Conversation, stop_sequences) -> str:
            messages_api_format: list[dict] = self._convert_conv_to_api_format(conv)
            return self._call_api(messages_api_format, stop_sequences=stop_sequences)

        return _call_api_wrapper(conv, stop_sequences)


class OpenAIChat(CommonLLMChat):
    SUPPORTED_LLM_NAMES: list[str] = [
        "gpt-4o-mini-2024-07-18",
        "gpt-4o-2024-11-20",
    ]

    def __init__(
        self,
        model_name: str,
        model_path: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        seed: int = 0,
        max_retries: int = 3,
        wait_seconds: int = 2,
    ):
        super().__init__(model_name, model_path, max_tokens, temperature, seed, max_retries, wait_seconds)
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def _call_api(self, messages_api_format: list[dict], stop_sequences: list[str] | None = None) -> str:
        # https://platform.openai.com/docs/api-reference/introduction
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages_api_format,
            temperature=self.temperature,
            max_completion_tokens=self.max_tokens,
            seed=self.seed,
            stop=stop_sequences,
        )
        return completion.choices[0].message.content


class TogetherChat(CommonLLMChat):
    SUPPORTED_LLM_NAMES: list[str] = [
        "together:meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        "together:meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        "together:meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
        "together:meta-llama/Llama-Vision-Free",
    ]

    def __init__(
        self,
        model_name: str,
        model_path: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        seed: int = 0,
        max_retries: int = 3,
        wait_seconds: int = 2,
    ):
        assert model_name.startswith("together:"), "model_name must start with 'together:'"
        super().__init__(model_name, model_path, max_tokens, temperature, seed, max_retries, wait_seconds)
        self.client = together.Together(api_key=os.getenv("TOGETHER_API_KEY"))

    def _call_api(self, messages_api_format: list[dict], stop_sequences: list[str] | None = None) -> str:
        # https://github.com/togethercomputer/together-python
        # Remove the "together:" prefix before setting up the client
        completion = self.client.chat.completions.create(
            model=self.model_name[len("together:") :],
            messages=messages_api_format,
            temperature=self.temperature,
            seed=self.seed,
            max_tokens=self.max_tokens,
            stop=stop_sequences,
        )
        return completion.choices[0].message.content


class AnthropicChat(CommonLLMChat):
    SUPPORTED_LLM_NAMES: list[str] = [
        "claude-3-5-haiku-20241022",
        "claude-3-5-sonnet-20241022",
    ]

    def __init__(
        self,
        model_name: str,
        model_path: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        seed: int = 0,
        max_retries: int = 3,
        wait_seconds: int = 2,
    ):
        super().__init__(model_name, model_path, max_tokens, temperature, seed, max_retries, wait_seconds)
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def _call_api(self, messages_api_format: list[dict], stop_sequences: list[str] | None = None) -> str:
        # https://docs.anthropic.com/en/api/migrating-from-text-completions-to-messages
        response = self.client.messages.create(
            model=self.model_name,
            messages=messages_api_format,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            stop_sequences=stop_sequences,
        )
        return response.content[0].text



class GeminiChat(CommonLLMChat):
    SUPPORTED_LLM_NAMES: list[str] = [
        "gemini-1.5-flash-002",
        "gemini-1.5-pro-002",
    ]

    def __init__(
        self,
        model_name: str,
        model_path: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        seed: int = 0,
        max_retries: int = 3,
        wait_seconds: int = 2,
    ):
        super().__init__(model_name, model_path, max_tokens, temperature, seed, max_retries, wait_seconds)

        gemini.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.client = gemini.GenerativeModel(self.model_name)

    def _convert_conv_to_api_format(self, conv: Conversation) -> list[dict]:
        """
        Converts the conversation object to the gemini format.
        ```
        [
            {"role": role1, "parts": text1,
            {"role": role2, "parts": text2,
            {"role": role3, "parts": text3,
        ]
        ```
        """
        # https://ai.google.dev/gemini-api/docs/models/gemini
        formatted_messages = []
        for message in conv.messages:
            for content in message.content:
                match content:
                    case ContentTextMessage(text=text):
                        role = "model" if message.role == "assistant" else message.role
                        formatted_messages.append({"role": role, "parts": text})
        return formatted_messages

    def _call_api(self, messages_api_format: list[dict], stop_sequences: list[str] | None = None) -> str:
        response = self.client.generate_content(
            contents=messages_api_format,
            generation_config=gemini.types.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
                stop_sequences=stop_sequences,
            ),
        )
        return response.text


SUPPORTED_LLM_NAMES: list[str] = (
    OpenAIChat.SUPPORTED_LLM_NAMES
    + TogetherChat.SUPPORTED_LLM_NAMES
    + AnthropicChat.SUPPORTED_LLM_NAMES
    + GeminiChat.SUPPORTED_LLM_NAMES
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
        case _:
            raise ValueError(f"Model name {model_name} must be one of {SUPPORTED_LLM_NAMES}.")
