"""Tests for LLMChat interfaces

NOTE: API keys must be set up for these tests to run successfully.
See the README for more information.
"""

import asyncio

import nest_asyncio

nest_asyncio.apply()

from phantom_eval.llm import ContentTextMessage, Conversation, InferenceGenerationConfig, Message, get_llm

EXAMPLE_PROMPT = """
Question: What is 1+1? (Please answer with a single integer.)
Answer:
"""
example_conv = Conversation(
    messages=[Message(role="user", content=[ContentTextMessage(text=EXAMPLE_PROMPT)])]
)
inf_gen_config = InferenceGenerationConfig()


def _test_llm(server: str, model_name: str):
    llm_chat = get_llm(server, model_name, model_kwargs={})
    """
    Test for synchronous calls
    """
    response = asyncio.run(llm_chat.generate_response(example_conv, inf_gen_config))
    pred = response.pred.strip()
    assert pred == "2", f"Expected 2, got {pred}"

    """
    Test for asynchronous calls
    """
    responses = asyncio.run(
        llm_chat.batch_generate_response(
            [
                example_conv,
            ],
            inf_gen_config,
        )
    )
    preds = [response.pred.strip() for response in responses]
    assert preds[0] == "2", f"Expected 2, got {preds[0]}"


def test_anthropic():
    _test_llm(server="anthropic", model_name="claude-3-5-haiku-20241022")


def test_gemini():
    _test_llm(server="gemini", model_name="gemini-1.5-flash-002")


def test_openai():
    _test_llm(server="openai", model_name="gpt-4o-mini-2024-07-18")


def test_together():
    """
    This test is known to fail with the following error:
    together.error.APIError: Error code: 500 - {"message": "Internal server error", "type_": "server_error"}
    """
    _test_llm(server="together", model_name="meta-llama/meta-llama-3.1-8b-instruct-turbo")


def test_vllm():
    """Test for VLLMChat

    This test is implemented slightly differently from the others,
    as vllm exposes an offline inference mode, which we use to implement
    batch_generate_response.

    NOTE: make sure to run the vllm server before running this test!!!
    ```bash
    vllm serve meta-llama/llama-3.1-8b-instruct --dtype auto --api-key token-abc123 --tensor_parallel_size 1
    ```
    """
    llm_chat = get_llm(
        "vllm",
        model_name="meta-llama/llama-3.1-8b-instruct",
        model_kwargs=dict(use_api=True),
    )
    response = asyncio.run(llm_chat.generate_response(example_conv, inf_gen_config))
    pred = response.pred.strip()
    assert pred == "2", f"Expected 2, got {pred}"


def test_llama():
    _test_llm(server="llama", model_name="Llama-3.3-70B-Instruct")
