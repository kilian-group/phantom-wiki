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
Question: What is the hobby of the child of Jewel Backus?
Answer: shogi

Example 2:
Question: What is the dob of the person whose hobby is meditation?
Answer: 0259-06-10{constants.answer_sep}0206-04-13

Example 3:
Question: How many siblings does the person whose hobby is meditation have?
Answer: 1{constants.answer_sep}0
"""

class FewshotLLMPrompt(LLMPrompt):
    FEWSHOT_INSTRUCTION = f"""
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
COT_EXAMPLES = f"""
Example 1:
Question: What is the hobby of the child of Jewel Backus?
Answer: First I need to find the child of Jewel Backus. Based on the evidence, the child of Jewel Backus is Derick Backus. Now I need to find the hobby of Derick Backus. Based on the evidence, the hobby of Derick Backus is shogi. The answer is shogi.

Example 2:
Question: What is the dob of the person whose hobby is meditation?
Answer: I need to search for people whose hobby is meditation. Based on the evidence, the people whose hobby is meditation are Adele Ervin, Tyler Ussery. The dob of Adele Ervin is 0259-06-10, and the dob of Tyler Ussery is 0206-04-13. The answer is 0259-06-10{constants.answer_sep}0206-04-13.

Example 3:
Question: How many siblings does the person whose hobby is meditation have?
Answer: I need to search for people whose hobby is meditation. Based on the evidence, the people whose hobby is meditation are Adele Ervin, Tyler Ussery. Adele Ervin has 1 sibling, and Tyler Ussery has 0 siblings. The answer is 1{constants.answer_sep}0.
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
    RAG_INSTRUCTION = f"""
    You are given the following evidence:
    (BEGIN EVIDENCE)
    {{evidence}}
    (END EVIDENCE)
    
    You will be provided a question. Your response must end in the following sentence: The answer is <answer>.
    Here, <answer> must be one of the following: 
    - a name (if there is only one correct answer); 
    - a list of names separated by '{constants.answer_sep}' (if there are multiple correct answers); or
    - a number (if the answer is numerical).

    Question: {{question}}
    Answer (Your response must end in "The answer is <answer>."): """

    def get_prompt(self) -> PromptTemplate:
        return PromptTemplate(
            input_variables=["evidence", "question"],
            template=self.RAG_INSTRUCTION,
        )


##### React method
REACT_EXAMPLES = f"""
Example 1:
Question: Who is the father of Karen Ervin?
Thought 1: I need to retrieve article about Karen Ervin and find who her father is.
Action 1: RetrieveArticle[Karen Ervin].
Observation 1: # Karen Ervin ## Family Karen Ervin's sibling is Alton Cater.  The brother of Karen Ervin is Alton Cater.  The mother of Karen Ervin is Vita Cater.  The father of Karen Ervin is Bruce Cater.  The children of Karen Ervin are Adele Ervin, Lisha Leibowitz.  The daughters of Karen Ervin are Adele Ervin, Lisha Leibowitz.  The husband of Karen Ervin is Boris Ervin.  ## Friends The friend of Karen Ervin is Tyler Ussery.  ## Attributes The date of birth of Karen Ervin is 0231-09-29.  The occupation of Karen Ervin is air cabin crew.  The hobby of Karen Ervin is bus spotting.  The gender of Karen Ervin is female.
Thought 2: The father of Karen Ervin is Bruce Cater, so the answer is Bruce Cater.
Action 2: Finish[Bruce Cater].

Example 2:
Question: Who is the mother of Ivana Smith?
Thought 1: I need to retrieve article about Ivana Smith and find who her mother is.
Action 1: RetrieveArticle[Ivana Smith].
Observation 1: No article exists for the requested entity. Please try retrieving article for another entity.
Thought 2: Article about Ivana Smith does not exist, so I cannot find the mother of Ivana Smith. I will output empty answer.
Action 2: Finish[].

