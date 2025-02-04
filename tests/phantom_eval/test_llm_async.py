"""Functionality for testing the RPM and TPM rate limits
"""

import asyncio
import time
from phantom_eval.llm import (CommonLLMChat, 
                              InferenceGenerationConfig,
                              LLMChatResponse)
from phantom_eval.data import (Conversation, 
                               ContentTextMessage, 
                               Message)
from phantom_eval.utils import setup_logging
setup_logging('DEBUG')

# 
# Mock class
# 
# 
# Testing the rate limiting logic
# 
class MockChat(CommonLLMChat):
    SUPPORTED_LLM_NAMES: list[str] = ["mock_model"]
    RATE_LIMITS = {
        "mock_model": {
            "usage_tier=1": {"RPM": 1_000, "TPM": 80_000}, # high RPM but low TPM
            "usage_tier=2": {"RPM": 15, "TPM": 1_000_000}, # low RPM but high TPM
            "usage_tier=3": {"RPM": 1_000, "TPM": 1_000_000}, # high RPM and TPM
        },
    }
    def __init__(
            self, 
            model_name: str, 
            model_path: str | None = None,
            usage_tier: int = 1,
        ):
        super().__init__(model_name, model_path)
        self._update_rate_limits(usage_tier)
    def _count_tokens(self, messages_api_format: list[dict]) -> int:
        return len(messages_api_format[0]["content"][0]["text"])
    def _call_api(self, messages_api_format: list[dict], inf_gen_config: InferenceGenerationConfig, use_async: bool = False) -> object:
        async def mock_api_call():
            # return the content of the message
            print("Begin mock API call")
            await asyncio.sleep(0.1)
            print("End mock API call")
            return messages_api_format[0]["content"][0]["text"]
        return mock_api_call()
    def _parse_api_output(self, response: object) -> LLMChatResponse:
        return LLMChatResponse(pred=response, usage={})


# 
# Tests
# 

EXAMPLE_PROMPT = """
Question: What is 1+1? (Please answer with a single integer.)
Answer:
"""
LONG_EXAMPLE_PROMPT = f"""
Question: What is {'1+' * 250}1? (Please answer with a single integer.)
Answer:
"""
example_conv = Conversation(messages=[
    Message(role="user", content=[ContentTextMessage(text=EXAMPLE_PROMPT)])
])
inf_gen_config = InferenceGenerationConfig()

def test_mock():
    llm_chat = MockChat(
        model_name="mock_model",
        usage_tier=1,
    )
    response = asyncio.run(llm_chat.generate_response(example_conv, inf_gen_config))
    pred = response.pred
    assert pred == EXAMPLE_PROMPT, f"Expected {EXAMPLE_PROMPT}, got {pred}"


def test_mock_batch_high_rpm_low_tpm():
    llm_chat = MockChat(
        model_name="mock_model",
        usage_tier=1,
    )
    n = 1_000
    start = time.time()
    responses = asyncio.run(llm_chat.batch_generate_response(
        [
            Conversation(messages=[Message(role="user", content=[ContentTextMessage(text=LONG_EXAMPLE_PROMPT)])]) 
            for _ in range(n)
        ], 
        inf_gen_config)
    )
    print(f"Time taken for {n} calls: {time.time()-start} seconds")
    print(f"Expected time taken for {n} calls: {n * len(LONG_EXAMPLE_PROMPT)/llm_chat.TPM_LIMIT * 60} seconds")
    preds = [response.pred for response in responses]
    assert all(preds[i] == LONG_EXAMPLE_PROMPT for i in range(n))


def test_mock_batch_low_rpm_high_tpm():
    llm_chat = MockChat(
        model_name="mock_model",
        usage_tier=2,
    )
    print(f"{llm_chat.RPM_LIMIT=}, {llm_chat.TPM_LIMIT=}")
    n = 100
    start = time.time()
    responses = asyncio.run(llm_chat.batch_generate_response(
        [
            Conversation(messages=[Message(role="user", content=[ContentTextMessage(text=LONG_EXAMPLE_PROMPT)])]) 
            for _ in range(n)
        ], 
        inf_gen_config)
    )
    print(f"Time taken for {n} calls: {time.time()-start} seconds")
    print(f"Expected time taken for {n} calls: {n/llm_chat.RPM_LIMIT * 60} seconds")
    preds = [response.pred for response in responses]
    assert all(preds[i] == LONG_EXAMPLE_PROMPT for i in range(n))


def test_mock_batch_high_rpm_high_tpm():
    llm_chat = MockChat(
        model_name="mock_model",
        usage_tier=3,
    )
    n = 1_000
    start = time.time()
    responses = asyncio.run(llm_chat.batch_generate_response(
        [
            Conversation(messages=[Message(role="user", content=[ContentTextMessage(text=LONG_EXAMPLE_PROMPT)])]) 
            for _ in range(n)
        ], 
        inf_gen_config)
    )
    preds = [response.pred for response in responses]
    assert all(preds[i] == LONG_EXAMPLE_PROMPT for i in range(n))
    print(f"Time taken for {n} calls: {time.time()-start} seconds")
    print(f"Expected time taken for {n} calls: {n/llm_chat.RPM_LIMIT * 60} seconds")
