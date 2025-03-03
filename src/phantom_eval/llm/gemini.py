import os

import google.generativeai as gemini

from phantom_eval._types import ContentTextMessage, Conversation, LLMChatResponse
from phantom_eval.llm.common import CommonLLMChat, InferenceGenerationConfig


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
            "usage_tier=0": {"RPM": 2, "TPM": 32_000_000},  # free tier
            "usage_tier=1": {"RPM": 1_000, "TPM": 4_000_000},
        },
        "gemini-1.5-flash-8b-001": {
            "usage_tier=0": {"RPM": 15, "TPM": 1_000_000},  # free tier
            "usage_tier=1": {"RPM": 4_000, "TPM": 4_000_000},
        },
        "gemini-2.0-flash-exp": {
            "usage_tier=0": {
                "RPM": 10,
                "TPM": 4_000_000,
            },  # free tier: https://ai.google.dev/gemini-api/docs/models/gemini#gemini-2.0-flash
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
                # NOTE: API does not support topK>40
            ),
        )
        return response

    def _parse_api_output(self, response: object) -> LLMChatResponse:
        # Try to get response text. If failed due to any reason, output empty prediction
        # Example instance why Gemini can fail to return response.text:
        # "The candidate's [finish_reason](https://ai.google.dev/api/generate-content#finishreason) is 4.
        # Meaning that the model was reciting from copyrighted material."
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
            error=error,
        )

    def _count_tokens(self, messages_api_format: list[dict]) -> int:
        response = self.client.count_tokens(messages_api_format)
        return response.total_tokens
