import os

import anthropic

from phantom_eval._types import LLMChatResponse
from phantom_eval.llm.common import CommonLLMChat, InferenceGenerationConfig


class AnthropicChat(CommonLLMChat):
    def __init__(
        self,
        model_name: str,
        usage_tier: int = 1,
        **kwargs,
    ):
        super().__init__(model_name, **kwargs)
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
