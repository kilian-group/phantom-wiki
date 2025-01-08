import abc

from langchain.prompts import PromptTemplate
import phantom_eval.llm as llm
from phantom_eval import constants


class LLMPrompt(abc.ABC):
    @abc.abstractmethod
    def get_prompt(self) -> PromptTemplate:
        pass


##### Zeroshot method
class ZeroshotLLMPrompt(LLMPrompt):
    ZEROSHOT_INSTRUCTION = f"""
    You are given the following evidence:
    (BEGIN EVIDENCE)
    {{evidence}}
    (END EVIDENCE)
    
    You will be provided a question. Your task is to provide an answer according to these instructions: 
    - The output must be one of the following: a name (if there is only one correct answer); a list of names separated by '{constants.answer_sep}' (if there are multiple correct answers); or a number (if the answer is numerical).
    - DO NOT include any additional information in your answer.

    Question: {{question}}
    Answer: """

    def get_prompt(self) -> PromptTemplate:
        return PromptTemplate(
            input_variables=["evidence", "question"],
            template=self.ZEROSHOT_INSTRUCTION,
        )

##### Fewshot method
# The current example is the example from CoT trivially adapted
FEWSHOT_EXAMPLES = f"""
Example 1:
Question: What is the job of the father of anastasia?
Answer: goldsmith.

Example 2:
Question: What is the job of the person whose hobby is woodworking?
Answer: goldsmith{constants.answer_sep}banker.

Example 3:
Question: How many children does the person whose job is woodworking have?
Answer: 1{constants.answer_sep}2.
"""
class FewshotLLMPrompt(LLMPrompt):
    FEWSHOT_INSTRUCTION = """
    You are given the following evidence:
    (BEGIN EVIDENCE)
    {{evidence}}
    (END EVIDENCE)
    
    You will be provided a question. Your task is to provide an answer according to these instructions: 
    - The output must be one of the following: a name (if there is only one correct answer); a list of names separated by '{constants.answer_sep}' (if there are multiple correct answers); or a number (if the answer is numerical).
    - DO NOT include any additional information in your answer.

    Here are some examples:
    (START OF EXAMPLES)
    {{examples}}
    (END OF EXAMPLES)

    Question: {{question}}
    Answer: """

    def get_prompt(self):
        return PromptTemplate(
            input_variables=["evidence", "examples", "question"],
            template=self.FEWSHOT_INSTRUCTION,
        )

##### CoT method
# Some alternative formats:
# 1. <thought>...</thought> and <action>Finish[answer]</action> tags
# Pros: 
# - This would be more similar to the React method. 
# - In the future, if we want to standardize things, maybe this is the way to go.
# Cons: 
# - We would require additional parsing for the final answer.
# 
# Justification for the present format:
# - Answer is easier to parse.
# - For smaller models, it might be easier to generate the answer.
# Potential cons:
# - Output is less structured, so might be harder to verify intermediate steps.
COT_EXAMPLES = f"""
Example 1:
Question: What is the job of the father of anastasia?
Answer: First I need to find the father of anastasia. Based on the evidence, the father of anastasia is daniel. Now I need to find the job of daniel. Based on the evidence, the job of daniel is goldsmith. The answer is goldsmith.

Example 2:
Question: What is the job of the person whose hobby is woodworking?
Answer: I need to search for people whose hobby is woodworking. Based on the evidence, the people whose hobby is woodworking are daniel, lee. The job of daniel is goldsmith, and the job of lee is banker. The answer is goldsmith{constants.answer_sep}banker.

Example 3:
Question: How many children does the person whose job is woodworking have?
Answer: I need to search for people whose hobby is woodworking. Based on the evidence, the people whose hobby is woodworking are daniel, lee. Daniel has 1 child, and lee has 2 children. The answer is 1{constants.answer_sep}2.
"""

