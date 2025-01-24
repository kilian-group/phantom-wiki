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
    - The output must be one of the following: a name (if there is only one correct answer); or a list of names separated by '{constants.answer_sep}' (if there are multiple correct answers).
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
Question: Who is the brother of Dino Beltran?
Answer: Orlando Beltran

Example 2:
Question: Who is the sibling of Barabara Beltran?
Answer: Aida Wang{constants.answer_sep}Vicki Hackworth

Example 3:
Question: Who is the child of the sibling of Stacia Toombs?
Answer: Aida Wang{constants.answer_sep}Barabara Beltran{constants.answer_sep}Vicki Hackworth

Example 4:
Question: Who is the uncle of William Smock?
Answer: Eli Smock

Example 5:
Question: What is the occupation of the sister of the grandmother of Virgil Hackworth?
Answer: actuary

Example 6:
Question: Who is the brother of the person whose occupation is associate professor?
Answer: Orlando Beltran

Example 7:
Question: What is the date of birth of the person whose hobby is meteorology?
Answer: 0929-10-28{constants.answer_sep}0989-06-11

Example 8:
Question: Who is the cousin of the person whose occupation is broadcast engineer?
Answer: Leslee Toombs

Example 9:
Question: Who is the great-granddaughter of the person whose hobby is biology?
Answer: Shelli Beltran{constants.answer_sep}Stacia Toombs
"""

class FewshotLLMPrompt(LLMPrompt):
    FEWSHOT_INSTRUCTION = f"""
    You are given the following evidence:
    (BEGIN EVIDENCE)
    {{evidence}}
    (END EVIDENCE)
    
    You will be provided a question. Your task is to provide an answer according to these instructions: 
    - The output must be one of the following: a name (if there is only one correct answer); or a list of names separated by '{constants.answer_sep}' (if there are multiple correct answers).
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
Question: Who is the brother of Dino Beltran?
Answer: Based on the evidence, the brother of Dino Beltran is Orlando Beltran. The answer is Orlando Beltran.

Example 2:
Question: Who is the sibling of Barabara Beltran?
Answer: Based on the evidence, the siblings of Barabara Beltran are Aida Wang, Vicki Hackworth. The answer is Aida Wang{constants.answer_sep}Vicki Hackworth.

Example 3:
Question: Who is the child of the sibling of Stacia Toombs?
Answer: First I need to find the sibling of Stacia Toombs. Based on the evidence, the sibling of Stacia Toombs is Shelli Beltran. Now I need to find the child of Shelli Beltran. Based on the evidence, the children of Shelli Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth. The answer is Aida Wang{constants.answer_sep}Barabara Beltran{constants.answer_sep}Vicki Hackworth.

Example 4:
Question: Who is the uncle of William Smock?
Answer: An uncle is the brother of a parent. Based on the evidence, the parents of William Smock are Dominique Smock, Gene Smock. To find the uncle of William Smock, I need to find the brother of Dominique Smock and Gene Smock. Based on the evidence, Dominique Smock has no brother, and the brother of Gene Smock is Eli Smock. So the uncle of William Smock is Eli Smock. The answer is Eli Smock.

Example 5:
Question: What is the occupation of the sister of the grandmother of Virgil Hackworth?
Answer: A grandmother is the mother of a parent. Based on the evidence, the parents of Virgil Hackworth are Ricardo Hackworth, Vicki Hackworth. To find the grandmother of Virgil Hackworth, I need to find the mother of Ricardo Hackworth and Vicki Hackworth. Based on the evidence, Ricardo Hackworth has no mother, and the mother of Vicki Hackworth is Shelli Beltran. Now I need to find the sister of Shelli Beltran. Based on the evidence, the sister of Shelli Beltran is Stacia Toombs. Based on the evidence, the occupation of Stacia Toombs is actuary. The answer is actuary.

Example 6:
Question: Who is the brother of the person whose occupation is associate professor?
Answer: I need to search for people whose occupation is associate professor. Based on the evidence, the person whose occupation is associate professor is Dino Beltran. And the brother of Dino Beltran is Orlando Beltran. The answer is Orlando Beltran.

Example 7:
Question: What is the date of birth of the person whose hobby is meteorology?
Answer: I need to search for people whose hobby is meteorology. Based on the evidence, the people whose hobby is meteorology are Alison Smock, Barabara Beltran. The date of birth of Alison Smock is 0929-10-28, and the date of birth of Barabara Beltran is 0989-06-11. The answer is 0929-10-28{constants.answer_sep}0989-06-11.

Example 8:
Question: Who is the cousin of the person whose occupation is broadcast engineer?
Answer: I need to search for people whose occupation is broadcast engineer. Based on the evidence, the person whose occupation is broadcast engineer is Barabara Beltran. A cousin is the child of the sibling of the parent. Based on the evidence, the parents of Barabara Beltran are Dino Beltran, Shelli Beltran. The sibling of Dino Beltran is Orlando Beltran, and the sibling of Shelli Beltran is Stacia Toombs. Based on the evidence, Orlando Beltran has no child, and the child of Stacia Toombs is Leslee Toombs. So the cousin of Barabara Beltran is Leslee Toombs. The answer is Leslee Toombs.

Example 9:
Question: Who is the great-granddaughter of the person whose hobby is biology?
Answer: I need to search for people whose hobby is biology. Based on the evidence, the person whose hobby is biology is Alvaro Smock. To find the great-granddaughter of Alvaro Smock, I need to find the daughter of the child of the child of Alvaro Smock. Based on the evidence, the children of Alvaro Smock are Eli Smock, Gene Smock. Eli Smock has no child, and the child of Gene Smock is Williams Smock. The daughters of Williams Smock are Shelli Beltran, Stacia Toombs. So the great-granddaughters of Alvaro Smock, whose hobby is biology, are Shelli Beltran, Stacia Toombs. The answer is Shelli Beltran{constants.answer_sep}Stacia Toombs.
"""

class CoTLLMPrompt(LLMPrompt):
    COT_INSTRUCTION = f"""
    You are given the following evidence:
    (BEGIN EVIDENCE)
    {{evidence}}
    (END EVIDENCE)
    
    You will be provided a question. Your response must end in the following sentence: The answer is <answer>.
    Here, <answer> must be one of the following: 
    - a name (if there is only one correct answer); or
    - a list of names separated by '{constants.answer_sep}' (if there are multiple correct answers).

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
Question: Who is the brother of Dino Beltran?
Thought 1: I need to retrieve article about Dino Beltran and find who his brother is.
Action 1: RetrieveArticle[Dino Beltran].
Observation 1: # Dino Beltran ## Family The parents of Dino Beltran are Brian Beltran, Daisy Beltran.  Dino Beltran's sibling is Orlando Beltran.  The brother of Dino Beltran is Orlando Beltran.  The mother of Dino Beltran is Daisy Beltran.  The father of Dino Beltran is Brian Beltran.  The children of Dino Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth.  The daughters of Dino Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth.  The wife of Dino Beltran is Shelli Beltran.  ## Friends The friend of Dino Beltran is Alvaro Smock.  ## Attributes The date of birth of Dino Beltran is 0958-08-09.  The occupation of Dino Beltran is associate professor.  The hobby of Dino Beltran is shogi.
Thought 2: The brother of Dino Beltran is Orlando Beltran, so the answer is Orlando Beltran.
Action 2: Finish[Orlando Beltran].

