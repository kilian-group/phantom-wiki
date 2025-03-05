from phantom_eval._types import ContentTextMessage, Conversation, LLMChatResponse, Message
from phantom_eval.llm.common import InferenceGenerationConfig, LLMChat, aggregate_usage

SUPPORTED_LLM_SERVERS = [
    "anthropic",
    "gemini",
    "openai",
    "together",
    "vllm",
]


def get_llm(server: str, model_name: str, model_kwargs: dict) -> LLMChat:
    match server:
        case "anthropic":
            from phantom_eval.llm.anthropic import AnthropicChat

            return AnthropicChat(model_name=model_name, **model_kwargs)
        case "gemini":
            from phantom_eval.llm.gemini import GeminiChat

            return GeminiChat(model_name=model_name, **model_kwargs)
        case "openai":
            from phantom_eval.llm.openai import OpenAIChat

            return OpenAIChat(model_name=model_name, **model_kwargs)
        case "together":
            from phantom_eval.llm.together import TogetherChat

            return TogetherChat(model_name=model_name, **model_kwargs)
        case "vllm":
            from phantom_eval.llm.vllm import VLLMChat

            return VLLMChat(model_name=model_name, **model_kwargs)
        case _:
            raise ValueError(f"Provider {server} not supported.")