Example 3:
Question: Who is the brother of Veronica Donohue?
Thought 1: I need to retrieve article about Veronica Donohue and find who her brother is.
Action 1: RetrieveArticle[Veronica Donohue].
Observation 1: # Veronica Donohue ## Family Veronica Donohue's siblings are Dirk Donohue, Pedro Donohue, Ty Donohue.  The brothers of Veronica Donohue are Dirk Donohue, Pedro Donohue, Ty Donohue.  The mother of Veronica Donohue is Therese Donohue.  The father of Veronica Donohue is Mason Donohue.  ## Friends The friends of Veronica Donohue are Vita Cater, Aubrey Leibowitz, Bruce Cater, Gerry Donohue, Rigoberto Bode.  ## Attributes The date of birth of Veronica Donohue is 0174-07-16.  The occupation of Veronica Donohue is airline pilot.  The hobby of Veronica Donohue is wikipedia editing.  The gender of Veronica Donohue is female.
Thought 2: The brothers of anastasia are Dirk Donohue, Pedro Donohue, Ty Donohue, so the answer is Dirk Donohue, Pedro Donohue, Ty Donohue.
Action 2: Finish[Dirk Donohue{constants.answer_sep}Pedro Donohue{constants.answer_sep}Ty Donohue].

Example 4:
Question: How many brothers does Veronica Donohue have?
Thought 1: I need to retrieve article about Veronica Donohue and find who her brother is.
Action 1: RetrieveArticle[Veronica Donohue].
Observation 1: # Veronica Donohue ## Family Veronica Donohue's siblings are Dirk Donohue, Pedro Donohue, Ty Donohue.  The brothers of Veronica Donohue are Dirk Donohue, Pedro Donohue, Ty Donohue.  The mother of Veronica Donohue is Therese Donohue.  The father of Veronica Donohue is Mason Donohue.  ## Friends The friends of Veronica Donohue are Vita Cater, Aubrey Leibowitz, Bruce Cater, Gerry Donohue, Rigoberto Bode.  ## Attributes The date of birth of Veronica Donohue is 0174-07-16.  The occupation of Veronica Donohue is airline pilot.  The hobby of Veronica Donohue is wikipedia editing.  The gender of Veronica Donohue is female.
Thought 2: The brothers of anastasia are Dirk Donohue, Pedro Donohue, Ty Donohue, so the answer is 3 brothers.
Action 2: Finish[3].

Example 5:
Question: What is the hobby of the child of Jewel Backus?
Thought 1: First, I need to retrieve article about Jewel Backus and find who her child is.
Action 1: RetrieveArticle[Jewel Backus].
Observation 1: # Jewel Backus ## Family Jewel Backus's sibling is Wilfredo Cater.  The brother of Jewel Backus is Wilfredo Cater.  The mother of Jewel Backus is Ella Cater.  The father of Jewel Backus is Alton Cater.  The child of Jewel Backus is Derick Backus.  The son of Jewel Backus is Derick Backus.  The husband of Jewel Backus is Wes Backus.  ## Friends The friends of Jewel Backus are Pedro Donohue, Staci Donohue, Tiffany Bode, Ty Donohue, Delpha Donohue, Gerry Donohue.  ## Attributes The date of birth of Jewel Backus is 0268-03-07.  The occupation of Jewel Backus is ranger/warden.  The hobby of Jewel Backus is trainspotting.  The gender of Jewel Backus is female.
Thought 2: The child of Jewel Backus is Derick Backus. To find out the hobby of Derick Backus, I need to retrieve article about Derick Backus.
Action 2: RetrieveArticle[Derick Backus].
Observation 2: # Derick Backus ## Family The mother of Derick Backus is Jewel Backus.  The father of Derick Backus is Wes Backus.  ## Friends The friends of Derick Backus are Ella Cater, Gustavo Leibowitz, Lisha Leibowitz, Mason Donohue.  ## Attributes The date of birth of Derick Backus is 0295-10-18.  The occupation of Derick Backus is production assistant, television.  The hobby of Derick Backus is shogi.  The gender of Derick Backus is male.
Thought 3: The son of Jewel Backus is Derick Backus, and the hobby of Derick Backus is shogi. So the answer is shogi.
Action 3: Finish[shogi].

