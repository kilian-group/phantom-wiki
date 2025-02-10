"""Tests for LLMChat interfaces

NOTE: API keys must be set up for these tests to run successfully.
See the README for more information.
"""

import asyncio
from phantom_eval._types import Conversation, ContentTextMessage, Message
from phantom_eval.llm import get_llm
from phantom_eval.llm.common import InferenceGenerationConfig

EXAMPLE_PROMPT = """
Question: What is 1+1? (Please answer with a single integer.)
Answer:
"""
example_conv = Conversation(messages=[
    Message(role="user", content=[ContentTextMessage(text=EXAMPLE_PROMPT)])
])
inf_gen_config = InferenceGenerationConfig()

def _test_llm(model_name):
    llm_chat = get_llm(
        model_name=model_name,
        model_kwargs={}
    )
    """
    Test for synchronous calls
    """
    response = llm_chat.generate_response(example_conv, inf_gen_config)
    pred = response.pred.strip()
    assert pred == "2", f"Expected 2, got {pred}"

    """
    Test for asynchronous calls
    """
    responses = asyncio.run(llm_chat.batch_generate_response([example_conv,], inf_gen_config))
    preds = [response.pred.strip() for response in responses]
    assert preds[0] == "2", f"Expected 2, got {preds[0]}"

def test_anthropic():
    _test_llm("claude-3-5-haiku-20241022")
def test_gemini():
    _test_llm("gemini-1.5-flash-002")
def test_openai():
    _test_llm("gpt-4o-mini-2024-07-18")
def test_together():
    """
    This test is known to fail with the following error:
    together.error.APIError: Error code: 500 - {"message": "Internal server error", "type_": "server_error"}
    """
    _test_llm("meta-llama/meta-llama-3.1-8b-instruct-turbo")

def test_vllm():
    """Test for VLLMChat
    
    This test is implemented slightly differently from the others, 
    as vllm exposes an offline inference mode, which we use to implement
    batch_generate_response.

    NOTE: make sure to run the vllm server before running this test!!!
    ```bash
    vllm serve meta-llama/llama-3.1-8b-instruct --dtype auto --api-key token-abc123 --tensor_parallel_size 4
    ```
    """
    llm_chat = get_llm(
        model_name='meta-llama/llama-3.1-8b-instruct',
        model_kwargs=dict(
            use_server=True,
        )
    )
    response = llm_chat.generate_response(example_conv)
    pred = response.pred.strip()
    assert pred == "2", f"Expected 2, got {pred}"