class CoTLLMPrompt(LLMPrompt):
    COT_INSTRUCTION = f"""
    You are given the following evidence:
    (BEGIN EVIDENCE)
    {{evidence}}
    (END EVIDENCE)
    
    You will be provided a question. Your response must end in the following sentence: The answer is <answer>.
    Here, <answer> must be one of the following: 
    - a name (if there is only one correct answer); 
    - a list of names separated by '{constants.answer_sep}' (if there are multiple correct answers); or
    - a number (if the answer is numerical).

    Here are some examples:
    (START OF EXAMPLES)
    {{examples}}
    (END OF EXAMPLES)

    Question: {{question}}
    Answer: """

    def get_prompt(self) -> PromptTemplate:
        return PromptTemplate(
            input_variables=["evidence", "examples", "question"],
            template=self.COT_INSTRUCTION,
        )


##### RAG method
class RAGLLMPrompt(LLMPrompt):
    RAG_INSTRUCTION = """"""

    def get_prompt(self):
        raise NotImplementedError("RAG evaluation is not supported yet.")


##### React method
REACT_EXAMPLES = f"""
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
<action round="2">Finish[jack{constants.answer_sep}ringo{constants.answer_sep}liam]</action>

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
<action round="2">Finish[goldsmith{constants.answer_sep}banker]</action>

Example 7:
<question>How many children does the person whose job is woodworking have?</question>
<thought round="1">I need to search for people whose hobby is woodworking.</thought>
<action round="1">Search[woodworking]</action>
<observation round="1">1. # daniel ## Family The daughter of daniel is anastasia. The wife of daniel is leah. The mother of daniel is mary. ## Friends The friend of daniel is paul, catherine, william. ## Attributes The date of birth of daniel is 0192-12-23. The job of daniel is goldsmith. The hobby of daniel is woodworking, crocheting.  2. # lee ## Family The wife of lee is mary. The child of lee is marie, cindy. ## Friends The friend of lee is young, charles. ## Attributes The job of lee is banker. The hobby of lee is running, woodworking.</observation>
<thought round="2">People whose hobby is woodworking are daniel, lee. daniel has 1 child, and lee has 2 children. So the answer is 1, 2.</thought>
<action round="2">Finish[1{constants.answer_sep}2]</action>
"""


class ReactLLMPrompt(LLMPrompt):
    # We use fstring to write the prompt, because we want to use the constants from the constants.py file
    # examples, question, and scratchpad are input variables that the react agent
    # will provide after calling the get_prompt method.
    # n, entity, attribute, answer are placeholders that we want the LLM to read within double braces, like {{n}}, {{entity}}, {{attribute}}, {{answer}}
    # So we escape them with 4 braces in this fstring (after get_prompt().format() is called, 
    # they will be replaced with 2 braces)
    REACT_INSTRUCTION = f"""
    Solve a question answering task with interleaving thought, action, observation steps.
    They are specified in XML tags: <thought>...</thought>, <action>...</action>, and <observation>...</observation>.
    Thought can reason about the current situation, and action can be 3 types:
    (1) <action round="{{{{n}}}}">RetrieveArticle[{{{{entity}}}}]</action>. This action retrieves the article about {{{{entity}}}} if it exists. If the article does not exist, the action will say so.
    (2) <action round="{{{{n}}}}">Search[{{{{attribute}}}}]</action>. This action searches the database for {{{{attribute}}}} and retrieves all articles that contain {{{{attribute}}}}. If no article contains {{{{attribute}}}}, the action will say so.
    (3) <action round="{{{{n}}}}">Finish[{{{{answer}}}}]</action>. This action answers the question with {{{{answer}}}}.
    If you cannot find the answer, output the empty answer like: <action round="{{{{n}}}}">Finish[]</action>.
    If there are multiple answers A,B,C, answer with a list like: <action round="{{{{n}}}}">Finish[A{constants.answer_sep}B{constants.answer_sep}C]</action>.

    You may take as many steps as necessary.
    Here are some examples:
    (START OF EXAMPLES)
    {{examples}}
    (END OF EXAMPLES)

    Now answer the following question:
    <question>{{question}}</question>
    {{scratchpad}}
    """

    def get_prompt(self) -> PromptTemplate:
        return PromptTemplate(
            input_variables=["examples", "question", "scratchpad"],
            template=self.REACT_INSTRUCTION,
        )