Example 6:
Question: What is the dob of the person whose hobby is meditation?
Thought 1: First, I need to search for people whose hobby is meditation.
Action 1: Search[meditation].
Observation 1: (1) Adele Ervin (2) Tyler Ussery
Thought 2: People whose hobby is meditation are Adele Ervin, Tyler Ussery. Now I need to retrieve articles about Adele Ervin and Tyler Ussery and find their dob.
Action 2: RetrieveArticle[Adele Ervin].
Observation 2: # Adele Ervin ## Family Adele Ervin's sibling is Lisha Leibowitz.  The sister of Adele Ervin is Lisha Leibowitz.  The mother of Adele Ervin is Karen Ervin.  The father of Adele Ervin is Boris Ervin.  ## Friends The friends of Adele Ervin are Alton Cater, Boris Ervin, Dirk Donohue, Therese Donohue, Wilfredo Cater.  ## Attributes The date of birth of Adele Ervin is 0259-06-10.  The occupation of Adele Ervin is contractor.  The hobby of Adele Ervin is meditation.  The gender of Adele Ervin is female.
Thought 3: The dob of Adele Ervin is 0259-06-10. Now I need to retrieve article about Tyler Ussery and find his dob.
Action 3: RetrieveArticle[Tyler Ussery].
Observation 3: # Tyler Ussery ## Family The child of Tyler Ussery is Ella Cater.  The daughter of Tyler Ussery is Ella Cater.  The wife of Tyler Ussery is Margarite Ussery.  ## Friends The friends of Tyler Ussery are Karen Ervin, Lisha Leibowitz.  ## Attributes The date of birth of Tyler Ussery is 0206-04-13.  The occupation of Tyler Ussery is investment banker, corporate.  The hobby of Tyler Ussery is meditation.  The gender of Tyler Ussery is male.
Thought 4: The dob of Tyler Ussery is 0206-04-13. The dob of Adele Ervin is 0259-06-10. So the answer is 0259-06-10, 0206-04-13.
Action 4: Finish[0259-06-10{constants.answer_sep}0206-04-13].

