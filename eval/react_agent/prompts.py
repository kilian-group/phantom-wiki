import llm


# TODO add more examples
REACT_EXAMPLES6 = """
<question>Who is the father of anastasia?</question>
<thought round="1">I need to retrieve article about anastasia and find who her father is.</thought>
<action round="1">RetrieveArticle[anastasia]</action>
<observation round="1"># anastasia ## Family The child of anastasia is jack, ringo, maeve. The son of anastasia is dirk. The father of anastasia is daniel. The husband of anastasia is bob. ## Friends The friend of anastasia is marie, thomas, kate. ## Attributes The date of birth of anastasia is 0213-01-04. The job of anastasia is realtor. The hobby of anastasia is bird watching.</observation>
<thought round="2">The father of anastasia is daniel, so the answer is daniel.</thought>
<action round="2">Finish[daniel]</action>
"""


class LLMPrompt:
    REACT_INSTRUCTION = """
    Solve a question answering task with interleaving Thought, Action, Observation steps.
    They are specified in XML tags: <thought>...</thought>, <action>...</action>, and <observation>...</observation>.
    Thought can reason about the current situation, and Action can be two types:
    (1) <action round="{{n}}">RetrieveArticle[{{entity}}]"</action>, which searches the exact {{entity}} on Wikipedia and returns the page if it exists. If not, it will return that the page does not exist.
    (2) <action round="{{n}}">Finish[{{answer}}]"</action>, which finishes the task with {{answer}}.
    You may take as many steps as necessary.
    Here are some examples:
    {examples}
    (END OF EXAMPLES)
    <question>{question}</question>
    {scratchpad}
    """

    def get_react_prompt(self) -> str:
        return self.REACT_INSTRUCTION


class OpenAIPrompt(LLMPrompt):
    pass


class TogetherPrompt(LLMPrompt):
    pass


class GeminiPrompt(LLMPrompt):
    pass


class AnthropicPrompt(LLMPrompt):
    pass


def get_llm_prompt(model_name: str) -> LLMPrompt:
    match model_name:
        case model_name if model_name in llm.OpenAIChat.SUPPORTED_LLM_NAMES:
            return OpenAIPrompt()
        case model_name if model_name in llm.TogetherChat.SUPPORTED_LLM_NAMES:
            return TogetherPrompt()
        case model_name if model_name in llm.GeminiChat.SUPPORTED_LLM_NAMES:
            return GeminiPrompt()
        case model_name if model_name in llm.AnthropicChat.SUPPORTED_LLM_NAMES:
            return AnthropicPrompt()
        case _:
            raise ValueError(f"Model name {model_name} must be one of {llm.SUPPORTED_LLM_NAMES}.")