Example 2:
Question: Who is the mother of Ivana Smith?
Thought 1: I need to retrieve article about Ivana Smith and find who her mother is.
Action 1: RetrieveArticle[Ivana Smith].
Observation 1: No article exists for the requested entity. Please try retrieving article for another entity.
Thought 2: Article about Ivana Smith does not exist, so I cannot find the mother of Ivana Smith. I will output empty answer.
Action 2: Finish[].

Example 3:
Question: Who is the sibling of Barabara Beltran?
Thought 1: I need to retrieve article about Barabara Beltran and find who her sibling is.
Action 1: RetrieveArticle[Barabara Beltran].
Observation 1: # Barabara Beltran ## Family The parents of Barabara Beltran are Dino Beltran, Shelli Beltran.  Barabara Beltran's siblings are Aida Wang, Vicki Hackworth.  The sisters of Barabara Beltran are Aida Wang, Vicki Hackworth.  The mother of Barabara Beltran is Shelli Beltran.  The father of Barabara Beltran is Dino Beltran.  ## Friends ## Attributes The date of birth of Barabara Beltran is 0989-06-11.  The occupation of Barabara Beltran is broadcast engineer.  The hobby of Barabara Beltran is meteorology.
Thought 2: The siblings of Barabara Beltran are Aida Wang, Vicki Hackworth. So the answer is Aida Wang, Vicki Hackworth.
Action 2: Finish[Aida Wang{constants.answer_sep}Vicki Hackworth].

Example 4:
Question: Who is the child of the sibling of Stacia Toombs?
Thought 1: First, I need to retrieve article about Stacia Toombs and find who her sibling is.
Action 1: RetrieveArticle[Stacia Toombs].
Observation 1: # Stacia Toombs ## Family The parents of Stacia Toombs are Alison Smock, Williams Smock.  Stacia Toombs's sibling is Shelli Beltran.  The sister of Stacia Toombs is Shelli Beltran.  The mother of Stacia Toombs is Alison Smock.  The father of Stacia Toombs is Williams Smock.  The child of Stacia Toombs is Leslee Toombs.  The daughter of Stacia Toombs is Leslee Toombs.  The husband of Stacia Toombs is Wilbert Toombs.  ## Friends The friends of Stacia Toombs are Brian Beltran, Isiah Lutz, Leeann Hackworth, Lesley Lutz, Ryan Wang.  ## Attributes The date of birth of Stacia Toombs is 0959-03-22.  The occupation of Stacia Toombs is actuary.  The hobby of Stacia Toombs is finance.
Thought 2: The sibling of Stacia Toombs is Shelli Beltran. Now I need to retrieve article about Shelli Beltran and find who her child is.
Action 2: RetrieveArticle[Shelli Beltran].
Observation 2: # Shelli Beltran ## Family The parents of Shelli Beltran are Alison Smock, Williams Smock.  Shelli Beltran's sibling is Stacia Toombs.  The sister of Shelli Beltran is Stacia Toombs.  The mother of Shelli Beltran is Alison Smock.  The father of Shelli Beltran is Williams Smock.  The children of Shelli Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth.  The daughters of Shelli Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth.  The husband of Shelli Beltran is Dino Beltran.  ## Friends The friends of Shelli Beltran are Brian Beltran, Eli Smock, Isiah Lutz, Leslee Toombs, Lesley Lutz, Ryan Wang.  ## Attributes The date of birth of Shelli Beltran is 0958-03-08.  The occupation of Shelli Beltran is occupational therapist.  The hobby of Shelli Beltran is sociology.
Thought 3: The child of Shelli Beltran is Aida Wang, Barabara Beltran, Vicki Hackworth. So the answer is Aida Wang, Barabara Beltran, Vicki Hackworth.
Action 3: Finish[Aida Wang{constants.answer_sep}Barabara Beltran{constants.answer_sep}Vicki Hackworth].

Example 5:
Question: Who is the uncle of William Smock?
Thought 1: First, I need to retrieve article about William Smock. To find the uncle of William Smock, I need to find the brother of his parent.
Action 1: RetrieveArticle[William Smock].
Observation 1: # Williams Smock ## Family The parents of Williams Smock are Dominique Smock, Gene Smock.  The mother of Williams Smock is Dominique Smock.  The father of Williams Smock is Gene Smock.  The children of Williams Smock are Shelli Beltran, Stacia Toombs.  The daughters of Williams Smock are Shelli Beltran, Stacia Toombs.  The wife of Williams Smock is Alison Smock.  ## Friends The friend of Williams Smock is Lannie Smock.  ## Attributes The date of birth of Williams Smock is 0926-04-04.  The occupation of Williams Smock is clinical biochemist.  The hobby of Williams Smock is social studies.
Thought 2: The parents of William Smock are Dominique Smock, Gene Smock. To find the uncle of William Smock, I need to find the brother of Dominique Smock and Gene Smock.
Action 2: RetrieveArticle[Dominique Smock].
Observation 2: # Dominique Smock ## Family The child of Dominique Smock is Williams Smock.  The son of Dominique Smock is Williams Smock.  The husband of Dominique Smock is Gene Smock.  ## Friends The friends of Dominique Smock are Gene Smock, Isiah Lutz, Orlando Beltran, Vicki Hackworth.  ## Attributes The date of birth of Dominique Smock is 0897-09-08.  The occupation of Dominique Smock is sports therapist.  The hobby of Dominique Smock is dominoes.
Thought 3: Dominique Smock has no brother. Now I need to retrieve article about Gene Smock and find his brother.
Action 3: RetrieveArticle[Gene Smock].
Observation 3: # Gene Smock ## Family The parents of Gene Smock are Alvaro Smock, Lannie Smock.  Gene Smock's sibling is Eli Smock.  The brother of Gene Smock is Eli Smock.  The mother of Gene Smock is Lannie Smock.  The father of Gene Smock is Alvaro Smock.  The child of Gene Smock is Williams Smock.  The son of Gene Smock is Williams Smock.  The wife of Gene Smock is Dominique Smock.  ## Friends The friends of Gene Smock are Leeann Hackworth, Leisa Lutz, Ricardo Hackworth, Alvaro Smock, Dominique Smock.  ## Attributes The date of birth of Gene Smock is 0898-08-16.  The occupation of Gene Smock is immunologist.  The hobby of Gene Smock is architecture.
Thought 4: The brother of Gene Smock is Eli Smock, and Dominique Smock has no brother. Since Gene Smock and Dominique Smock are the parents of William Smock, the uncle of William Smock is Eli Smock. So the answer is Eli Smock.
Action 4: Finish[Eli Smock].

