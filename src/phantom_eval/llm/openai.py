import os

import openai
import tiktoken

from phantom_eval._types import LLMChatResponse
from phantom_eval.llm.common import CommonLLMChat, InferenceGenerationConfig


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
        enforce_rate_limits: bool = False,
    ):
        super().__init__(
            model_name, model_path, strict_model_name=True, enforce_rate_limits=enforce_rate_limits
        )
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
