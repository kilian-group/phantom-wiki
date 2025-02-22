from huggingface_hub import repo_exists

from phantom_eval.llm.anthropic import AnthropicChat
from phantom_eval.llm.common import LLMChat
from phantom_eval.llm.gemini import GeminiChat
from phantom_eval.llm.openai import OpenAIChat
from phantom_eval.llm.together import TogetherChat
from phantom_eval.llm.vllm import VLLMChat

SUPPORTED_LLM_NAMES: list[str] = (
    AnthropicChat.SUPPORTED_LLM_NAMES
    + GeminiChat.SUPPORTED_LLM_NAMES
    + OpenAIChat.SUPPORTED_LLM_NAMES
    + TogetherChat.SUPPORTED_LLM_NAMES
    + VLLMChat.SUPPORTED_LLM_NAMES
)


def get_llm(model_name: str, model_kwargs: dict) -> LLMChat:
    match model_name:
        case model_name if model_name in AnthropicChat.SUPPORTED_LLM_NAMES:
            return AnthropicChat(model_name=model_name, **model_kwargs)
        case model_name if model_name in GeminiChat.SUPPORTED_LLM_NAMES:
            return GeminiChat(model_name=model_name, **model_kwargs)
        case model_name if model_name in OpenAIChat.SUPPORTED_LLM_NAMES:
            return OpenAIChat(model_name=model_name, **model_kwargs)
        case model_name if model_name in TogetherChat.SUPPORTED_LLM_NAMES:
            return TogetherChat(model_name=model_name, **model_kwargs)
        case model_name if repo_exists(model_name):
            # NOTE: vLLM supports all models on Hugging Face Hub
            return VLLMChat(model_name=model_name, **model_kwargs)
        case _:
            raise ValueError(f"Model name {model_name} must be one of {SUPPORTED_LLM_NAMES}.")