Example 6:
Question: What is the occupation of the sister of the grandmother of Virgil Hackworth?
Thought 1: First, I need to retrieve article about Virgil Hackworth. To find the grandmother of Virgil Hackworth, I need to find the mother of his parent.
Action 1: RetrieveArticle[Virgil Hackworth].
Observation 1: # Virgil Hackworth ## Family The parents of Virgil Hackworth are Ricardo Hackworth, Vicki Hackworth.  Virgil Hackworth's siblings are Leeann Hackworth, Leisa Lutz.  The sisters of Virgil Hackworth are Leeann Hackworth, Leisa Lutz.  The mother of Virgil Hackworth is Vicki Hackworth.  The father of Virgil Hackworth is Ricardo Hackworth.  ## Friends The friends of Virgil Hackworth are Alison Smock, Eli Smock, Orlando Beltran, Ryan Wang.  ## Attributes The date of birth of Virgil Hackworth is 1009-06-23.  The occupation of Virgil Hackworth is sound technician.  The hobby of Virgil Hackworth is wikipedia editing.
Thought 2: The parents of Virgil Hackworth are Ricardo Hackworth, Vicki Hackworth. To find the grandmother of Virgil Hackworth, I need to find the mother of Ricardo Hackworth and Vicki Hackworth.
Action 2: RetrieveArticle[Ricardo Hackworth].
Observation 2: # Ricardo Hackworth ## Family The children of Ricardo Hackworth are Leeann Hackworth, Leisa Lutz, Virgil Hackworth.  The son of Ricardo Hackworth is Virgil Hackworth.  The daughters of Ricardo Hackworth are Leeann Hackworth, Leisa Lutz.  The wife of Ricardo Hackworth is Vicki Hackworth.  ## Friends The friends of Ricardo Hackworth are Gene Smock, Isiah Lutz, Johnetta Wang.  ## Attributes The date of birth of Ricardo Hackworth is 0983-02-24.  The occupation of Ricardo Hackworth is clinical research associate.  The hobby of Ricardo Hackworth is dairy farming.
Thought 3: Ricardo Hackworth has no mother. So I need to retrieve article about Vicki Hackworth and find her mother.
Action 3: RetrieveArticle[Vicki Hackworth].
Observation 3: # Vicki Hackworth ## Family The parents of Vicki Hackworth are Dino Beltran, Shelli Beltran.  Vicki Hackworth's siblings are Aida Wang, Barabara Beltran.  The sisters of Vicki Hackworth are Aida Wang, Barabara Beltran.  The mother of Vicki Hackworth is Shelli Beltran.  The father of Vicki Hackworth is Dino Beltran.  The children of Vicki Hackworth are Leeann Hackworth, Leisa Lutz, Virgil Hackworth.  The son of Vicki Hackworth is Virgil Hackworth.  The daughters of Vicki Hackworth are Leeann Hackworth, Leisa Lutz.  The husband of Vicki Hackworth is Ricardo Hackworth.  ## Friends The friends of Vicki Hackworth are Brian Beltran, Dominique Smock, Eli Smock.  ## Attributes The date of birth of Vicki Hackworth is 0985-05-30.  The occupation of Vicki Hackworth is police officer.  The hobby of Vicki Hackworth is meditation.
Thought 4: The mother of Vicki Hackworth is Shelli Beltran. So the only grandmother of Virgil Hackworth is Shelli Beltran. Now I need to retrieve article about Shelli Beltran and find her sister.
Action 4: RetrieveArticle[Shelli Beltran].
Observation 4: # Shelli Beltran ## Family The parents of Shelli Beltran are Alison Smock, Williams Smock.  Shelli Beltran's sibling is Stacia Toombs.  The sister of Shelli Beltran is Stacia Toombs.  The mother of Shelli Beltran is Alison Smock.  The father of Shelli Beltran is Williams Smock.  The children of Shelli Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth.  The daughters of Shelli Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth.  The husband of Shelli Beltran is Dino Beltran.  ## Friends The friends of Shelli Beltran are Brian Beltran, Eli Smock, Isiah Lutz, Leslee Toombs, Lesley Lutz, Ryan Wang.  ## Attributes The date of birth of Shelli Beltran is 0958-03-08.  The occupation of Shelli Beltran is occupational therapist.  The hobby of Shelli Beltran is sociology.
Thought 5: The sister of Shelli Beltran is Stacia Toombs. Now I need to retrieve article about Stacia Toombs and find her occupation.
Action 5: RetrieveArticle[Stacia Toombs].
Observation 5: # Stacia Toombs ## Family The parents of Stacia Toombs are Alison Smock, Williams Smock.  Stacia Toombs's sibling is Shelli Beltran.  The sister of Stacia Toombs is Shelli Beltran.  The mother of Stacia Toombs is Alison Smock.  The father of Stacia Toombs is Williams Smock.  The child of Stacia Toombs is Leslee Toombs.  The daughter of Stacia Toombs is Leslee Toombs.  The husband of Stacia Toombs is Wilbert Toombs.  ## Friends The friends of Stacia Toombs are Brian Beltran, Isiah Lutz, Leeann Hackworth, Lesley Lutz, Ryan Wang.  ## Attributes The date of birth of Stacia Toombs is 0959-03-22.  The occupation of Stacia Toombs is actuary.  The hobby of Stacia Toombs is finance.
Thought 6: The occupation of Stacia Toombs is actuary. So the answer is actuary.
Action 6: Finish[actuary].

