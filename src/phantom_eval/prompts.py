import abc

from langchain.prompts import PromptTemplate
import phantom_eval.llm as llm


class LLMPrompt(abc.ABC):
    @abc.abstractmethod
    def get_prompt(self) -> PromptTemplate:
        pass


##### Zeroshot method
class ZeroshotLLMPrompt(LLMPrompt):
    ZEROSHOT_INSTRUCTION = """
    {evidence}
    Answer the following question:
    {question}

    The output should be one of the following:
    - A name (if there is only one correct answer)
    - A list of names separated by commas (if there are multiple correct answers)
    - A number (if the answer is a number)
    DO NOT include any additional information in the output.
    """

    def get_prompt(self) -> PromptTemplate:
        # TODO return str
        return PromptTemplate(
            input_variables=["evidence", "question"],
            template=self.ZEROSHOT_INSTRUCTION,
        )


##### React method
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


class ReactLLMPrompt(LLMPrompt):
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


def get_llm_prompt(method: str, model_name: str) -> LLMPrompt:
    match method:
        case "zeroshot":
            return ZeroshotLLMPrompt()
        case "fewshot":
            raise NotImplementedError("Few-shot evaluation is not supported yet.") 
        case "cot":
            raise NotImplementedError("COT evaluation is not supported yet.")
        case "react":
            match model_name:
                case model_name if model_name in llm.OpenAIChat.SUPPORTED_LLM_NAMES:
                    return ReactLLMPrompt()
                case model_name if model_name in llm.TogetherChat.SUPPORTED_LLM_NAMES:
                    return ReactTogetherPrompt()
                case model_name if model_name in llm.GeminiChat.SUPPORTED_LLM_NAMES:
                    return ReactGeminiPrompt()
                case model_name if model_name in llm.AnthropicChat.SUPPORTED_LLM_NAMES:
                    return ReactLLMPrompt()
                case _:
                    raise ValueError(f"Model name {model_name} must be one of {llm.SUPPORTED_LLM_NAMES}.")
        case _:
            raise ValueError(f"Method {method} not supported.")


# prompt = "Given following table of data about an individual, {} {}"  # question, data

# extra = {
#     "stepbystep": "Think carefully step by step.",
#     "verify": "Verify that your answer aligns with the given data.",
#     "instruction": "Please carefully follow the instructions to provide an accurate answer.",
# }

# format = {
#     "plain": "Please respond with only your answer and no other text.",
#     "answer: with ex": "Please finish your response with Answer: <your answer>, for example, if the answer was yes, you should finish your response with Answer: yes",
#     "answer:": "Please finish your answer with Answer: <your answer>",
# }


# from .score import match

# def score_answer(response, true, scoring=match, key_text="answer: "):
#     response = response.lower()
#     if key_text is None:
#         return response == true
#     answer_index = response.rfind(key_text)
#     if answer_index == -1:
#         return False
#     return scoring(response[answer_index + len(key_text) :], true)


# def evaluate(data, model, prompt, score):
#     correct = 0
#     for input, true in data:
#         input_prompt = prompt.format(*input)
#         pred = model(input_prompt)
#         correct += score(pred, true)

#     return correct


# data = [
#     (
#         (
#             "He was born in 1987 in the state of asw234782. He married his childhood sweetheart kdjhf948 in 2004 and had two beautiful children tuty33545 and 2534bdjd.",
#             "What is the name of the spouse of asw234782?",
#         ),
#         "kdjhf948",
#     ),
#     (
#         (
#             "He was born in 1987 in the state of asw234782. He married his childhood sweetheart kdjhf948 in 2004 and had two beautiful children tuty33545 and 2534bdjd.",
#             "Where was he born?",
#         ),
#         "asw234782",
#     ),
#     (
#         (
#             "He was born in 1987 in the state of asw234782. He married his childhood sweetheart kdjhf948 in 2004 and had two beautiful children tuty33545 and 2534bdjd.",
#             "When was he born?",
#         ),
#         "1987",
#     ),
# ]


# # evaluate(
# #     data,
# #     print,
# #     " ".join([prompt, extra["stepbystep"], format["plain"]]),
# #     lambda x, y: True,
# # )

# # prompt, extra["stepbystep"], format["answer:"]
# answers = [
#     """Sure! Let's work through this step-by-step to determine the name of the spouse of "asw234782":

# The person being described was born in 1987 in a state called "asw234782".
# This person got married to someone named "kdjhf948" in 2004.
# As a result of their marriage, they had two children together: "tuty33545" and "2534bdjd".
# So, based on the information provided, the name of the spouse of "asw234782" is "kdjhf948".

# Answer: kdjhf948""",
#     """Thank you for providing me with this information! Based on the given data, I can determine where he was born as follows:

# The first letter of the state name is "A".
# The second letter of the state name is "S".
# The third letter of the state name is "W".
# Therefore, the person was born in the state of ASW234782.

# Answer: ASW234782""",
#     """To determine when the person was born, we need to follow these steps based on the given information:

# Step 1: Find the year of marriage from the information provided.
# The person got married in 2004.

# Step 2: Calculate the age difference between the date of birth and the year of marriage.
# Year of marriage - Date of birth = X (where X is the number of years)
# X = 2004 - 1987 = 17 years

# Step 3: Determine the exact date of birth using the age at the time of marriage.
# Since the person was born 17 years before their marriage, they were born in:
# Date of birth = Year of marriage + Age at marriage - 17
# Date of birth = 2004 + 17 - 17 = 2004

# Answer: The person was born in 2004.""",
# ]


# for answer, (_, true) in zip(answers, data):
#     print(score_answer(answer, true))
