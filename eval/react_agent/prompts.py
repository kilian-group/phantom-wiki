from langchain.prompts import PromptTemplate
import llm


REACT_EXAMPLES = """
Example 1:
<question>Who is the father of anastasia?</question>
<thought round="1">I need to retrieve article about anastasia and find who her father is.</thought>
<action round="1">RetrieveArticle[anastasia]</action>
<observation round="1"># anastasia ## Family The son of anastasia is jack, ringo, liam. The son of anastasia is dirk. The father of anastasia is daniel. The husband of anastasia is bob. ## Friends The friend of anastasia is marie, thomas, kate. ## Attributes The date of birth of anastasia is 0213-01-04. The job of anastasia is realtor. The hobby of anastasia is bird watching.</observation>
<thought round="2">The father of anastasia is daniel, so the answer is daniel.</thought>
<action round="2">Finish[daniel]</action>

Example 2:
<question>Who is the mother of ivana?</question>
<thought round="1">I need to retrieve article about ivana and find who her mother is.</thought>
<action round="1">RetrieveArticle[ivana]</action>
<observation round="1">No article exists for the requested entity. Please try retrieving article for another entity.</observation>
<thought round="2">Article about ivana does not exist, so I cannot find the mother of ivana. I will output empty answer.</thought>
<action round="2">Finish[]</action>

Example 3:
<question>Who is the son of anastasia?</question>
<thought round="1">I need to retrieve article about anastasia and find who her father is.</thought>
<action round="1">RetrieveArticle[anastasia]</action>
<observation round="1"># anastasia ## Family The son of anastasia is jack, ringo, liam. The son of anastasia is dirk. The father of anastasia is daniel. The husband of anastasia is bob. ## Friends The friend of anastasia is marie, thomas, kate. ## Attributes The date of birth of anastasia is 0213-01-04. The job of anastasia is realtor. The hobby of anastasia is bird watching.</observation>
<thought round="2">The son of anastasia is jack, ringo, liam, so the answer is jack, ringo, liam.</thought>
<action round="2">Finish[jack,ringo,liam]</action>

Example 4:
<question>How many sons does anastasia have?</question>
<thought round="1">I need to retrieve article about anastasia and find who her father is.</thought>
<action round="1">RetrieveArticle[anastasia]</action>
<observation round="1"># anastasia ## Family The son of anastasia is jack, ringo, liam. The son of anastasia is dirk. The father of anastasia is daniel. The husband of anastasia is bob. ## Friends The friend of anastasia is marie, thomas, kate. ## Attributes The date of birth of anastasia is 0213-01-04. The job of anastasia is realtor. The hobby of anastasia is bird watching.</observation>
<thought round="2">The son of anastasia is jack, ringo, liam, so the answer is 3 sons.</thought>
<action round="2">Finish[3]</action>

Example 5:
<question>What is the job of the father of anastasia?</question>
<thought round="1">First, I need to retrieve article about anastasia and find who her father is.</thought>
<action round="1">RetrieveArticle[anastasia]</action>
<observation round="1"># anastasia ## Family The son of anastasia is jack, ringo, liam. The son of anastasia is dirk. The father of anastasia is daniel. The husband of anastasia is bob. ## Friends The friend of anastasia is marie, thomas, kate. ## Attributes The date of birth of anastasia is 0213-01-04. The job of anastasia is realtor. The hobby of anastasia is bird watching.</observation>
<thought round="2">The father of anastasia is daniel. To find out the job of daniel, I need to retrieve article about daniel.</thought>
<action round="2">RetrieveArticle[daniel]</action>
<observation round="2"># daniel ## Family The daughter of daniel is anastasia. The wife of daniel is leah. The mother of daniel is mary. ## Friends The friend of daniel is paul, catherine, william. ## Attributes The date of birth of daniel is 0192-12-23. The job of daniel is goldsmith. The hobby of daniel is woodworking, crocheting.</observation>
<thought round="3">The father of anastasia is daniel, and the job of daniel is goldsmith. So the answer is goldsmith.</thought>
<action round="3">Finish[goldsmith]</action>

Example 6:
<question>What is the job of the person whose hobby is woodworking?</question>
<thought round="1">I need to search for people whose hobby is woodworking.</thought>
<action round="1">Search[woodworking]</action>
<observation round="1">1. # daniel ## Family The daughter of daniel is anastasia. The wife of daniel is leah. The mother of daniel is mary. ## Friends The friend of daniel is paul, catherine, william. ## Attributes The date of birth of daniel is 0192-12-23. The job of daniel is goldsmith. The hobby of daniel is woodworking, crocheting.  2. # lee ## Family The wife of lee is mary. The child of lee is marie, cindy. ## Friends The friend of lee is young, charles. ## Attributes The job of lee is banker. The hobby of lee is running, woodworking.</observation>
<thought round="2">People whose hobby is woodworking are daniel, lee. The job of daniel is goldsmith, and the job of lee is banker. So the answer is goldsmith, banker.</thought>
<action round="2">Finish[goldsmith,banker]</action>

Example 7:
<question>How many children does the person whose job is woodworking have?</question>
<thought round="1">I need to search for people whose hobby is woodworking.</thought>
<action round="1">Search[woodworking]</action>
<observation round="1">1. # daniel ## Family The daughter of daniel is anastasia. The wife of daniel is leah. The mother of daniel is mary. ## Friends The friend of daniel is paul, catherine, william. ## Attributes The date of birth of daniel is 0192-12-23. The job of daniel is goldsmith. The hobby of daniel is woodworking, crocheting.  2. # lee ## Family The wife of lee is mary. The child of lee is marie, cindy. ## Friends The friend of lee is young, charles. ## Attributes The job of lee is banker. The hobby of lee is running, woodworking.</observation>
<thought round="2">People whose hobby is woodworking are daniel, lee. daniel has 1 child, and lee has 2 children. So the answer is 1, 2.</thought>
<action round="2">Finish[1,2]</action>
"""


class LLMPrompt:
    REACT_INSTRUCTION = """
    Solve a question answering task with interleaving thought, action, observation steps.
    They are specified in XML tags: <thought>...</thought>, <action>...</action>, and <observation>...</observation>.
    Thought can reason about the current situation, and action can be 3 types:
    (1) <action round="{{n}}">RetrieveArticle[{{entity}}]</action>. This action retrieves the article about {{entity}} if it exists. If the article does not exist, the action will say so.
    (2) <action round="{{n}}">Search[{{attribute}}]</action>. This action searches the database for {{attribute}} and retrieves all articles that contain {{attribute}}. If no article contains {{attribute}}, the action will say so.
    (3) <action round="{{n}}">Finish[{{answer}}]</action>. This action answers the question with {{answer}}.
    If you cannot find the answer, output the empty answer like: <action round="{{n}}">Finish[]</action>. 
    If there are multiple answers A,B,C, answer with a comma separated list like: <action round="{{n}}">Finish[A,B,C]</action>. 

    You may take as many steps as necessary.
    Here are some examples:
    (START OF EXAMPLES)
    {examples}
    (END OF EXAMPLES)

    Now answer the following question:
    <question>{question}</question>
    {scratchpad}
    """

    def get_react_prompt(self) -> PromptTemplate:
        return PromptTemplate(
            input_variables=["examples", "question", "scratchpad"],
            template=self.REACT_INSTRUCTION,
        )


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