Example 7:
Question: Who is the brother of the person whose occupation is associate professor?
Thought 1: First, I need to search for people whose occupation is associate professor.
Action 1: Search[associate professor].
Observation 1: (1) Dino Beltran
Thought 2: Person whose hobby is associate professor is Dino Beltran. Now I need to retrieve article about Dino Beltran and find his brother.
Action 2: RetrieveArticle[Dino Beltran].
Observation 2: # Dino Beltran ## Family The parents of Dino Beltran are Brian Beltran, Daisy Beltran.  Dino Beltran's sibling is Orlando Beltran.  The brother of Dino Beltran is Orlando Beltran.  The mother of Dino Beltran is Daisy Beltran.  The father of Dino Beltran is Brian Beltran.  The children of Dino Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth.  The daughters of Dino Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth.  The wife of Dino Beltran is Shelli Beltran.  ## Friends The friend of Dino Beltran is Alvaro Smock.  ## Attributes The date of birth of Dino Beltran is 0958-08-09.  The occupation of Dino Beltran is associate professor.  The hobby of Dino Beltran is shogi.
Thought 3: The brother of Dino Beltran is Orlando Beltran, so the answer is Orlando Beltran.
Action 3: Finish[Orlando Beltran].

Example 8:
Question: What is the date of birth of the person whose hobby is meteorology?
Thought 1: First, I need to search for people whose hobby is meteorology.
Action 1: Search[meteorology].
Observation 1: (1) Alison Smock (2) Barabara Beltran
Thought 2: People whose hobby is meteorology are Alison Smock, Barabara Beltran. Now I need to retrieve article about Alison Smock and Barabara Beltran and find their date of birth.
Action 2: RetrieveArticle[Alison Smock].
Observation 2: # Alison Smock ## Family The children of Alison Smock are Shelli Beltran, Stacia Toombs.  The daughters of Alison Smock are Shelli Beltran, Stacia Toombs.  The husband of Alison Smock is Williams Smock.  ## Friends The friends of Alison Smock are Eli Smock, Lannie Smock, Virgil Hackworth.  ## Attributes The date of birth of Alison Smock is 0929-10-28.  The occupation of Alison Smock is health promotion specialist.  The hobby of Alison Smock is meteorology.
Thought 3: The date of birth of Alison Smock is 0929-10-28. Now I need to retrieve article about Barabara Beltran and find her date of birth.
Action 3: RetrieveArticle[Barabara Beltran].
Observation 3: # Barabara Beltran ## Family The parents of Barabara Beltran are Dino Beltran, Shelli Beltran.  Barabara Beltran's siblings are Aida Wang, Vicki Hackworth.  The sisters of Barabara Beltran are Aida Wang, Vicki Hackworth.  The mother of Barabara Beltran is Shelli Beltran.  The father of Barabara Beltran is Dino Beltran.  ## Friends ## Attributes The date of birth of Barabara Beltran is 0989-06-11.  The occupation of Barabara Beltran is broadcast engineer.  The hobby of Barabara Beltran is meteorology.
Thought 4: The date of birth of Barabara Beltran is 0989-06-11. So the answer is 0929-10-28, 0989-06-11.
Action 4: Finish[0929-10-28{constants.answer_sep}0989-06-11].

Example 9:
Question: Who is the cousin of the person whose occupation is broadcast engineer?
Thought 1: First, I need to search for people whose occupation is broadcast engineer.
Action 1: Search[broadcast engineer].
Observation 1: # Barabara Beltran ## Family The parents of Barabara Beltran are Dino Beltran, Shelli Beltran.  Barabara Beltran's siblings are Aida Wang, Vicki Hackworth.  The sisters of Barabara Beltran are Aida Wang, Vicki Hackworth.  The mother of Barabara Beltran is Shelli Beltran.  The father of Barabara Beltran is Dino Beltran.  ## Friends ## Attributes The date of birth of Barabara Beltran is 0989-06-11.  The occupation of Barabara Beltran is broadcast engineer.  The hobby of Barabara Beltran is meteorology.
Thought 2: Person whose hobby is broadcast engineer is Barabara Beltran. The cousin of Barabara Beltran is the child of sibling of her parent. Barabara Beltran's parents are Dino Beltran and Shelly Beltran. Now I need to find the sibling of Dino Beltran and Shelly Beltran.
Action 2: RetrieveArticle[Dino Beltran].
Observation 2: # Dino Beltran ## Family The parents of Dino Beltran are Brian Beltran, Daisy Beltran.  Dino Beltran's sibling is Orlando Beltran.  The brother of Dino Beltran is Orlando Beltran.  The mother of Dino Beltran is Daisy Beltran.  The father of Dino Beltran is Brian Beltran.  The children of Dino Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth.  The daughters of Dino Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth.  The wife of Dino Beltran is Shelli Beltran.  ## Friends The friend of Dino Beltran is Alvaro Smock.  ## Attributes The date of birth of Dino Beltran is 0958-08-09.  The occupation of Dino Beltran is associate professor.  The hobby of Dino Beltran is shogi.
Thought 3: The sibling of Dino Beltran is Orlando Beltran. Now I need to retrieve article about Orlando Beltran and find his child.
Action 3: RetrieveArticle[Orlando Beltran].
Observation 3: # Orlando Beltran ## Family The parents of Orlando Beltran are Brian Beltran, Daisy Beltran.  Orlando Beltran's sibling is Dino Beltran.  The brother of Orlando Beltran is Dino Beltran.  The mother of Orlando Beltran is Daisy Beltran.  The father of Orlando Beltran is Brian Beltran.  ## Friends The friends of Orlando Beltran are Virgil Hackworth, Dominique Smock.  ## Attributes The date of birth of Orlando Beltran is 0953-10-23.  The occupation of Orlando Beltran is petroleum engineer.  The hobby of Orlando Beltran is learning.
Thought 4: Orlando Beltran has no child, so no cousin from the side of Dino Beltran. Now I need to retrieve article about Shelli Beltran and find her sibling.
Action 4: RetrieveArticle[Shelli Beltran].
Observation 4: # Shelli Beltran ## Family The parents of Shelli Beltran are Alison Smock, Williams Smock.  Shelli Beltran's sibling is Stacia Toombs.  The sister of Shelli Beltran is Stacia Toombs.  The mother of Shelli Beltran is Alison Smock.  The father of Shelli Beltran is Williams Smock.  The children of Shelli Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth.  The daughters of Shelli Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth.  The husband of Shelli Beltran is Dino Beltran.  ## Friends The friends of Shelli Beltran are Brian Beltran, Eli Smock, Isiah Lutz, Leslee Toombs, Lesley Lutz, Ryan Wang.  ## Attributes The date of birth of Shelli Beltran is 0958-03-08.  The occupation of Shelli Beltran is occupational therapist.  The hobby of Shelli Beltran is sociology.
Thought 5: The sibling of Shelli Beltran is Stacia Toombs. Now I need to retrieve article about Stacia Toombs and find her child, to get the cousin of Barabara Beltran.
Action 5: RetrieveArticle[Stacia Toombs].
Observation 5: # Stacia Toombs ## Family The parents of Stacia Toombs are Alison Smock, Williams Smock.  Stacia Toombs's sibling is Shelli Beltran.  The sister of Stacia Toombs is Shelli Beltran.  The mother of Stacia Toombs is Alison Smock.  The father of Stacia Toombs is Williams Smock.  The child of Stacia Toombs is Leslee Toombs.  The daughter of Stacia Toombs is Leslee Toombs.  The husband of Stacia Toombs is Wilbert Toombs.  ## Friends The friends of Stacia Toombs are Brian Beltran, Isiah Lutz, Leeann Hackworth, Lesley Lutz, Ryan Wang.  ## Attributes The date of birth of Stacia Toombs is 0959-03-22.  The occupation of Stacia Toombs is actuary.  The hobby of Stacia Toombs is finance.
Thought 6: The child of Stacia Toombs is Leslee Toombs. So the cousin of Barabara Beltran is Leslee Toombs. The answer is Leslee Toombs.
Action 6: Finish[Leslee Toombs].

