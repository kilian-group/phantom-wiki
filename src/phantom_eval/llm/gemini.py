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

    def __init__(
        self,
        model_name: str,
        usage_tier: int = 1,
        **kwargs,
    ):
        super().__init__(model_name, **kwargs)

        gemini.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.client = gemini.GenerativeModel(self.model_name)
        self._update_rate_limits("gemini", model_name, usage_tier)

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

    def _parse_api_output(
        self, response: object, inf_gen_config: InferenceGenerationConfig | None = None
    ) -> LLMChatResponse:
        # NOTE: we don't use inf_gen_config for parsing the output of the gemini server
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
