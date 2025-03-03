import logging
import os

import together

from phantom_eval._types import ContentTextMessage, Conversation, LLMChatResponse
from phantom_eval.llm.common import CommonLLMChat, InferenceGenerationConfig

logger = logging.getLogger(__name__)

TG_PREFIX = "tg::"


class TogetherChat(CommonLLMChat):
    # https://docs.together.ai/docs/serverless-models
    SUPPORTED_LLM_NAMES: list[str] = [
        "meta-llama/meta-llama-3.1-8b-instruct-turbo",
        "meta-llama/meta-llama-3.1-70b-instruct-turbo",
        "meta-llama/llama-3.3-70b-instruct-turbo",
        "meta-llama/meta-llama-3.1-405b-instruct-turbo",
        "meta-llama/llama-vision-free",
        # NOTE: the Together model names are identical to the
        # HF model names, so we we add a tg:: prefix to the
        # model names to indicate that we want to use the
        # together.ai serverless models
        # TODO (Albert): debug runtime errors with
        # - deepseek-v3,
        # - r1-distill-llama-70b
        # f"{TG_PREFIX}deepseek-ai/deepseek-v3",
        # f"{TG_PREFIX}deepseek-ai/deepseek-r1",
        # TODO (Albert): use YAML config to specify lower RPM for
        # - deepseek-r1,
        # - r1-distill-qwen-14b
        # f"{TG_PREFIX}deepseek-ai/deepseek-r1-distill-llama-70b",
        # f"{TG_PREFIX}deepseek-ai/deepseek-r1-distill-qwen-1.5b",
        # f"{TG_PREFIX}deepseek-ai/deepseek-r1-distill-qwen-14b",
    ]
    # https://docs.together.ai/docs/rate-limits
    RATE_LIMITS = {
        llm_name: {
            "usage_tier=0": {"RPM": 60, "TPM": 60_000},  # free tier
            "usage_tier=1": {"RPM": 600, "TPM": 180_000},
            "usage_tier=2": {"RPM": 1_800, "TPM": 250_000},
        }
        for llm_name in SUPPORTED_LLM_NAMES
    }

    def __init__(
        self,
        model_name: str,
        model_path: str | None = None,
        usage_tier: int = 1,
        enforce_rate_limits: bool = False,
    ):
        logger.info("Using TogetherAI for inference")
        super().__init__(
            model_name, model_path, strict_model_name=True, enforce_rate_limits=enforce_rate_limits
        )
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
            model=self._get_together_model_name(),
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

    def _get_together_model_name(self) -> str:
        """Remove the tg:: prefix from the model name if present."""
        return self.model_name.replace(TG_PREFIX, "")