Example 7:
Question: How many siblings does the person whose hobby is meditation have?
Thought 1: I need to search for people whose hobby is meditation.
Action 1: Search[meditation].
Observation 1: (1) Adele Ervin (2) Tyler Ussery
Thought 2: People whose hobby is meditation are Adele Ervin, Tyler Ussery. Now I need to retrieve articles about Adele Ervin and Tyler Ussery and find their number of siblings.
Action 2: RetrieveArticle[Adele Ervin].
Observation 2: # Adele Ervin ## Family Adele Ervin's sibling is Lisha Leibowitz.  The sister of Adele Ervin is Lisha Leibowitz.  The mother of Adele Ervin is Karen Ervin.  The father of Adele Ervin is Boris Ervin.  ## Friends The friends of Adele Ervin are Alton Cater, Boris Ervin, Dirk Donohue, Therese Donohue, Wilfredo Cater.  ## Attributes The date of birth of Adele Ervin is 0259-06-10.  The occupation of Adele Ervin is contractor.  The hobby of Adele Ervin is meditation.  The gender of Adele Ervin is female.
Thought 3: The sibling of Adele Ervin is Lisha Leibowitz. Now I need to retrieve article about Tyler Ussery and find his sibling.
Action 3: RetrieveArticle[Tyler Ussery].
Observation 3: # Tyler Ussery ## Family The child of Tyler Ussery is Ella Cater.  The daughter of Tyler Ussery is Ella Cater.  The wife of Tyler Ussery is Margarite Ussery.  ## Friends The friends of Tyler Ussery are Karen Ervin, Lisha Leibowitz.  ## Attributes The date of birth of Tyler Ussery is 0206-04-13.  The occupation of Tyler Ussery is investment banker, corporate.  The hobby of Tyler Ussery is meditation.  The gender of Tyler Ussery is male.
Thought 4: The article about Tyler Ussery does not mention any siblings, so he has 0 siblings. Adele Ervin has 1 sibling. So the answer is 1, 0.
Action 4: Finish[1{constants.answer_sep}0].
"""


class ReactLLMPrompt(LLMPrompt):
    # We use fstring to write the prompt, because we want to use the constants from the constants.py file
    # examples, question, and scratchpad are input variables that the react agent
    # will provide after calling the get_prompt method.
    # n, entity, attribute, answer are placeholders that we want the LLM to read within double braces, like {{n}}, {{entity}}, {{attribute}}, {{answer}}
    # So we escape them with 4 braces in this fstring (after get_prompt().format() is called, 
    # they will be replaced with 2 braces)
    REACT_INSTRUCTION = f"""
    Solve a question answering task with interleaving Thought, Action, Observation steps.
    Thought can reason about the current situation, and Action can be 3 types:
    (1) RetrieveArticle[{{{{entity}}}}]. This action retrieves the article about {{{{entity}}}} if it exists. If the article does not exist, the action will say so.
    (2) Search[{{{{attribute}}}}]. This action searches the database for {{{{attribute}}}} and retrieves all articles that contain {{{{attribute}}}}. If no article contains {{{{attribute}}}}, the action will say so.
    (3) Finish[{{{{answer}}}}]. This action answers the question with {{{{answer}}}}.
    If you cannot find the answer, output the empty answer like: Finish[].
    If you cannot find the answer for a counting question, output the empty answer like: Finish[0].
    If there are multiple answers A,B,C, answer with a list like: Finish[A{constants.answer_sep}B{constants.answer_sep}C].

    You may take as many steps as necessary.
    Here are some examples:
    (START OF EXAMPLES)
    {{examples}}
    (END OF EXAMPLES)

    Now answer the following question:
    Question: {{question}}
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
Question: Who is the father of Karen Ervin?
Action 1: RetrieveArticle[Karen Ervin].
Observation 1: # Karen Ervin ## Family Karen Ervin's sibling is Alton Cater.  The brother of Karen Ervin is Alton Cater.  The mother of Karen Ervin is Vita Cater.  The father of Karen Ervin is Bruce Cater.  The children of Karen Ervin are Adele Ervin, Lisha Leibowitz.  The daughters of Karen Ervin are Adele Ervin, Lisha Leibowitz.  The husband of Karen Ervin is Boris Ervin.  ## Friends The friend of Karen Ervin is Tyler Ussery.  ## Attributes The date of birth of Karen Ervin is 0231-09-29.  The occupation of Karen Ervin is air cabin crew.  The hobby of Karen Ervin is bus spotting.  The gender of Karen Ervin is female.
Action 2: Finish[Bruce Cater].

Example 2:
Question: Who is the mother of Ivana Smith?
Action 1: RetrieveArticle[Ivana Smith].
Observation 1: No article exists for the requested entity. Please try retrieving article for another entity.
Action 2: Finish[].

Example 3:
Question: Who is the brother of Veronica Donohue?
Action 1: RetrieveArticle[Veronica Donohue].
Observation 1: # Veronica Donohue ## Family Veronica Donohue's siblings are Dirk Donohue, Pedro Donohue, Ty Donohue.  The brothers of Veronica Donohue are Dirk Donohue, Pedro Donohue, Ty Donohue.  The mother of Veronica Donohue is Therese Donohue.  The father of Veronica Donohue is Mason Donohue.  ## Friends The friends of Veronica Donohue are Vita Cater, Aubrey Leibowitz, Bruce Cater, Gerry Donohue, Rigoberto Bode.  ## Attributes The date of birth of Veronica Donohue is 0174-07-16.  The occupation of Veronica Donohue is airline pilot.  The hobby of Veronica Donohue is wikipedia editing.  The gender of Veronica Donohue is female.
Action 2: Finish[Dirk Donohue{constants.answer_sep}Pedro Donohue{constants.answer_sep}Ty Donohue].

