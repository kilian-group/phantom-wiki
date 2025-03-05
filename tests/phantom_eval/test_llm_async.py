"""Functionality for testing the RPM and TPM rate limits
"""

import asyncio
import time

from phantom_eval.llm import (
    ContentTextMessage,
    Conversation,
    InferenceGenerationConfig,
    LLMChatResponse,
    Message,
)
from phantom_eval.llm.common import CommonLLMChat
from phantom_eval.utils import setup_logging

setup_logging("DEBUG")


#
# Mock class
#
#
# Testing the rate limiting logic
#
class MockChat(CommonLLMChat):
    RATE_LIMITS = {
        "mock_model": {
            "usage_tier=1": {"RPM": 1_000, "TPM": 80_000},  # high RPM but low TPM
            "usage_tier=2": {"RPM": 20, "TPM": 1_000_000},  # low RPM but high TPM
            "usage_tier=3": {"RPM": 1_000, "TPM": 1_000_000},  # high RPM and TPM
        },
    }

    def __init__(
        self,
        model_name: str,
        model_path: str | None = None,
        usage_tier: int = 1,
        enforce_rate_limits: bool = True,
    ):
        super().__init__(model_name, model_path, enforce_rate_limits=enforce_rate_limits)
        self._update_rate_limits(usage_tier)

    def _count_tokens(self, messages_api_format: list[dict]) -> int:
        return len(messages_api_format[0]["content"][0]["text"])

    def _call_api(
        self,
        messages_api_format: list[dict],
        inf_gen_config: InferenceGenerationConfig,
        use_async: bool = False,
    ) -> object:
        assert use_async, "Mock API does not support sync calls"

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
example_conv = Conversation(
    messages=[Message(role="user", content=[ContentTextMessage(text=EXAMPLE_PROMPT)])]
)
inf_gen_config = InferenceGenerationConfig()


def test_mock():
    llm_chat = MockChat(
        model_name="mock_model",
        usage_tier=1,
        enforce_rate_limits=True,
    )
    response = asyncio.run(llm_chat.generate_response(example_conv, inf_gen_config))
    pred = response.pred
    assert pred == EXAMPLE_PROMPT, f"Expected {EXAMPLE_PROMPT}, got {pred}"


def test_mock_batch_high_rpm_low_tpm():
    """
    Expected output:
    ```
    Time taken for 300 calls: 2 minutes 1.7 seconds
    Expected time taken for 300 calls: 2 minutes 1.2 seconds
    ```
    """
    n = 300
    llm_chat = MockChat(
        model_name="mock_model",
        usage_tier=1,
        enforce_rate_limits=True,
    )
    start = time.time()
    responses = asyncio.run(
        llm_chat.batch_generate_response(
            [
                Conversation(
                    messages=[Message(role="user", content=[ContentTextMessage(text=LONG_EXAMPLE_PROMPT)])]
                )
                for _ in range(n)
            ],
            inf_gen_config,
        )
    )
    elapsed = time.time() - start
    minutes = int(elapsed // 60)
    seconds = elapsed % 60
    print(f"Time taken for {n} calls: {minutes} minutes {seconds:.1f} seconds")

    # NOTE: for this test, the limiting factor is the tokens
    TRUE_RPM = llm_chat.TPM_LIMIT // len(LONG_EXAMPLE_PROMPT)
    expected_minutes = int(n // TRUE_RPM)  # minutes
    remainder_requests = n - expected_minutes * TRUE_RPM
    expected_seconds = remainder_requests / llm_chat.RPM_LIMIT * 60  # seconds
    print(f"Expected time taken for {n} calls: {expected_minutes} minutes {expected_seconds:.1f} seconds")

    preds = [response.pred for response in responses]
    assert all(preds[i] == LONG_EXAMPLE_PROMPT for i in range(n))


def test_mock_batch_low_rpm_high_tpm():
    """expected output:
    ```
    Time taken for 50 calls: 2 minutes 30.0 seconds
    Expected time taken for 50 calls: 2 minutes 30.0 seconds
    ```
    """
    llm_chat = MockChat(
        model_name="mock_model",
        usage_tier=2,
        enforce_rate_limits=True,
    )
    print(f"{llm_chat.RPM_LIMIT=}, {llm_chat.TPM_LIMIT=}")
    n = 50
    start = time.time()
    responses = asyncio.run(
        llm_chat.batch_generate_response(
            [
                Conversation(
                    messages=[Message(role="user", content=[ContentTextMessage(text=LONG_EXAMPLE_PROMPT)])]
                )
                for _ in range(n)
            ],
            inf_gen_config,
        )
    )
    elapsed = time.time() - start
    minutes = int(elapsed // 60)
    seconds = elapsed % 60
    print(f"Time taken for {n} calls: {minutes} minutes {seconds:.1f} seconds")

    # NOTE: for this test, the limiting factor is the RPM
    TRUE_RPM = llm_chat.RPM_LIMIT
    expected_minutes = n // TRUE_RPM  # minutes
    remainder_requests = n - expected_minutes * TRUE_RPM
    expected_seconds = remainder_requests / TRUE_RPM * 60  # seconds
    print(f"Expected time taken for {n} calls: {expected_minutes} minutes {expected_seconds:.1f} seconds")

    preds = [response.pred for response in responses]
    assert all(preds[i] == LONG_EXAMPLE_PROMPT for i in range(n))


def test_mock_batch_high_rpm_high_tpm():
    """expected output:
    ```
    Time taken for 300 calls: 0 minute 18 seconds
    Expected time taken for 300 calls: 0 minute 18 seconds
    ```
    """
    llm_chat = MockChat(
        model_name="mock_model",
        usage_tier=3,
        enforce_rate_limits=True,
    )
    n = 300
    start = time.time()
    responses = asyncio.run(
        llm_chat.batch_generate_response(
            [
                Conversation(
                    messages=[Message(role="user", content=[ContentTextMessage(text=LONG_EXAMPLE_PROMPT)])]
                )
                for _ in range(n)
            ],
            inf_gen_config,
        )
    )
    elapsed = time.time() - start
    minutes = int(elapsed // 60)
    seconds = elapsed % 60
    print(f"Time taken for {n} calls: {minutes} minutes {seconds:.1f} seconds")

    # NOTE: for this test, the limiting factor is the RPM
    TRUE_RPM = llm_chat.RPM_LIMIT
    expected_minutes = n // TRUE_RPM  # minutes
    remainder_requests = n - expected_minutes * TRUE_RPM
    expected_seconds = remainder_requests / TRUE_RPM * 60  # seconds
    print(f"Expected time taken for {n} calls: {expected_minutes} minutes {expected_seconds:.1f} seconds")

    preds = [response.pred for response in responses]
    assert all(preds[i] == LONG_EXAMPLE_PROMPT for i in range(n))
