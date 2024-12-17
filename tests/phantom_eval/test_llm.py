import asyncio
from phantom_eval.llm import get_llm
from phantom_eval.data import (Conversation, 
                               ContentTextMessage, 
                               Message)

EXAMPLE_PROMPT = """
Question: What is 1+1? (Please answer with a single integer.)
Answer:
"""
example_conv = Conversation(messages=[
    Message(role="user", content=[ContentTextMessage(text=EXAMPLE_PROMPT)])
])

def _test_llm(model_name):
    llm_chat = get_llm(
        model_name=model_name,
        model_kwargs=dict(
            temperature=0.0,
            max_retries=0,
        )
    )
    """
    Test for synchronous calls
    """
    response = llm_chat.generate_response(example_conv)
    pred = response.strip()
    assert pred == "2", f"Expected 2, got {pred}"

    """
    Test for asynchronous calls
    """
    responses = asyncio.run(llm_chat.batch_generate_response([example_conv,]))
    preds = [response['pred'].strip() for response in responses]
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
    _test_llm("together:meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo")

# TODO: add tests for VLLMChat