Example 4:
Question: How many brothers does Veronica Donohue have?
Action 1: RetrieveArticle[Veronica Donohue].
Observation 1: # Veronica Donohue ## Family Veronica Donohue's siblings are Dirk Donohue, Pedro Donohue, Ty Donohue.  The brothers of Veronica Donohue are Dirk Donohue, Pedro Donohue, Ty Donohue.  The mother of Veronica Donohue is Therese Donohue.  The father of Veronica Donohue is Mason Donohue.  ## Friends The friends of Veronica Donohue are Vita Cater, Aubrey Leibowitz, Bruce Cater, Gerry Donohue, Rigoberto Bode.  ## Attributes The date of birth of Veronica Donohue is 0174-07-16.  The occupation of Veronica Donohue is airline pilot.  The hobby of Veronica Donohue is wikipedia editing.  The gender of Veronica Donohue is female.
Action 2: Finish[3].

Example 5:
Question: What is the hobby of the child of Jewel Backus?
Action 1: RetrieveArticle[Jewel Backus].
Observation 1: # Jewel Backus ## Family Jewel Backus's sibling is Wilfredo Cater.  The brother of Jewel Backus is Wilfredo Cater.  The mother of Jewel Backus is Ella Cater.  The father of Jewel Backus is Alton Cater.  The child of Jewel Backus is Derick Backus.  The son of Jewel Backus is Derick Backus.  The husband of Jewel Backus is Wes Backus.  ## Friends The friends of Jewel Backus are Pedro Donohue, Staci Donohue, Tiffany Bode, Ty Donohue, Delpha Donohue, Gerry Donohue.  ## Attributes The date of birth of Jewel Backus is 0268-03-07.  The occupation of Jewel Backus is ranger/warden.  The hobby of Jewel Backus is trainspotting.  The gender of Jewel Backus is female.
Action 2: RetrieveArticle[Derick Backus].
Observation 2: # Derick Backus ## Family The mother of Derick Backus is Jewel Backus.  The father of Derick Backus is Wes Backus.  ## Friends The friends of Derick Backus are Ella Cater, Gustavo Leibowitz, Lisha Leibowitz, Mason Donohue.  ## Attributes The date of birth of Derick Backus is 0295-10-18.  The occupation of Derick Backus is production assistant, television.  The hobby of Derick Backus is shogi.  The gender of Derick Backus is male.
Action 3: Finish[shogi].

Example 6:
Question: What is the dob of the person whose hobby is meditation?
Action 1: Search[meditation].
Observation 1: (1) Adele Ervin (2) Tyler Ussery
Action 2: RetrieveArticle[Adele Ervin].
Observation 2: # Adele Ervin ## Family Adele Ervin's sibling is Lisha Leibowitz.  The sister of Adele Ervin is Lisha Leibowitz.  The mother of Adele Ervin is Karen Ervin.  The father of Adele Ervin is Boris Ervin.  ## Friends The friends of Adele Ervin are Alton Cater, Boris Ervin, Dirk Donohue, Therese Donohue, Wilfredo Cater.  ## Attributes The date of birth of Adele Ervin is 0259-06-10.  The occupation of Adele Ervin is contractor.  The hobby of Adele Ervin is meditation.  The gender of Adele Ervin is female.
Action 3: RetrieveArticle[Tyler Ussery].
Observation 3: # Tyler Ussery ## Family The child of Tyler Ussery is Ella Cater.  The daughter of Tyler Ussery is Ella Cater.  The wife of Tyler Ussery is Margarite Ussery.  ## Friends The friends of Tyler Ussery are Karen Ervin, Lisha Leibowitz.  ## Attributes The date of birth of Tyler Ussery is 0206-04-13.  The occupation of Tyler Ussery is investment banker, corporate.  The hobby of Tyler Ussery is meditation.  The gender of Tyler Ussery is male.
Action 4: Finish[0259-06-10{constants.answer_sep}0206-04-13].