class ReactTogetherPrompt(ReactLLMPrompt):
    # TODO: Customize REACT_INSTRUCTION for Together models
    pass


class ReactGeminiPrompt(ReactLLMPrompt):
    # TODO: Customize REACT_INSTRUCTION for Gemini
    pass


##### Act method
ACT_EXAMPLES = f"""
Example 1:
<question>Who is the father of anastasia?</question>
<action round="1">RetrieveArticle[anastasia]</action>
<observation round="1"># anastasia ## Family The son of anastasia is jack, ringo, liam. The son of anastasia is dirk. The father of anastasia is daniel. The husband of anastasia is bob. ## Friends The friend of anastasia is marie, thomas, kate. ## Attributes The date of birth of anastasia is 0213-01-04. The job of anastasia is realtor. The hobby of anastasia is bird watching.</observation>
<action round="2">Finish[daniel]</action>

Example 2:
<question>Who is the mother of ivana?</question>
<action round="1">RetrieveArticle[ivana]</action>
<observation round="1">No article exists for the requested entity. Please try retrieving article for another entity.</observation>
<action round="2">Finish[]</action>

Example 3:
<question>Who is the son of anastasia?</question>
<action round="1">RetrieveArticle[anastasia]</action>
<observation round="1"># anastasia ## Family The son of anastasia is jack, ringo, liam. The son of anastasia is dirk. The father of anastasia is daniel. The husband of anastasia is bob. ## Friends The friend of anastasia is marie, thomas, kate. ## Attributes The date of birth of anastasia is 0213-01-04. The job of anastasia is realtor. The hobby of anastasia is bird watching.</observation>
<action round="2">Finish[jack{constants.answer_sep}ringo{constants.answer_sep}liam]</action>

Example 4:
<question>How many sons does anastasia have?</question>
<action round="1">RetrieveArticle[anastasia]</action>
<observation round="1"># anastasia ## Family The son of anastasia is jack, ringo, liam. The son of anastasia is dirk. The father of anastasia is daniel. The husband of anastasia is bob. ## Friends The friend of anastasia is marie, thomas, kate. ## Attributes The date of birth of anastasia is 0213-01-04. The job of anastasia is realtor. The hobby of anastasia is bird watching.</observation>
<action round="2">Finish[3]</action>

Example 5:
<question>What is the job of the father of anastasia?</question>
<action round="1">RetrieveArticle[anastasia]</action>
<observation round="1"># anastasia ## Family The son of anastasia is jack, ringo, liam. The son of anastasia is dirk. The father of anastasia is daniel. The husband of anastasia is bob. ## Friends The friend of anastasia is marie, thomas, kate. ## Attributes The date of birth of anastasia is 0213-01-04. The job of anastasia is realtor. The hobby of anastasia is bird watching.</observation>
<action round="2">RetrieveArticle[daniel]</action>
<observation round="2"># daniel ## Family The daughter of daniel is anastasia. The wife of daniel is leah. The mother of daniel is mary. ## Friends The friend of daniel is paul, catherine, william. ## Attributes The date of birth of daniel is 0192-12-23. The job of daniel is goldsmith. The hobby of daniel is woodworking, crocheting.</observation>
<action round="3">Finish[goldsmith]</action>

Example 6:
<question>What is the job of the person whose hobby is woodworking?</question>
<action round="1">Search[woodworking]</action>
<observation round="1">1. # daniel ## Family The daughter of daniel is anastasia. The wife of daniel is leah. The mother of daniel is mary. ## Friends The friend of daniel is paul, catherine, william. ## Attributes The date of birth of daniel is 0192-12-23. The job of daniel is goldsmith. The hobby of daniel is woodworking, crocheting.  2. # lee ## Family The wife of lee is mary. The child of lee is marie, cindy. ## Friends The friend of lee is young, charles. ## Attributes The job of lee is banker. The hobby of lee is running, woodworking.</observation>
<action round="2">Finish[goldsmith{constants.answer_sep}banker]</action>

Example 7:
<question>How many children does the person whose job is woodworking have?</question>
<action round="1">Search[woodworking]</action>
<observation round="1">1. # daniel ## Family The daughter of daniel is anastasia. The wife of daniel is leah. The mother of daniel is mary. ## Friends The friend of daniel is paul, catherine, william. ## Attributes The date of birth of daniel is 0192-12-23. The job of daniel is goldsmith. The hobby of daniel is woodworking, crocheting.  2. # lee ## Family The wife of lee is mary. The child of lee is marie, cindy. ## Friends The friend of lee is young, charles. ## Attributes The job of lee is banker. The hobby of lee is running, woodworking.</observation>
<action round="2">Finish[1{constants.answer_sep}2]</action>
"""