Example 10:
Question: Who is the great-granddaughter of the person whose hobby is biology?
Thought 1: First, I need to search for people whose hobby is biology.
Action 1: Search[biology].
Observation 1: (1) Alvaro Smock
Thought 2: Person whose hobby is biology is Alvaro Smock. Now I need to retrieve article about Alvaro Smock and find his great-granddaughter. A great-granddaughter is the daughter of the child of the child of the person.
Action 2: RetrieveArticle[Alvaro Smock].
Observation 2: # Alvaro Smock ## Family The children of Alvaro Smock are Eli Smock, Gene Smock.  The sons of Alvaro Smock are Eli Smock, Gene Smock.  The wife of Alvaro Smock is Lannie Smock.  ## Friends The friends of Alvaro Smock are Dino Beltran, Gene Smock, Aida Wang.  ## Attributes The date of birth of Alvaro Smock is 0867-07-12.  The occupation of Alvaro Smock is osteopath.  The hobby of Alvaro Smock is biology.
Thought 3: The children of Alvaro Smock are Eli Smock, Gene Smock. Now I need to retrieve article about Eli Smock and Gene Smock and find their child.
Action 3: RetrieveArticle[Eli Smock].
Observation 3: # Eli Smock ## Family The parents of Eli Smock are Alvaro Smock, Lannie Smock.  Eli Smock's sibling is Gene Smock.  The brother of Eli Smock is Gene Smock.  The mother of Eli Smock is Lannie Smock.  The father of Eli Smock is Alvaro Smock.  ## Friends The friends of Eli Smock are Leisa Lutz, Shelli Beltran, Vicki Hackworth, Virgil Hackworth, Alison Smock, Brian Beltran.  ## Attributes The date of birth of Eli Smock is 0901-01-18.  The occupation of Eli Smock is retail manager.  The hobby of Eli Smock is tether car.
Thought 4: Eli Smock has no child. Now I need to retrieve article about Gene Smock and find his child.
Action 4: RetrieveArticle[Gene Smock].
Observation 4: # Gene Smock ## Family The parents of Gene Smock are Alvaro Smock, Lannie Smock.  Gene Smock's sibling is Eli Smock.  The brother of Gene Smock is Eli Smock.  The mother of Gene Smock is Lannie Smock.  The father of Gene Smock is Alvaro Smock.  The child of Gene Smock is Williams Smock.  The son of Gene Smock is Williams Smock.  The wife of Gene Smock is Dominique Smock.  ## Friends The friends of Gene Smock are Leeann Hackworth, Leisa Lutz, Ricardo Hackworth, Alvaro Smock, Dominique Smock.  ## Attributes The date of birth of Gene Smock is 0898-08-16.  The occupation of Gene Smock is immunologist.  The hobby of Gene Smock is architecture.
Thought 5: The child of Gene Smock is Williams Smock. Now I need to retrieve article about Williams Smock and find his daughter, to get the great-granddaughter of Alvaro Smock.
Action 5: RetrieveArticle[Williams Smock].
Observation 5: # Williams Smock ## Family The parents of Williams Smock are Dominique Smock, Gene Smock.  The mother of Williams Smock is Dominique Smock.  The father of Williams Smock is Gene Smock.  The children of Williams Smock are Shelli Beltran, Stacia Toombs.  The daughters of Williams Smock are Shelli Beltran, Stacia Toombs.  The wife of Williams Smock is Alison Smock.  ## Friends The friend of Williams Smock is Lannie Smock.  ## Attributes The date of birth of Williams Smock is 0926-04-04.  The occupation of Williams Smock is clinical biochemist.  The hobby of Williams Smock is social studies.
Thought 6: The daughters of Williams Smock are Shelli Beltran, Stacia Toombs. So the great-granddaughters of Alvaro Smock, whose hobby is biology, are Shelli Beltran, Stacia Toombs. The answer is Shelli Beltran, Stacia Toombs.
Action 6: Finish[Shelli Beltran{constants.answer_sep}Stacia Toombs].
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
Question: Who is the brother of Dino Beltran?
Action 1: RetrieveArticle[Dino Beltran].
Observation 1: # Dino Beltran ## Family The parents of Dino Beltran are Brian Beltran, Daisy Beltran.  Dino Beltran's sibling is Orlando Beltran.  The brother of Dino Beltran is Orlando Beltran.  The mother of Dino Beltran is Daisy Beltran.  The father of Dino Beltran is Brian Beltran.  The children of Dino Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth.  The daughters of Dino Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth.  The wife of Dino Beltran is Shelli Beltran.  ## Friends The friend of Dino Beltran is Alvaro Smock.  ## Attributes The date of birth of Dino Beltran is 0958-08-09.  The occupation of Dino Beltran is associate professor.  The hobby of Dino Beltran is shogi.
Action 2: Finish[Orlando Beltran].