Example 7:
Question: How many siblings does the person whose hobby is meditation have?
Action 1: Search[meditation].
Observation 1: (1) Adele Ervin (2) Tyler Ussery
Action 2: RetrieveArticle[Adele Ervin].
Observation 2: # Adele Ervin ## Family Adele Ervin's sibling is Lisha Leibowitz.  The sister of Adele Ervin is Lisha Leibowitz.  The mother of Adele Ervin is Karen Ervin.  The father of Adele Ervin is Boris Ervin.  ## Friends The friends of Adele Ervin are Alton Cater, Boris Ervin, Dirk Donohue, Therese Donohue, Wilfredo Cater.  ## Attributes The date of birth of Adele Ervin is 0259-06-10.  The occupation of Adele Ervin is contractor.  The hobby of Adele Ervin is meditation.  The gender of Adele Ervin is female.
Action 3: RetrieveArticle[Tyler Ussery].
Observation 3: # Tyler Ussery ## Family The child of Tyler Ussery is Ella Cater.  The daughter of Tyler Ussery is Ella Cater.  The wife of Tyler Ussery is Margarite Ussery.  ## Friends The friends of Tyler Ussery are Karen Ervin, Lisha Leibowitz.  ## Attributes The date of birth of Tyler Ussery is 0206-04-13.  The occupation of Tyler Ussery is investment banker, corporate.  The hobby of Tyler Ussery is meditation.  The gender of Tyler Ussery is male.
Action 4: Finish[1{constants.answer_sep}0].
"""


class ActLLMPrompt(LLMPrompt):
    # We use fstring to write the prompt, because we want to use the constants from the constants.py file
    # examples, question, and scratchpad are input variables that the act agent
    # will provide after calling the get_prompt method.
    # n, entity, attribute, answer are placeholders that we want the LLM to read within double braces, like {{n}}, {{entity}}, {{attribute}}, {{answer}}
    # So we escape them with 4 braces in this fstring (after get_prompt().format() is called, 
    # they will be replaced with 2 braces)
    ACT_INSTRUCTION = f"""
    Solve a question answering task with interleaving Action and Observation steps.
    Action can be 3 types:
    (1) RetrieveArticle[{{{{entity}}}}]. This action retrieves the article about {{{{entity}}}} if it exists. If the article does not exist, the action will say so.
    (2) Search[{{{{attribute}}}}]. This action searches the database for {{{{attribute}}}} and retrieves all articles that contain {{{{attribute}}}}. If no article contains {{{{attribute}}}}, the action will say so.
    (3) Finish[{{{{answer}}}}]. This action answers the question with {{{{answer}}}}.
    If you cannot find the answer, output the empty answer like: Finish[].
    If you cannot find the answer for a counting question, output the empty answer like: Finish[0].
    If there are multiple answers A,B,C, answer with a list like: Finish[A{constants.answer_sep}B{constants.answer_sep}C].

    You may take as many steps as necessary.
    Here are some examples:
    (START OF EXAMPLES)
    {{examples}}
    (END OF EXAMPLES)

    Now answer the following question:
    Question: {{question}}
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
        case "fewshot" | "fewshot-sc" | "fewshot-rag":
            return FewshotLLMPrompt()
        case "cot" | "cot-sc" | "cot-sc->react" | "cot-rag":
            return CoTLLMPrompt()
        case "rag":
            return ZeroshotLLMPrompt()
            # return RAGLLMPrompt()
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

