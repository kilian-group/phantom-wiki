import logging
import os

import together

from phantom_eval._types import ContentTextMessage, Conversation, LLMChatResponse
from phantom_eval.llm.common import (
    DEFAULT_LLMS_RPM_TPM_CONFIG_FPATH,
    CommonLLMChat,
    InferenceGenerationConfig,
    load_yaml_config,
)

logger = logging.getLogger(__name__)


class TogetherChat(CommonLLMChat):
    def __init__(
        self,
        model_name: str,
        usage_tier: int = 1,
        **kwargs,
    ):
        super().__init__(model_name, **kwargs)
        self.client = together.Together(api_key=os.getenv("TOGETHER_API_KEY"))
        self.async_client = together.AsyncTogether(api_key=os.getenv("TOGETHER_API_KEY"))
        self._update_rate_limits("together", model_name, usage_tier)

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

    def _update_rate_limits(self, server: str, model_name: str, usage_tier: int) -> None:
        """
        Load rate limits from config file based on server, model name, and usage tier.

        If the rate limits are not found, set `self.enforce_rate_limits` to False.

        Overrides the `_update_rate_limits` method in `CommonLLMChat` to handle TogetherAI's
        default rate limits.
        """
        config = load_yaml_config(DEFAULT_LLMS_RPM_TPM_CONFIG_FPATH)
        tier_key = f"usage_tier={usage_tier}"

        try:
            # Access the configuration using the provider, model name, and usage tier
            server_config = config[server]

            # Check if model_name is in server_config or if "default" is in server_config
            if model_name in server_config:
                rate_limits = server_config[model_name][tier_key]
            else:
                rate_limits = server_config["default"][tier_key]

            self.rpm_limit = rate_limits["RPM"]
            self.tpm_limit = rate_limits["TPM"]
        except KeyError:
            logger.info(
                f"Rate limits not found for {server} server, model name={self.model_name} with {tier_key}."
                " Rate limits will not be enforced."
            )
            self.enforce_rate_limits = False

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