Example 2:
Question: Who is the mother of Ivana Smith?
Action 1: RetrieveArticle[Ivana Smith].
Observation 1: No article exists for the requested entity. Please try retrieving article for another entity.
Action 2: Finish[].

Example 3:
Question: Who is the sibling of Barabara Beltran?
Action 1: RetrieveArticle[Barabara Beltran].
Observation 1: # Barabara Beltran ## Family The parents of Barabara Beltran are Dino Beltran, Shelli Beltran.  Barabara Beltran's siblings are Aida Wang, Vicki Hackworth.  The sisters of Barabara Beltran are Aida Wang, Vicki Hackworth.  The mother of Barabara Beltran is Shelli Beltran.  The father of Barabara Beltran is Dino Beltran.  ## Friends ## Attributes The date of birth of Barabara Beltran is 0989-06-11.  The occupation of Barabara Beltran is broadcast engineer.  The hobby of Barabara Beltran is meteorology.
Action 2: Finish[Aida Wang{constants.answer_sep}Vicki Hackworth].

Example 4:
Question: Who is the child of the sibling of Stacia Toombs?
Action 1: RetrieveArticle[Stacia Toombs].
Observation 1: # Stacia Toombs ## Family The parents of Stacia Toombs are Alison Smock, Williams Smock.  Stacia Toombs's sibling is Shelli Beltran.  The sister of Stacia Toombs is Shelli Beltran.  The mother of Stacia Toombs is Alison Smock.  The father of Stacia Toombs is Williams Smock.  The child of Stacia Toombs is Leslee Toombs.  The daughter of Stacia Toombs is Leslee Toombs.  The husband of Stacia Toombs is Wilbert Toombs.  ## Friends The friends of Stacia Toombs are Brian Beltran, Isiah Lutz, Leeann Hackworth, Lesley Lutz, Ryan Wang.  ## Attributes The date of birth of Stacia Toombs is 0959-03-22.  The occupation of Stacia Toombs is actuary.  The hobby of Stacia Toombs is finance.
Action 2: RetrieveArticle[Shelli Beltran].
Observation 2: # Shelli Beltran ## Family The parents of Shelli Beltran are Alison Smock, Williams Smock.  Shelli Beltran's sibling is Stacia Toombs.  The sister of Shelli Beltran is Stacia Toombs.  The mother of Shelli Beltran is Alison Smock.  The father of Shelli Beltran is Williams Smock.  The children of Shelli Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth.  The daughters of Shelli Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth.  The husband of Shelli Beltran is Dino Beltran.  ## Friends The friends of Shelli Beltran are Brian Beltran, Eli Smock, Isiah Lutz, Leslee Toombs, Lesley Lutz, Ryan Wang.  ## Attributes The date of birth of Shelli Beltran is 0958-03-08.  The occupation of Shelli Beltran is occupational therapist.  The hobby of Shelli Beltran is sociology.
Action 3: Finish[Aida Wang{constants.answer_sep}Barabara Beltran{constants.answer_sep}Vicki Hackworth].

Example 5:
Question: Who is the uncle of William Smock?
Action 1: RetrieveArticle[William Smock].
Observation 1: # Williams Smock ## Family The parents of Williams Smock are Dominique Smock, Gene Smock.  The mother of Williams Smock is Dominique Smock.  The father of Williams Smock is Gene Smock.  The children of Williams Smock are Shelli Beltran, Stacia Toombs.  The daughters of Williams Smock are Shelli Beltran, Stacia Toombs.  The wife of Williams Smock is Alison Smock.  ## Friends The friend of Williams Smock is Lannie Smock.  ## Attributes The date of birth of Williams Smock is 0926-04-04.  The occupation of Williams Smock is clinical biochemist.  The hobby of Williams Smock is social studies.
Action 2: RetrieveArticle[Dominique Smock].
Observation 2: # Dominique Smock ## Family The child of Dominique Smock is Williams Smock.  The son of Dominique Smock is Williams Smock.  The husband of Dominique Smock is Gene Smock.  ## Friends The friends of Dominique Smock are Gene Smock, Isiah Lutz, Orlando Beltran, Vicki Hackworth.  ## Attributes The date of birth of Dominique Smock is 0897-09-08.  The occupation of Dominique Smock is sports therapist.  The hobby of Dominique Smock is dominoes.
Action 3: RetrieveArticle[Gene Smock].
Observation 3: # Gene Smock ## Family The parents of Gene Smock are Alvaro Smock, Lannie Smock.  Gene Smock's sibling is Eli Smock.  The brother of Gene Smock is Eli Smock.  The mother of Gene Smock is Lannie Smock.  The father of Gene Smock is Alvaro Smock.  The child of Gene Smock is Williams Smock.  The son of Gene Smock is Williams Smock.  The wife of Gene Smock is Dominique Smock.  ## Friends The friends of Gene Smock are Leeann Hackworth, Leisa Lutz, Ricardo Hackworth, Alvaro Smock, Dominique Smock.  ## Attributes The date of birth of Gene Smock is 0898-08-16.  The occupation of Gene Smock is immunologist.  The hobby of Gene Smock is architecture.
Action 4: Finish[Eli Smock].