class ActLLMPrompt(LLMPrompt):
    # We use fstring to write the prompt, because we want to use the constants from the constants.py file
    # examples, question, and scratchpad are input variables that the act agent
    # will provide after calling the get_prompt method.
    # n, entity, attribute, answer are placeholders that we want the LLM to read within double braces, like {{n}}, {{entity}}, {{attribute}}, {{answer}}
    # So we escape them with 4 braces in this fstring (after get_prompt().format() is called, 
    # they will be replaced with 2 braces)
    ACT_INSTRUCTION = f"""
    Solve a question answering task with interleaving action and observation steps.
    They are specified in XML tags: <action>...</action> and <observation>...</observation>.
    Action can be 3 types:
    (1) <action round="{{{{n}}}}">RetrieveArticle[{{{{entity}}}}]</action>. This action retrieves the article about {{{{entity}}}} if it exists. If the article does not exist, the action will say so.
    (2) <action round="{{{{n}}}}">Search[{{{{attribute}}}}]</action>. This action searches the database for {{{{attribute}}}} and retrieves all articles that contain {{{{attribute}}}}. If no article contains {{{{attribute}}}}, the action will say so.
    (3) <action round="{{{{n}}}}">Finish[{{{{answer}}}}]</action>. This action answers the question with {{{{answer}}}}.
    If you cannot find the answer, output the empty answer like: <action round="{{{{n}}}}">Finish[]</action>.
    If there are multiple answers A,B,C, answer with a list like: <action round="{{{{n}}}}">Finish[A{constants.answer_sep}B{constants.answer_sep}C]</action>.

    You may take as many steps as necessary.
    Here are some examples:
    (START OF EXAMPLES)
    {{examples}}
    (END OF EXAMPLES)

    Now answer the following question:
    <question>{{question}}</question>
    {{scratchpad}}
    """

    def get_prompt(self) -> PromptTemplate:
        return PromptTemplate(
            input_variables=["examples", "question", "scratchpad"],
            template=self.ACT_INSTRUCTION,
        )


def get_llm_prompt(method: str, model_name: str) -> LLMPrompt:
    # For react->cot-sc and cot-sc->react methods, return the LLMPrompt for the first part of the method
    match method:
        case "zeroshot" | "zeroshot-sc":
            return ZeroshotLLMPrompt()
        case "fewshot" | "fewshot-sc":
            return FewshotLLMPrompt()
        case "cot" | "cot-sc" | "cot-sc->react":
            return CoTLLMPrompt()
        case "RAG":
            raise NotImplementedError("RAG evaluation is not supported yet.")
        case "react" | "react->cot-sc":
            match model_name:
                case model_name if model_name in llm.OpenAIChat.SUPPORTED_LLM_NAMES:
                    return ReactLLMPrompt()
                case model_name if model_name in llm.TogetherChat.SUPPORTED_LLM_NAMES:
                    return ReactTogetherPrompt()
                case model_name if model_name in llm.GeminiChat.SUPPORTED_LLM_NAMES:
                    return ReactGeminiPrompt()
                case model_name if model_name in llm.AnthropicChat.SUPPORTED_LLM_NAMES:
                    return ReactLLMPrompt()
                case model_name if model_name in llm.VLLMChat.SUPPORTED_LLM_NAMES:
                    return ReactLLMPrompt()
                case _:
                    raise ValueError(f"Model name {model_name} must be one of {llm.SUPPORTED_LLM_NAMES}.")
        case "act":
            return ActLLMPrompt()
        case _:
            raise ValueError(f"Method {method} not supported.")