Example 6:
Question: What is the occupation of the sister of the grandmother of Virgil Hackworth?
Action 1: RetrieveArticle[Virgil Hackworth].
Observation 1: # Virgil Hackworth ## Family The parents of Virgil Hackworth are Ricardo Hackworth, Vicki Hackworth.  Virgil Hackworth's siblings are Leeann Hackworth, Leisa Lutz.  The sisters of Virgil Hackworth are Leeann Hackworth, Leisa Lutz.  The mother of Virgil Hackworth is Vicki Hackworth.  The father of Virgil Hackworth is Ricardo Hackworth.  ## Friends The friends of Virgil Hackworth are Alison Smock, Eli Smock, Orlando Beltran, Ryan Wang.  ## Attributes The date of birth of Virgil Hackworth is 1009-06-23.  The occupation of Virgil Hackworth is sound technician.  The hobby of Virgil Hackworth is wikipedia editing.
Action 2: RetrieveArticle[Ricardo Hackworth].
Observation 2: # Ricardo Hackworth ## Family The children of Ricardo Hackworth are Leeann Hackworth, Leisa Lutz, Virgil Hackworth.  The son of Ricardo Hackworth is Virgil Hackworth.  The daughters of Ricardo Hackworth are Leeann Hackworth, Leisa Lutz.  The wife of Ricardo Hackworth is Vicki Hackworth.  ## Friends The friends of Ricardo Hackworth are Gene Smock, Isiah Lutz, Johnetta Wang.  ## Attributes The date of birth of Ricardo Hackworth is 0983-02-24.  The occupation of Ricardo Hackworth is clinical research associate.  The hobby of Ricardo Hackworth is dairy farming.
Action 3: RetrieveArticle[Vicki Hackworth].
Observation 3: # Vicki Hackworth ## Family The parents of Vicki Hackworth are Dino Beltran, Shelli Beltran.  Vicki Hackworth's siblings are Aida Wang, Barabara Beltran.  The sisters of Vicki Hackworth are Aida Wang, Barabara Beltran.  The mother of Vicki Hackworth is Shelli Beltran.  The father of Vicki Hackworth is Dino Beltran.  The children of Vicki Hackworth are Leeann Hackworth, Leisa Lutz, Virgil Hackworth.  The son of Vicki Hackworth is Virgil Hackworth.  The daughters of Vicki Hackworth are Leeann Hackworth, Leisa Lutz.  The husband of Vicki Hackworth is Ricardo Hackworth.  ## Friends The friends of Vicki Hackworth are Brian Beltran, Dominique Smock, Eli Smock.  ## Attributes The date of birth of Vicki Hackworth is 0985-05-30.  The occupation of Vicki Hackworth is police officer.  The hobby of Vicki Hackworth is meditation.
Action 4: RetrieveArticle[Shelli Beltran].
Observation 4: # Shelli Beltran ## Family The parents of Shelli Beltran are Alison Smock, Williams Smock.  Shelli Beltran's sibling is Stacia Toombs.  The sister of Shelli Beltran is Stacia Toombs.  The mother of Shelli Beltran is Alison Smock.  The father of Shelli Beltran is Williams Smock.  The children of Shelli Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth.  The daughters of Shelli Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth.  The husband of Shelli Beltran is Dino Beltran.  ## Friends The friends of Shelli Beltran are Brian Beltran, Eli Smock, Isiah Lutz, Leslee Toombs, Lesley Lutz, Ryan Wang.  ## Attributes The date of birth of Shelli Beltran is 0958-03-08.  The occupation of Shelli Beltran is occupational therapist.  The hobby of Shelli Beltran is sociology.
Action 5: RetrieveArticle[Stacia Toombs].
Observation 5: # Stacia Toombs ## Family The parents of Stacia Toombs are Alison Smock, Williams Smock.  Stacia Toombs's sibling is Shelli Beltran.  The sister of Stacia Toombs is Shelli Beltran.  The mother of Stacia Toombs is Alison Smock.  The father of Stacia Toombs is Williams Smock.  The child of Stacia Toombs is Leslee Toombs.  The daughter of Stacia Toombs is Leslee Toombs.  The husband of Stacia Toombs is Wilbert Toombs.  ## Friends The friends of Stacia Toombs are Brian Beltran, Isiah Lutz, Leeann Hackworth, Lesley Lutz, Ryan Wang.  ## Attributes The date of birth of Stacia Toombs is 0959-03-22.  The occupation of Stacia Toombs is actuary.  The hobby of Stacia Toombs is finance.
Action 6: Finish[actuary].

Example 7:
Question: Who is the brother of the person whose occupation is associate professor?
Action 1: Search[associate professor].
Observation 1: (1) Dino Beltran
Action 2: RetrieveArticle[Dino Beltran].
Observation 2: # Dino Beltran ## Family The parents of Dino Beltran are Brian Beltran, Daisy Beltran.  Dino Beltran's sibling is Orlando Beltran.  The brother of Dino Beltran is Orlando Beltran.  The mother of Dino Beltran is Daisy Beltran.  The father of Dino Beltran is Brian Beltran.  The children of Dino Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth.  The daughters of Dino Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth.  The wife of Dino Beltran is Shelli Beltran.  ## Friends The friend of Dino Beltran is Alvaro Smock.  ## Attributes The date of birth of Dino Beltran is 0958-08-09.  The occupation of Dino Beltran is associate professor.  The hobby of Dino Beltran is shogi.
Action 3: Finish[Orlando Beltran].

Example 8:
Question: What is the date of birth of the person whose hobby is meteorology?
Action 1: Search[meteorology].
Observation 1: (1) Alison Smock (2) Barabara Beltran
Action 2: RetrieveArticle[Alison Smock].
Observation 2: # Alison Smock ## Family The children of Alison Smock are Shelli Beltran, Stacia Toombs.  The daughters of Alison Smock are Shelli Beltran, Stacia Toombs.  The husband of Alison Smock is Williams Smock.  ## Friends The friends of Alison Smock are Eli Smock, Lannie Smock, Virgil Hackworth.  ## Attributes The date of birth of Alison Smock is 0929-10-28.  The occupation of Alison Smock is health promotion specialist.  The hobby of Alison Smock is meteorology.
Action 3: RetrieveArticle[Barabara Beltran].
Observation 3: # Barabara Beltran ## Family The parents of Barabara Beltran are Dino Beltran, Shelli Beltran.  Barabara Beltran's siblings are Aida Wang, Vicki Hackworth.  The sisters of Barabara Beltran are Aida Wang, Vicki Hackworth.  The mother of Barabara Beltran is Shelli Beltran.  The father of Barabara Beltran is Dino Beltran.  ## Friends ## Attributes The date of birth of Barabara Beltran is 0989-06-11.  The occupation of Barabara Beltran is broadcast engineer.  The hobby of Barabara Beltran is meteorology.
Action 4: Finish[0929-10-28{constants.answer_sep}0989-06-11].

Example 9:
Question: Who is the cousin of the person whose occupation is broadcast engineer?
Action 1: Search[broadcast engineer].
Observation 1: # Barabara Beltran ## Family The parents of Barabara Beltran are Dino Beltran, Shelli Beltran.  Barabara Beltran's siblings are Aida Wang, Vicki Hackworth.  The sisters of Barabara Beltran are Aida Wang, Vicki Hackworth.  The mother of Barabara Beltran is Shelli Beltran.  The father of Barabara Beltran is Dino Beltran.  ## Friends ## Attributes The date of birth of Barabara Beltran is 0989-06-11.  The occupation of Barabara Beltran is broadcast engineer.  The hobby of Barabara Beltran is meteorology.
Action 2: RetrieveArticle[Dino Beltran].
Observation 2: # Dino Beltran ## Family The parents of Dino Beltran are Brian Beltran, Daisy Beltran.  Dino Beltran's sibling is Orlando Beltran.  The brother of Dino Beltran is Orlando Beltran.  The mother of Dino Beltran is Daisy Beltran.  The father of Dino Beltran is Brian Beltran.  The children of Dino Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth.  The daughters of Dino Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth.  The wife of Dino Beltran is Shelli Beltran.  ## Friends The friend of Dino Beltran is Alvaro Smock.  ## Attributes The date of birth of Dino Beltran is 0958-08-09.  The occupation of Dino Beltran is associate professor.  The hobby of Dino Beltran is shogi.
Action 3: RetrieveArticle[Orlando Beltran].
Observation 3: # Orlando Beltran ## Family The parents of Orlando Beltran are Brian Beltran, Daisy Beltran.  Orlando Beltran's sibling is Dino Beltran.  The brother of Orlando Beltran is Dino Beltran.  The mother of Orlando Beltran is Daisy Beltran.  The father of Orlando Beltran is Brian Beltran.  ## Friends The friends of Orlando Beltran are Virgil Hackworth, Dominique Smock.  ## Attributes The date of birth of Orlando Beltran is 0953-10-23.  The occupation of Orlando Beltran is petroleum engineer.  The hobby of Orlando Beltran is learning.
Action 4: RetrieveArticle[Shelli Beltran].
Observation 4: # Shelli Beltran ## Family The parents of Shelli Beltran are Alison Smock, Williams Smock.  Shelli Beltran's sibling is Stacia Toombs.  The sister of Shelli Beltran is Stacia Toombs.  The mother of Shelli Beltran is Alison Smock.  The father of Shelli Beltran is Williams Smock.  The children of Shelli Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth.  The daughters of Shelli Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth.  The husband of Shelli Beltran is Dino Beltran.  ## Friends The friends of Shelli Beltran are Brian Beltran, Eli Smock, Isiah Lutz, Leslee Toombs, Lesley Lutz, Ryan Wang.  ## Attributes The date of birth of Shelli Beltran is 0958-03-08.  The occupation of Shelli Beltran is occupational therapist.  The hobby of Shelli Beltran is sociology.
Action 5: RetrieveArticle[Stacia Toombs].
Observation 5: # Stacia Toombs ## Family The parents of Stacia Toombs are Alison Smock, Williams Smock.  Stacia Toombs's sibling is Shelli Beltran.  The sister of Stacia Toombs is Shelli Beltran.  The mother of Stacia Toombs is Alison Smock.  The father of Stacia Toombs is Williams Smock.  The child of Stacia Toombs is Leslee Toombs.  The daughter of Stacia Toombs is Leslee Toombs.  The husband of Stacia Toombs is Wilbert Toombs.  ## Friends The friends of Stacia Toombs are Brian Beltran, Isiah Lutz, Leeann Hackworth, Lesley Lutz, Ryan Wang.  ## Attributes The date of birth of Stacia Toombs is 0959-03-22.  The occupation of Stacia Toombs is actuary.  The hobby of Stacia Toombs is finance.
Action 6: Finish[Leslee Toombs].

Example 10:
Question: Who is the great-granddaughter of the person whose hobby is biology?
Action 1: Search[biology].
Observation 1: (1) Alvaro Smock
Action 2: RetrieveArticle[Alvaro Smock].
Observation 2: # Alvaro Smock ## Family The children of Alvaro Smock are Eli Smock, Gene Smock.  The sons of Alvaro Smock are Eli Smock, Gene Smock.  The wife of Alvaro Smock is Lannie Smock.  ## Friends The friends of Alvaro Smock are Dino Beltran, Gene Smock, Aida Wang.  ## Attributes The date of birth of Alvaro Smock is 0867-07-12.  The occupation of Alvaro Smock is osteopath.  The hobby of Alvaro Smock is biology.
Action 3: RetrieveArticle[Eli Smock].
Observation 3: # Eli Smock ## Family The parents of Eli Smock are Alvaro Smock, Lannie Smock.  Eli Smock's sibling is Gene Smock.  The brother of Eli Smock is Gene Smock.  The mother of Eli Smock is Lannie Smock.  The father of Eli Smock is Alvaro Smock.  ## Friends The friends of Eli Smock are Leisa Lutz, Shelli Beltran, Vicki Hackworth, Virgil Hackworth, Alison Smock, Brian Beltran.  ## Attributes The date of birth of Eli Smock is 0901-01-18.  The occupation of Eli Smock is retail manager.  The hobby of Eli Smock is tether car.
Action 4: RetrieveArticle[Gene Smock].
Observation 4: # Gene Smock ## Family The parents of Gene Smock are Alvaro Smock, Lannie Smock.  Gene Smock's sibling is Eli Smock.  The brother of Gene Smock is Eli Smock.  The mother of Gene Smock is Lannie Smock.  The father of Gene Smock is Alvaro Smock.  The child of Gene Smock is Williams Smock.  The son of Gene Smock is Williams Smock.  The wife of Gene Smock is Dominique Smock.  ## Friends The friends of Gene Smock are Leeann Hackworth, Leisa Lutz, Ricardo Hackworth, Alvaro Smock, Dominique Smock.  ## Attributes The date of birth of Gene Smock is 0898-08-16.  The occupation of Gene Smock is immunologist.  The hobby of Gene Smock is architecture.
Action 5: RetrieveArticle[Williams Smock].
Observation 5: # Williams Smock ## Family The parents of Williams Smock are Dominique Smock, Gene Smock.  The mother of Williams Smock is Dominique Smock.  The father of Williams Smock is Gene Smock.  The children of Williams Smock are Shelli Beltran, Stacia Toombs.  The daughters of Williams Smock are Shelli Beltran, Stacia Toombs.  The wife of Williams Smock is Alison Smock.  ## Friends The friend of Williams Smock is Lannie Smock.  ## Attributes The date of birth of Williams Smock is 0926-04-04.  The occupation of Williams Smock is clinical biochemist.  The hobby of Williams Smock is social studies.
Action 6: Finish[Shelli Beltran{constants.answer_sep}Stacia Toombs].
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
        case "zeroshot" | "zeroshot-sc" | "reasoning":
            return ZeroshotLLMPrompt()
        case "fewshot" | "fewshot-sc" | "fewshot-retriever":
            return FewshotLLMPrompt()
        case "cot" | "cot-sc" | "cot-sc->react" | "cot-retriever":
            return CoTLLMPrompt()
        case "retriever":
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

