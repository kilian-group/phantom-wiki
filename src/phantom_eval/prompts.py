import abc

from langchain.prompts import PromptTemplate

from phantom_eval import constants, llm
from phantom_eval.llm import is_huggingface_model
from phantom_eval.llm.anthropic import AnthropicChat
from phantom_eval.llm.gemini import GeminiChat
from phantom_eval.llm.openai import OpenAIChat
from phantom_eval.llm.together import TogetherChat


class LLMPrompt(abc.ABC):
    @abc.abstractmethod
    def get_prompt(self, prolog_query: bool = False) -> PromptTemplate:
        """Get the prompt template for this LLM prompt.

        Args:
            prolog_query: If True, returns a prompt template that instructs the LLM to generate a Prolog query.
                         If False, returns a prompt template that instructs the LLM to generate a direct answer.

        Returns:
            A PromptTemplate object containing the prompt template.
        """


##### Zeroshot method
class ZeroshotLLMPrompt(LLMPrompt):
    ZEROSHOT_INSTRUCTION_PROLOG = f"""
    You are given the following evidence:
    (BEGIN EVIDENCE)
    {{evidence}}
    (END EVIDENCE)

    You will be provided a question. Your task is to generate the prolog query that will retrieve the answer to the question.
    - DO NOT include any additional information in your answer.

    Question: {{question}}
    Answer: """

    ZEROSHOT_INSTRUCTION = f"""
    You are given the following evidence:
    (BEGIN EVIDENCE)
    {{evidence}}
    (END EVIDENCE)

    You will be provided a question. Your task is to provide an answer according to these instructions:
    - The output must be one of the following: a name (if there is only one correct answer); or a list of names separated by '{constants.answer_sep}' (if there are multiple correct answers); or numbers separated by '{constants.answer_sep}' (if the answer is numerical).
    - DO NOT include any additional information in your answer.

    Question: {{question}}
    Answer: """

    def get_prompt(self, prolog_query: bool = False) -> PromptTemplate:
        """Get the zeroshot prompt template.

        Args:
            prolog_query: If True, returns a prompt template that instructs the LLM to generate a Prolog query.
                         If False, returns a prompt template that instructs the LLM to generate a direct answer.

        Returns:
            A PromptTemplate object containing the zeroshot prompt template.
        """
        if prolog_query:
            return PromptTemplate(
                input_variables=["evidence", "question"],
                template=self.ZEROSHOT_INSTRUCTION_PROLOG,
            )
        else:
            return PromptTemplate(
                input_variables=["evidence", "question"],
                template=self.ZEROSHOT_INSTRUCTION,
            )


##### Fewshot method
# The current example is the example from CoT trivially adapted
FEWSHOT_EXAMPLES_PROLOG = f"""
Example 1:
Question: Who is the brother of Dino Beltran?
Answer: brother(X, "Dino Beltran")

Example 2:
Question: Who is the sibling of Barabara Beltran?
Answer: sibling(X, "Barabara Beltran")

Example 3:
Question: Who is the mother of the sister of Stacia Toombs?
Answer: sister("Stacia Toombs", Y), mother(Y, X)

Example 4:
Question: Who is the male second cousin of the uncle of William Smock?
Answer: uncle("William Smock", X), male_second_cousin(X, Y)

Example 5:
Question: What is the occupation of the sister of the grandmother of Virgil Hackworth?
Answer: grandmother("Virgil Hackworth", Z), sister(Z, Y), job(Y, X)

Example 6:
Question: Who is the wife of the person whose occupation is associate professor?
Answer: job(X, "associate professor"), wife(X, Y)

Example 7:
Question: What is the date of birth of the person whose hobby is meteorology?
Answer: hobby(X, "meteorology"), dob(X, Y)

Example 8:
Question: Who is the granddaughter of the mother of the friend of the friend of the mother of the parent of the friend of the great-granddaughter of the person whose occupation is theatre manager?
Answer: job(A, "theatre manager"), great_granddaughter(A, B), friend(B, C), parent(C, D), mother(D, E), friend(E, F), friend(F, G), mother(G, H), granddaughter(H, I)

Example 9:
Question: How many friends does the child of Alvaro Smock have?
Answer: child("Alvaro Smock", A), aggregate_all(count, friend(A, B), C)

Example 10:
Question: How many uncles does the maternal grandmother of the friend of Stacia Toombs have?
Answer: friend("Stacia Toombs", A), mother(A, B), mother(B, C), aggregate_all(count, uncle(C, D), E)
"""

FEWSHOT_EXAMPLES = f"""
Example 1:
Question: Who is the sister of Aida Wang?
Answer: Barabara Beltran{constants.answer_sep}Vicki Hackworth

Example 2:
Question: Who is the child of Alvaro Smock?
Answer: Eli Smock{constants.answer_sep}Gene Smock

Example 3:
Question: Who is the friend of the child of Alvaro Smock?
Answer: Leisa Lutz{constants.answer_sep}Shelli Beltran{constants.answer_sep}Vicki Hackworth{constants.answer_sep}Virgil Hackworth{constants.answer_sep}Alison Smock{constants.answer_sep}Brian Beltran{constants.answer_sep}Leeann Hackworth{constants.answer_sep}Ricardo Hackworth{constants.answer_sep}Dominique Smock

Example 4:
Question: Who is the aunt of Vicki Hackworth?
Answer: Stacia Toombs

Example 5:
Question: What is the occupation of the husband of Stacia Toombs?
Answer: theatre manager

Example 6:
Question: What is the hobby of the daughter-in-law of Lannie Smock?
Answer: dominoes

Example 7:
Question: What is the date of birth of the person whose hobby is finance?
Answer: 0959-03-22

Example 8:
Question: Who is the great-granddaughter of the person whose occupation is biomedical scientist?
Answer: Shelli Beltran{constants.answer_sep}Stacia Toombs

Example 9:
Question: How many friends does Ryan Wang have?
Answer: 4

Example 10:
Question: How many friends does the child of Alvaro Smock have?
Answer: 6{constants.answer_sep}5

Example 11:
Question: How many uncles does the friend of Stacia Toombs have?
Answer: 0{constants.answer_sep}1
"""


class FewshotLLMPrompt(LLMPrompt):
    FEWSHOT_INSTRUCTION_PROLOG = f"""
    You are given the following evidence:
    (BEGIN EVIDENCE)
    {{evidence}}
    (END EVIDENCE)

    You will be provided a question. Your task is to provide a prolog query that will retrieve the answer to the question.
    - DO NOT include any additional information in your answer.

    Here are some examples:
    (START OF EXAMPLES)
    {{examples}}
    (END OF EXAMPLES)

    Question: {{question}}
    Answer: """

    FEWSHOT_INSTRUCTION = f"""
    You are given the following evidence:
    (BEGIN EVIDENCE)
    {{evidence}}
    (END EVIDENCE)

    You will be provided a question. Your task is to provide an answer according to these instructions:
    - The output must be one of the following: a name (if there is only one correct answer); or a list of names separated by '{constants.answer_sep}' (if there are multiple correct answers); or numbers separated by '{constants.answer_sep}' (if the answer is numerical).
    - DO NOT include any additional information in your answer.

    Here are some examples:
    (START OF EXAMPLES)
    {{examples}}
    (END OF EXAMPLES)

    Question: {{question}}
    Answer: """

    def get_prompt(self, prolog_query: bool = False) -> PromptTemplate:
        """Get the fewshot prompt template.

        Args:
            prolog_query: If True, returns a prompt template that instructs the LLM to generate a Prolog query.
                         If False, returns a prompt template that instructs the LLM to generate a direct answer.

        Returns:
            A PromptTemplate object containing the fewshot prompt template.
        """
        if prolog_query:
            return PromptTemplate(
                input_variables=["evidence", "examples", "question"],
                template=self.FEWSHOT_INSTRUCTION_PROLOG,
            )
        else:
            return PromptTemplate(
                input_variables=["evidence", "examples", "question"],
                template=self.FEWSHOT_INSTRUCTION,
            )


##### CoT method
COT_EXAMPLES_PROLOG = f"""
Example 1:
Question: Who is the brother of Dino Beltran?
Answer: I can get the brother of Dino Beltran with the query brother(X, "Dino Beltran"). Therefore, the answer is brother(X, "Dino Beltran").
Example 2:
Question: Who is the sibling of Barabara Beltran?
Answer: I can get the sibling of Barbara Beltran with the query sibling(X, "Barabara Beltran"). Therefore, the answer is sibling(X, "Barabara Beltran").
Example 3:
Question: Who is the mother of the sister of Stacia Toombs?
Answer: I can get the sister of Stacia Toombs with the query sister("Stacia Toombs", Y). Since Y is the sister of Stacia Toombs, I can get the mother of Y with the query mother(Y, X). Therefore, the answer is sister("Stacia Toombs", Y), mother(Y, X).
Example 4:
Question: Who is the male second cousin of the uncle of William Smock?
Answer: I can get the uncle of William Smock with the query uncle("William Smock", X). Since X is the uncle of William Smock, I can get the male second cousin of X with the query male_second_cousin(X, Y). Therefore, the answer is uncle("William Smock", X), male_second_cousin(X, Y).
Example 5:
Question: What is the occupation of the sister of the grandmother of Virgil Hackworth?
Answer: I can get the grandmother of Virgil Hackworth with the query grandmother("Virgil Hackworth", Z). Since Z is the grandmother of Virgil Hackworth, I can get the sister of Z with the query sister(Z, Y). Since Y is the sister of the grandmother of Virgil Hackworth, I can get the occupation of Y with the query job(Y, X). Therefore, the answer is grandmother("Virgil Hackworth", Z), sister(Z, Y), job(Y, X).
Example 6:
Question: Who is the wife of the person whose occupation is associate professor?
Answer: I can get the person whose occupation is associate professor with the query job(X, "associate professor"). Since X is the person whose occupation is associate professor, I can get the wife of X with the query wife(X, Y). Therefore, the answer is job(X, "associate professor"), wife(X, Y).
Example 7:
Question: What is the date of birth of the person whose hobby is meteorology?
Answer: I can get the person whose hobby is meteorology with the query hobby(X, "meteorology"). Since X is the person whose hobby is meteorology, I can get the date of birth of X with the query dob(X, Y). Therefore, the answer is hobby(X, "meteorology"), dob(X, Y).
Example 8:
Question: Who is the cousin of the person whose hobby is broadcast engineer?
Answer: I can get the person whose hobby is broadcast engineer with the query hobby(Y, "broadcast engineer"). Since Y is the person whose hobby is broadcast engineer, I can get the cousin of Y with the query cousin(Y, X). Therefore, the answer is hobby(Y, "broadcast engineer"), cousin(Y, X).
Example 9:
Question: Who is the granddaughter of the mother of the friend of the friend of the mother of the parent of the friend of the great-granddaughter of the person whose occupation is theatre manager?
Answer: I can get the person whose occupation is theatre manager with the query job(A, "theatre manager"). Since A is the person whose occupation is theatre manager, I can get the great-granddaughter of A with the query great_granddaughter(A, B). Since B is the great-granddaughter of the person whose occupation is theatre manager, I can get the friend of B with the query friend(B, C). Since C is the friend of the great-granddaughter of the person whose occupation is theatre manager, I can get the parent of C with the query parent(C, D). Since D is the parent of the friend of the great-granddaughter of the person whose occupation is theatre manager, I can get the mother of D with the query mother(D, E). Since E is the mother of the parent of the friend of the great-granddaughter of the person whose occupation is theatre manager, I can get the friend of E with the query friend(E, F). Since F is the friend of the mother of the parent of the friend of the great-granddaughter of the person whose occupation is theatre manager, I can get the friend of F with the query friend(F, G). Since G is the friend of the friend of the mother of the parent of the friend of the great-granddaughter of the person whose occupation is theatre manager, I can get the mother of G with the query mother(G, H). Since H is the mother of the friend of the friend of the mother of the parent of the friend of the great-granddaughter of the person whose occupation is theatre manager, I can get the granddaughter of H with the query granddaughter(H, I). Therefore, the answer is job(A, "theatre manager"), great_granddaughter(A, B), friend(B, C), parent(C, D), mother(D, E), friend(E, F), friend(F, G), mother(G, H), granddaughter(H, I).
Example 9:
Question: How many friends does the child of Alvaro Smock have?
Answer: I can get the child of Alvaro Smock with the query child("Alvaro Smock", A). Since A is the child of Alvaro Smock, I can get the number of friends of A with the query findall(B, friend(A, B), C), length(C, D). Therefore, the answer is child("Alvaro Smock", A), findall(B, friend(A, B), C), length(C, D).
Example 10:
Question: How many uncles does the maternal grandmother of the friend of Stacia Toombs have?
Answer: I can get the friend of Stacia Toombs with the query friend("Stacia Toombs", A). Since A is the friend of Stacia Toombs, I can get the maternal grandmother of A with the query mother(A, B), mother(B, C). Since D is the maternal grandmother of the friend of Stacia Toombs, I can get the number of uncles of D with the query findall(E, uncle(D, E), F), length(F, G). Therefore, the answer is friend("Stacia Toombs", A), mother(A, B), mother(B, C), findall(E, uncle(D, E), F), length(F, G).
"""

COT_EXAMPLES = f"""
Example 1:
Question: Who is the sister of Aida Wang?
Answer: Based on the evidence, the sisters of Aida Wang are Barabara Beltran, Vicki Hackworth. The answer is Barabara Beltran{constants.answer_sep}Vicki Hackworth.

Example 2:
Question: Who is the child of Alvaro Smock?
Answer: Based on the evidence, the children of Alvaro Smock are Eli Smock, Gene Smock. The answer is Eli Smock{constants.answer_sep}Gene Smock.

Example 3:
Question: Who is the friend of the child of Alvaro Smock?
Answer: First I need to find the children of Alvaro Smock. Based on the evidence, the children of Alvaro Smock are Eli Smock, Gene Smock. Now I need to find the friends of Eli Smock and Gene Smock. Based on the evidence, the friends of Eli Smock are Leisa Lutz, Shelli Beltran, Vicki Hackworth, Virgil Hackworth, Alison Smock, Brian Beltran. The friends of Gene Smock are Leeann Hackworth, Leisa Lutz, Ricardo Hackworth, Alvaro Smock, Dominique Smock. The answer is Leisa Lutz{constants.answer_sep}Shelli Beltran{constants.answer_sep}Vicki Hackworth{constants.answer_sep}Virgil Hackworth{constants.answer_sep}Alison Smock{constants.answer_sep}Brian Beltran{constants.answer_sep}Leeann Hackworth{constants.answer_sep}Ricardo Hackworth{constants.answer_sep}Dominique Smock.

Example 4:
Question: Who is the aunt of Vicki Hackworth?
Answer: An aunt is the sister of a parent. Based on the evidence, the parents of Vicki Hackworth are Shelli Beltran, Dino Beltran. To find the aunt of Vicki Hackworth, I need to find the sister of Shelli Beltran and Dino Beltran. Based on the evidence, Shelli Beltran has no sister, and the sister of Dino Beltran is Stacia Toombs. The answer is Stacia Toombs.

Example 5:
Question: What is the occupation of the husband of Stacia Toombs?
Answer: Based on the evidence, the husband of Stacia Toombs is Wilbert Toombs. The occupation of Wilbert Toombs is theatre manager. The answer is theatre manager.

Example 6:
Question: What is the hobby of the daughter-in-law of Lannie Smock?
Answer: A daughter-in-law is the wife of a child. Based on the evidence, the children of Lannie Smock are Eli Smock, Gene Smock. Eli Smock has no wife, and the wife of Gene Smock is Dominique Smock. The hobby of Dominique Smock is dominoes. The answer is dominoes.

Example 7:
Question: What is the date of birth of the person whose hobby is finance?
Answer: I need to search for people whose hobby is finance. Based on the evidence, the person whose hobby is finance is Stacia Toombs. The date of birth of Stacia Toombs is 0959-03-22. The answer is 0959-03-22.

Example 8:
Question: Who is the great-granddaughter of the person whose occupation is biomedical scientist?
Answer: I need to search for people whose occupation is biomedical scientist. Based on the evidence, the person whose occupation is biomedical scientist is Lannie Smock. To find the great-granddaughter of Lannie Smock, I need to find the daughter of the child of the child of Lannie Smock. Based on the evidence, the children of Lannie Smock are Eli Smock, Gene Smock. Eli Smock has no child, and the child of Gene Smock is Williams Smock. The daughters of Williams Smock are Shelli Beltran, Stacia Toombs. The answer is Shelli Beltran{constants.answer_sep}Stacia Toombs.

Example 9:
Question: How many friends does Ryan Wang have?
Answer: Based on the evidence, the friends of Ryan Wang are Shelli Beltran, Stacia Toombs, Virgil Hackworth, Aida Wang. The answer is 4.

Example 10:
Question: How many friends does the child of Alvaro Smock have?
Answer: First, I need to find the children of Alvaro Smock. Based on the evidence, the children of Alvaro Smock are Eli Smock, Gene Smock. Now I need to find how many friends they have. Based on the evidence, the friends of Eli Smock are Leisa Lutz, Shelli Beltran, Vicki Hackworth, Virgil Hackworth, Alison Smock, Brian Beltran. The friends of Gene Smock are Leeann Hackworth, Leisa Lutz, Ricardo Hackworth, Alvaro Smock, Dominique Smock. The answer is 6{constants.answer_sep}5.

Example 11:
Question: How many uncles does the friend of Stacia Toombs have?
Answer: First, I need to find the friends of Stacia Toombs. Based on the evidence, the friends of Stacia Toombs are Brian Beltran, Isiah Lutz, Leeann Hackworth, Lesley Lutz, Ryan Wang.  Now I need to find how many uncles they have.  An uncle is the brother of a parent.  Based on the evidence, Brian Beltran has no parents, Isiah Lutz has no parents, Leeann Hackworth has 2 parents, Lesley Lutz has 2 parents, and Ryan Wang has no parents.  Based on the evidence, the parents of Leeann Hackworth are Vicki Hackworth, Ricardo Hackworth. But both parents do not have brothers.  Based on the evidence, the parents of Lesley Lutz are Leisa Lutz, Isiah Lutz. The brother of Leisa Lutz is Virgil Hackworth, so he is an uncle of Lesley Lutz. Isiah Lutz has no brother.  So the friends of Stacia Toombs have 0, 0, 0, 1, 0 uncles. Unique is 0, 1. The answer is 0{constants.answer_sep}1.
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
    - a list of names separated by '{constants.answer_sep}' (if there are multiple correct answers); or
    - numbers separated by '{constants.answer_sep}' (if the answer is numerical).

    Here are some examples:
    (START OF EXAMPLES)
    {{examples}}
    (END OF EXAMPLES)

    Question: {{question}}
    Answer: """

    COT_INSTRUCTION_PROLOG = f"""
    You are given the following evidence:
    (BEGIN EVIDENCE)
    {{evidence}}
    (END EVIDENCE)

    You will be provided a question. Your response must end in the following sentence: The answer is <answer>.
    Here, <answer> must be the prolog query that will retrieve the answer to the question.
    Make sure to double check the query to make sure it is syntactically correct using the following checks:
    - The query is a valid prolog query.
    - Fields that aren't variables should be enclosed in double quotes.
    - The variables in the query are capital letters.

    Here are some examples:
    (START OF EXAMPLES)
    {{examples}}
    (END OF EXAMPLES)
    Question: {{question}}
    Answer: """

    def get_prompt(self, prolog_query: bool = False) -> PromptTemplate:
        """Get the Chain-of-Thought prompt template.

        Args:
            prolog_query: If True, returns a prompt template that instructs the LLM to generate a Prolog query.
                        If False, returns a prompt template that instructs the LLM to generate a direct answer.

        Returns:
            A PromptTemplate object containing the Chain-of-Thought prompt template.
        """
        if prolog_query:
            return PromptTemplate(
                input_variables=["evidence", "examples", "question"],
                template=self.COT_INSTRUCTION_PROLOG,
            )
        else:
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
    - numbers separated by '{constants.answer_sep}' (if the answer is numerical).

    Question: {{question}}
    Answer (Your response must end in "The answer is <answer>."): """

    def get_prompt(self, prolog_query: bool = False) -> PromptTemplate:
        """Get the RAG prompt template.

        Args:
            prolog_query: This parameter is not used for RAG prompts, as they do not support Prolog query generation.

        Returns:
            A PromptTemplate object containing the RAG prompt template.
        """
        return PromptTemplate(
            input_variables=["evidence", "question"],
            template=self.RAG_INSTRUCTION,
        )


##### React method
REACT_EXAMPLES = f"""
Example 1:
Question: Who is the sister of Aida Wang?
Thought 1: I need to retrieve article about Aida Wang and find who their sister is.
Action 1: RetrieveArticle[Aida Wang].
Observation 1: # Aida Wang ## Family The sisters of Aida Wang are Barabara Beltran, Vicki Hackworth.  The mother of Aida Wang is Shelli Beltran.  The father of Aida Wang is Dino Beltran.  The daughter of Aida Wang is Johnetta Wang.  The husband of Aida Wang is Ryan Wang.  ## Friends The friends of Aida Wang are Alvaro Smock, Lannie Smock, Leslee Toombs, Ryan Wang.  ## Attributes The date of birth of Aida Wang is 0985-05-30.  The occupation of Aida Wang is personal assistant.  The hobby of Aida Wang is meditation.  The gender of Aida Wang is female.
Thought 2: The sisters of Aida Wang are Barabara Beltran, Vicki Hackworth. So the answer is Barabara Beltran, Vicki Hackworth.
Action 2: Finish[Barabara Beltran{constants.answer_sep}Vicki Hackworth].

Example 2:
Question: Who is the mother of Ivana Smith?
Thought 1: I need to retrieve article about Ivana Smith and find who her mother is.
Action 1: RetrieveArticle[Ivana Smith].
Observation 1: No article exists for the requested entity. Please try retrieving article for another entity.
Thought 2: Article about Ivana Smith does not exist, so I cannot find the mother of Ivana Smith. I will output empty answer.
Action 2: Finish[].

Example 3:
Question: Who is the child of Alvaro Smock?
Thought 1: I need to retrieve article about Alvaro Smock and find who his children are.
Action 1: RetrieveArticle[Alvaro Smock].
Observation 1: # Alvaro Smock ## Family The sons of Alvaro Smock are Eli Smock, Gene Smock.  The wife of Alvaro Smock is Lannie Smock.  ## Friends The friends of Alvaro Smock are Dino Beltran, Gene Smock, Aida Wang.  ## Attributes The date of birth of Alvaro Smock is 0867-07-12.  The occupation of Alvaro Smock is osteopath.  The hobby of Alvaro Smock is biology
Thought 2: The children of Alvaro Smock are Eli Smock, Gene Smock. So the answer is Eli Smock, Gene Smock.
Action 2: Finish[Eli Smock{constants.answer_sep}Gene Smock].

Example 4:
Question: Who is the friend of the child of Alvaro Smock?
Thought 1: First, I need to retrieve article about Alvaro Smock and find who his child is.
Action 1: RetrieveArticle[Alvaro Smock].
Observation 1: # Alvaro Smock ## Family The sons of Alvaro Smock are Eli Smock, Gene Smock.  The wife of Alvaro Smock is Lannie Smock.  ## Friends The friends of Alvaro Smock are Dino Beltran, Gene Smock, Aida Wang.  ## Attributes The date of birth of Alvaro Smock is 0867-07-12.  The occupation of Alvaro Smock is osteopath.  The hobby of Alvaro Smock is biology.  The gender of Alvaro Smock is male.
Thought 2: The children of Alvaro Smock are Eli Smock, Gene Smock. Now I need to retrieve article about Eli Smock and Gene Smock and find who their friends are.
Action 2: RetrieveArticle[Eli Smock].
Observation 2: # Eli Smock ## Family The brother of Eli Smock is Gene Smock.  The mother of Eli Smock is Lannie Smock.  The father of Eli Smock is Alvaro Smock.  ## Friends The friends of Eli Smock are Leisa Lutz, Shelli Beltran, Vicki Hackworth, Virgil Hackworth, Alison Smock, Brian Beltran.  ## Attributes The date of birth of Eli Smock is 0901-01-18.  The occupation of Eli Smock is retail manager.  The hobby of Eli Smock is tether car.  The gender of Eli Smock is male.
Thought 3: The friends of Eli Smock are Leisa Lutz, Shelli Beltran, Vicki Hackworth, Virgil Hackworth, Alison Smock, Brian Beltran. Now I need to retrieve article about Gene Smock and find who his friends are.
Action 3: RetrieveArticle[Gene Smock].
Observation 3: # Gene Smock ## Family The brother of Gene Smock is Eli Smock.  The mother of Gene Smock is Lannie Smock.  The father of Gene Smock is Alvaro Smock.  The son of Gene Smock is Williams Smock.  The wife of Gene Smock is Dominique Smock.  ## Friends The friends of Gene Smock are Leeann Hackworth, Leisa Lutz, Ricardo Hackworth, Alvaro Smock, Dominique Smock.  ## Attributes The date of birth of Gene Smock is 0898-08-16.  The occupation of Gene Smock is immunologist.  The hobby of Gene Smock is architecture.  The gender of Gene Smock is male.
Thought 4: The friends of Gene Smock are Leeann Hackworth, Leisa Lutz, Ricardo Hackworth, Alvaro Smock, Dominique Smock. And the friends of Eli Smock are Leisa Lutz, Shelli Beltran, Vicki Hackworth, Virgil Hackworth, Alison Smock, Brian Beltran. So the friends of the children of Alvaro Smock are Leisa Lutz, Shelli Beltran, Vicki Hackworth, Virgil Hackworth, Alison Smock, Brian Beltran, Leeann Hackworth, Ricardo Hackworth, Dominique Smock. The answer is Leisa Lutz, Shelli Beltran, Vicki Hackworth, Virgil Hackworth, Alison Smock, Brian Beltran, Leeann Hackworth, Ricardo Hackworth, Dominique Smock.
Action 4: Finish[Leisa Lutz{constants.answer_sep}Shelli Beltran{constants.answer_sep}Vicki Hackworth{constants.answer_sep}Virgil Hackworth{constants.answer_sep}Alison Smock{constants.answer_sep}Brian Beltran{constants.answer_sep}Leeann Hackworth{constants.answer_sep}Ricardo Hackworth{constants.answer_sep}Dominique Smock].

Example 5:
Question: Who is the aunt of Vicki Hackworth?
Thought 1: First, I need to retrieve article about Vicki Hackworth. To find the aunt of Vicki Hackworth, I need to find the sister of her parents.
Action 1: RetrieveArticle[Vicki Hackworth].
Observation 1: # Vicki Hackworth ## Family The sisters of Vicki Hackworth are Aida Wang, Barabara Beltran.  The mother of Vicki Hackworth is Shelli Beltran.  The father of Vicki Hackworth is Dino Beltran.  The son of Vicki Hackworth is Virgil Hackworth.  The daughters of Vicki Hackworth are Leeann Hackworth, Leisa Lutz.  The husband of Vicki Hackworth is Ricardo Hackworth.  ## Friends The friends of Vicki Hackworth are Brian Beltran, Dominique Smock, Eli Smock.  ## Attributes The date of birth of Vicki Hackworth is 0985-05-30.  The occupation of Vicki Hackworth is police officer.  The hobby of Vicki Hackworth is meditation.  The gender of Vicki Hackworth is female.
Thought 2: The parents of Vicki Hackworth are Shelli Beltran, Dino Beltran. To find the aunt of Vicki Hackworth, I need to find the sister of Shelli Beltran and Dino Beltran.
Action 2: RetrieveArticle[Shelli Beltran].
Observation 2: # Shelli Beltran ## Family The sister of Shelli Beltran is Stacia Toombs.  The mother of Shelli Beltran is Alison Smock.  The father of Shelli Beltran is Williams Smock.  The daughters of Shelli Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth.  The husband of Shelli Beltran is Dino Beltran.  ## Friends The friends of Shelli Beltran are Brian Beltran, Eli Smock, Isiah Lutz, Leslee Toombs, Lesley Lutz, Ryan Wang.  ## Attributes The date of birth of Shelli Beltran is 0958-03-08.  The occupation of Shelli Beltran is occupational therapist.  The hobby of Shelli Beltran is sociology.  The gender of Shelli Beltran is female.
Thought 3: The sister of Shelli Beltran is Stacia Toombs. Now I need to retrieve article about Dino Beltran and find his sister.
Action 3: RetrieveArticle[Dino Beltran].
Observation 3: # Dino Beltran ## Family The brother of Dino Beltran is Orlando Beltran.  The mother of Dino Beltran is Daisy Beltran.  The father of Dino Beltran is Brian Beltran.  The daughters of Dino Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth.  The wife of Dino Beltran is Shelli Beltran.  ## Friends The friend of Dino Beltran is Alvaro Smock.  ## Attributes The date of birth of Dino Beltran is 0958-08-09.  The occupation of Dino Beltran is associate professor.  The hobby of Dino Beltran is shogi.  The gender of Dino Beltran is male.
Thought 4: Dino Beltran has no sister, and the sister of Shelli Beltran is Stacia Toombs. So the aunt of Vicki Hackworth is Stacia Toombs. The answer is Stacia Toombs.
Action 4: Finish[Stacia Toombs].

Example 6:
Question: What is the occupation of the husband of Stacia Toombs?
Thought 1: First, I need to retrieve article about Stacia Toombs and find who her husband is.
Action 1: RetrieveArticle[Stacia Toombs].
Observation 1: # Stacia Toombs ## Family The sister of Stacia Toombs is Shelli Beltran.  The mother of Stacia Toombs is Alison Smock.  The father of Stacia Toombs is Williams Smock.  The daughter of Stacia Toombs is Leslee Toombs.  The husband of Stacia Toombs is Wilbert Toombs.  ## Friends The friends of Stacia Toombs are Brian Beltran, Isiah Lutz, Leeann Hackworth, Lesley Lutz, Ryan Wang.  ## Attributes The date of birth of Stacia Toombs is 0959-03-22.  The occupation of Stacia Toombs is actuary.  The hobby of Stacia Toombs is finance.  The gender of Stacia Toombs is female.
Thought 2: The husband of Stacia Toombs is Wilbert Toombs. Now I need to retrieve article about Wilbert Toombs and find his occupation.
Action 2: RetrieveArticle[Wilbert Toombs].
Observation 2: # Wilbert Toombs ## Family The daughter of Wilbert Toombs is Leslee Toombs.  The wife of Wilbert Toombs is Stacia Toombs.  ## Friends ## Attributes The date of birth of Wilbert Toombs is 0956-07-26.  The occupation of Wilbert Toombs is theatre manager.  The hobby of Wilbert Toombs is radio-controlled car racing.  The gender of Wilbert Toombs is male.
Thought 3: The occupation of Wilbert Toombs is theatre manager. So the answer is theatre manager.
Action 3: Finish[theatre manager].

Example 7:
Question: What is the hobby of the daughter-in-law of Lannie Smock?
Thought 1: First, I need to retrieve article about Lannie Smock and find who her daughter-in-law is. A daughter-in-law is the wife of a child.
Action 1: RetrieveArticle[Lannie Smock].
Observation 1: # Lannie Smock ## Family The sons of Lannie Smock are Eli Smock, Gene Smock.  The husband of Lannie Smock is Alvaro Smock.  ## Friends The friends of Lannie Smock are Williams Smock, Aida Wang, Alison Smock.  ## Attributes The date of birth of Lannie Smock is 0867-08-24.  The occupation of Lannie Smock is biomedical scientist.  The hobby of Lannie Smock is bus spotting.  The gender of Lannie Smock is female.
Thought 2: The sons of Lannie Smock are Eli Smock, Gene Smock. Now I need to retrieve articles about Eli Smock and Gene Smock and find their wives.
Action 2: RetrieveArticle[Eli Smock].
Observation 2: # Eli Smock ## Family The brother of Eli Smock is Gene Smock.  The mother of Eli Smock is Lannie Smock.  The father of Eli Smock is Alvaro Smock.  ## Friends The friends of Eli Smock are Leisa Lutz, Shelli Beltran, Vicki Hackworth, Virgil Hackworth, Alison Smock, Brian Beltran.  ## Attributes The date of birth of Eli Smock is 0901-01-18.  The occupation of Eli Smock is retail manager.  The hobby of Eli Smock is tether car.  The gender of Eli Smock is male.
Thought 3: Eli Smock has no wife. Now I need to retrieve article about Gene Smock and find his wife.
Action 3: RetrieveArticle[Gene Smock].
Observation 3: # Gene Smock ## Family The brother of Gene Smock is Eli Smock.  The mother of Gene Smock is Lannie Smock.  The father of Gene Smock is Alvaro Smock.  The son of Gene Smock is Williams Smock.  The wife of Gene Smock is Dominique Smock.  ## Friends The friends of Gene Smock are Leeann Hackworth, Leisa Lutz, Ricardo Hackworth, Alvaro Smock, Dominique Smock.  ## Attributes The date of birth of Gene Smock is 0898-08-16.  The occupation of Gene Smock is immunologist.  The hobby of Gene Smock is architecture.  The gender of Gene Smock is male.
Thought 4: The wife of Gene Smock is Dominique Smock, and Eli Smock has no wife. So the daughter-in-law of Lannie Smock is Dominique Smock. Now I need to retrieve article about Dominique Smock and find her hobby.
Action 4: RetrieveArticle[Dominique Smock].
Observation 4: # Dominique Smock ## Family The son of Dominique Smock is Williams Smock.  The husband of Dominique Smock is Gene Smock.  ## Friends The friends of Dominique Smock are Gene Smock, Isiah Lutz, Orlando Beltran, Vicki Hackworth.  ## Attributes The date of birth of Dominique Smock is 0897-09-08.  The occupation of Dominique Smock is sports therapist.  The hobby of Dominique Smock is dominoes.  The gender of Dominique Smock is female.
Thought 4: The hobby of Dominique Smock is dominoes. So the answer is dominoes.
Action 4: Finish[dominoes].

Example 8:
Question: What is the date of birth of the person whose hobby is finance?
Thought 1: First, I need to search for people whose hobby is finance.
Action 1: Search[finance].
Observation 1: (1) Stacia Toombs
Thought 2: The person whose hobby is finance is Stacia Toombs. Now I need to retrieve article about Stacia Toombs and find their date of birth.
Action 2: RetrieveArticle[Stacia Toombs].
Observation 2: # Stacia Toombs ## Family The sister of Stacia Toombs is Shelli Beltran.  The mother of Stacia Toombs is Alison Smock.  The father of Stacia Toombs is Williams Smock.  The daughter of Stacia Toombs is Leslee Toombs.  The husband of Stacia Toombs is Wilbert Toombs.  ## Friends The friends of Stacia Toombs are Brian Beltran, Isiah Lutz, Leeann Hackworth, Lesley Lutz, Ryan Wang.  ## Attributes The date of birth of Stacia Toombs is 0959-03-22.  The occupation of Stacia Toombs is actuary.  The hobby of Stacia Toombs is finance.  The gender of Stacia Toombs is female.
Thought 3: The date of birth of Staica Toombs is 0959-03-22. So the answer is 0959-03-22.
Action 3: Finish[0959-03-22].

Example 9:
Question: Who is the great-granddaughter of the person whose occupation is biomedical scientist?
Thought 1: First, I need to search for people whose occupation is biomedical scientist.
Action 1: Search[biomedical scientist].
Observation 1: (1) Lannie Smock
Thought 2: The person whose occupation is biomedical scientist is Lannie Smock. Now I need to retrieve article about Lannie Smock and find her great-granddaughter. A great-granddaughter is the daughter of the child of the child of the person.
Action 2: RetrieveArticle[Lannie Smock].
Observation 2: # Lannie Smock ## Family The sons of Lannie Smock are Eli Smock, Gene Smock.  The husband of Lannie Smock is Alvaro Smock.  ## Friends The friends of Lannie Smock are Williams Smock, Aida Wang, Alison Smock.  ## Attributes The date of birth of Lannie Smock is 0867-08-24.  The occupation of Lannie Smock is biomedical scientist.  The hobby of Lannie Smock is bus spotting.  The gender of Lannie Smock is female.
Thought 3: The children of Lannie Smock are Eli Smock, Gene Smock. Now I need to retrieve article about Eli Smock and Gene Smock and find their children.
Action 3: RetrieveArticle[Eli Smock].
Observation 3: # Eli Smock ## Family The brother of Eli Smock is Gene Smock.  The mother of Eli Smock is Lannie Smock.  The father of Eli Smock is Alvaro Smock.  ## Friends The friends of Eli Smock are Leisa Lutz, Shelli Beltran, Vicki Hackworth, Virgil Hackworth, Alison Smock, Brian Beltran.  ## Attributes The date of birth of Eli Smock is 0901-01-18.  The occupation of Eli Smock is retail manager.  The hobby of Eli Smock is tether car.  The gender of Eli Smock is male.
Thought 3: Eli Smock has no child. Now I need to retrieve article about Gene Smock and find his child.
Action 4: RetrieveArticle[Gene Smock].
Observation 4: # Gene Smock ## Family The brother of Gene Smock is Eli Smock.  The mother of Gene Smock is Lannie Smock.  The father of Gene Smock is Alvaro Smock.  The son of Gene Smock is Williams Smock.  The wife of Gene Smock is Dominique Smock.  ## Friends The friends of Gene Smock are Leeann Hackworth, Leisa Lutz, Ricardo Hackworth, Alvaro Smock, Dominique Smock.  ## Attributes The date of birth of Gene Smock is 0898-08-16.  The occupation of Gene Smock is immunologist.  The hobby of Gene Smock is architecture.  The gender of Gene Smock is male.
Thought 4: The child of Gene Smock is Williams Smock. Now I need to retrieve article about Williams Smock and find his daughter. This will be the great-granddaughter of Lannie Smock.
Action 5: RetrieveArticle[Williams Smock].
Observation 5: # Williams Smock ## Family The mother of Williams Smock is Dominique Smock.  The father of Williams Smock is Gene Smock.  The daughters of Williams Smock are Shelli Beltran, Stacia Toombs.  The wife of Williams Smock is Alison Smock.  ## Friends The friend of Williams Smock is Lannie Smock.  ## Attributes The date of birth of Williams Smock is 0926-04-04.  The occupation of Williams Smock is clinical biochemist.  The hobby of Williams Smock is social studies.  The gender of Williams Smock is male.
Thought 5: The daughters of Williams Smock are Shelli Beltran, Stacia Toombs. So the great-granddaughters of Lannie Smock are Shelli Beltran, Stacia Toombs. The answer is Shelli Beltran, Stacia Toombs.
Action 5: Finish[Shelli Beltran{constants.answer_sep}Stacia Toombs].

Example 10:
Question: How many friends does Ryan Wang have?
Thought 1: I need to retrieve article about Ryan Wang and find how many friends he has.
Action 1: RetrieveArticle[Ryan Wang].
Observation 1: # Ryan Wang ## Family The daughter of Ryan Wang is Johnetta Wang.  The wife of Ryan Wang is Aida Wang.  ## Friends The friends of Ryan Wang are Shelli Beltran, Stacia Toombs, Virgil Hackworth, Aida Wang.  ## Attributes The date of birth of Ryan Wang is 0982-03-17.  The occupation of Ryan Wang is chief of staff.  The hobby of Ryan Wang is fossil hunting.  The gender of Ryan Wang is male.
Thought 2: The friends of Ryan Wang are Shelli Beltran, Stacia Toombs, Virgil Hackworth, Aida Wang. So the answer is 4.
Action 2: Finish[4].

Example 11:
Question: How many friends does the child of Alvaro Smock have?
Thought 1: First, I need to retrieve article about Alvaro Smock and find who his children are.
Action 1: RetrieveArticle[Alvaro Smock].
Observation 1: # Alvaro Smock ## Family The sons of Alvaro Smock are Eli Smock, Gene Smock.  The wife of Alvaro Smock is Lannie Smock.  ## Friends The friends of Alvaro Smock are Dino Beltran, Gene Smock, Aida Wang.  ## Attributes The date of birth of Alvaro Smock is 0867-07-12.  The occupation of Alvaro Smock is osteopath.  The hobby of Alvaro Smock is biology.  The gender of Alvaro Smock is male.
Thought 2: The children of Alvaro Smock are Eli Smock, Gene Smock. Now I need to retrieve article about Eli Smock and Gene Smock and find how many friends they have.
Action 2: RetrieveArticle[Eli Smock].
Observation 2: # Eli Smock ## Family The brother of Eli Smock is Gene Smock.  The mother of Eli Smock is Lannie Smock.  The father of Eli Smock is Alvaro Smock.  ## Friends The friends of Eli Smock are Leisa Lutz, Shelli Beltran, Vicki Hackworth, Virgil Hackworth, Alison Smock, Brian Beltran.  ## Attributes The date of birth of Eli Smock is 0901-01-18.  The occupation of Eli Smock is retail manager.  The hobby of Eli Smock is tether car.  The gender of Eli Smock is male.
Thought 3: The friends of Eli Smock are Leisa Lutz, Shelli Beltran, Vicki Hackworth, Virgil Hackworth, Alison Smock, Brian Beltran. So he has 6 friends. Now I need to retrieve article about Gene Smock and find how many friends he has.
Action 3: RetrieveArticle[Gene Smock].
Observation 3: # Gene Smock ## Family The brother of Gene Smock is Eli Smock.  The mother of Gene Smock is Lannie Smock.  The father of Gene Smock is Alvaro Smock.  The son of Gene Smock is Williams Smock.  The wife of Gene Smock is Dominique Smock.  ## Friends The friends of Gene Smock are Leeann Hackworth, Leisa Lutz, Ricardo Hackworth, Alvaro Smock, Dominique Smock.  ## Attributes The date of birth of Gene Smock is 0898-08-16.  The occupation of Gene Smock is immunologist.  The hobby of Gene Smock is architecture.  The gender of Gene Smock is male.
Thought 4: The friends of Gene Smock are Leeann Hackworth, Leisa Lutz, Ricardo Hackworth, Alvaro Smock, Dominique Smock. So he has 5 friends. The answer is 6, 5.
Action 4: Finish[6{constants.answer_sep}5].

Example 12:
Question: How many uncles does the friend of Stacia Toombs have?
Thought 1: First, I need to retrieve article about Stacia Toombs and find who her friends are.
Action 1: RetrieveArticle[Stacia Toombs].
Observation 1: # Stacia Toombs ## Family The sister of Stacia Toombs is Shelli Beltran.  The mother of Stacia Toombs is Alison Smock.  The father of Stacia Toombs is Williams Smock.  The daughter of Stacia Toombs is Leslee Toombs.  The husband of Stacia Toombs is Wilbert Toombs.  ## Friends The friends of Stacia Toombs are Brian Beltran, Isiah Lutz, Leeann Hackworth, Lesley Lutz, Ryan Wang.  ## Attributes The date of birth of Stacia Toombs is 0959-03-22.  The occupation of Stacia Toombs is actuary.  The hobby of Stacia Toombs is finance.  The gender of Stacia Toombs is female.
Thought 2: The friends of Stacia Toombs are Brian Beltran, Isiah Lutz, Leeann Hackworth, Lesley Lutz, Ryan Wang. Now I need to retrieve articles about each of them and find how many uncles they have. An uncle is the brother of a parent.
Action 2: RetrieveArticle[Brian Beltran].
Observation 2: # Brian Beltran ## Family The sons of Brian Beltran are Dino Beltran, Orlando Beltran.  The wife of Brian Beltran is Daisy Beltran.  ## Friends The friends of Brian Beltran are Eli Smock, Leeann Hackworth, Shelli Beltran, Stacia Toombs, Vicki Hackworth.  ## Attributes The date of birth of Brian Beltran is 0927-07-27.  The occupation of Brian Beltran is oncologist.  The hobby of Brian Beltran is dolls.  The gender of Brian Beltran is male.
Thought 3: Brian Beltran has no parent, hence 0 uncles of Brian Beltran. So I can move on to the next friend. Now I need to retrieve article about Isiah Lutz and find how many uncles he has.
Action 3: RetrieveArticle[Isiah Lutz].
Observation 3: # Isiah Lutz ## Family The son of Isiah Lutz is Lesley Lutz.  The wife of Isiah Lutz is Leisa Lutz.  ## Friends The friends of Isiah Lutz are Johnetta Wang, Ricardo Hackworth, Shelli Beltran, Stacia Toombs, Dominique Smock.  ## Attributes The date of birth of Isiah Lutz is 1014-10-18.  The occupation of Isiah Lutz is education administrator.  The hobby of Isiah Lutz is geocaching.  The gender of Isiah Lutz is male.
Thought 4: Isiah Lutz has no parent, hence 0 uncles of Isiah Lutz. So I can move on to the next friend. Now I need to retrieve article about Leeann Hackworth and find how many uncles she has.
Action 4: RetrieveArticle[Leeann Hackworth].
Observation 4: # Leeann Hackworth ## Family The sister of Leeann Hackworth is Leisa Lutz.  The brother of Leeann Hackworth is Virgil Hackworth.  The mother of Leeann Hackworth is Vicki Hackworth.  The father of Leeann Hackworth is Ricardo Hackworth.  ## Friends The friends of Leeann Hackworth are Stacia Toombs, Brian Beltran, Gene Smock.  ## Attributes The date of birth of Leeann Hackworth is 1011-10-25.  The occupation of Leeann Hackworth is music tutor.  The hobby of Leeann Hackworth is research.  The gender of Leeann Hackworth is female.
Thought 5: The parents of Leeann Hackworth are Vicki Hackworth, Ricardo Hackworth. I need to find the brother of Ricardo Hackworth and the brother of Vicki Hackworth to find the uncles of Stacia Toombs through Leeann's side.
Action 5: RetrieveArticle[Vicki Hackworth].
Observation 5: # Vicki Hackworth ## Family The sisters of Vicki Hackworth are Aida Wang, Barabara Beltran.  The mother of Vicki Hackworth is Shelli Beltran.  The father of Vicki Hackworth is Dino Beltran.  The son of Vicki Hackworth is Virgil Hackworth.  The daughters of Vicki Hackworth are Leeann Hackworth, Leisa Lutz.  The husband of Vicki Hackworth is Ricardo Hackworth.  ## Friends The friends of Vicki Hackworth are Brian Beltran, Dominique Smock, Eli Smock.  ## Attributes The date of birth of Vicki Hackworth is 0985-05-30.  The occupation of Vicki Hackworth is police officer.  The hobby of Vicki Hackworth is meditation.  The gender of Vicki Hackworth is female.
Thought 5: Vicki Hackworth has no brother. Now I need to retrieve article about Ricardo Hackworth and find his brother.
Action 6: RetrieveArticle[Ricardo Hackworth].
Observation 6: # Ricardo Hackworth ## Family The son of Ricardo Hackworth is Virgil Hackworth.  The daughters of Ricardo Hackworth are Leeann Hackworth, Leisa Lutz.  The wife of Ricardo Hackworth is Vicki Hackworth.  ## Friends The friends of Ricardo Hackworth are Gene Smock, Isiah Lutz, Johnetta Wang.  ## Attributes The date of birth of Ricardo Hackworth is 0983-02-24.  The occupation of Ricardo Hackworth is clinical research associate.  The hobby of Ricardo Hackworth is dairy farming.  The gender of Ricardo Hackworth is male.
Thought 7: Ricardo Hackworth has no brother. So there are 0 uncles of Leeann Hackworth. I can move on the next friend. Now I need to retrieve article about Lesley Lutz and find how many uncles she has.
Action 7: RetrieveArticle[Lesley Lutz].
Observation 7: # Lesley Lutz ## Family The mother of Lesley Lutz is Leisa Lutz.  The father of Lesley Lutz is Isiah Lutz.  ## Friends The friends of Lesley Lutz are Shelli Beltran, Stacia Toombs.  ## Attributes The date of birth of Lesley Lutz is 1040-01-31.  The occupation of Lesley Lutz is barrister's clerk.  The hobby of Lesley Lutz is canoeing.  The gender of Lesley Lutz is male.
Thought 8: The parents of Lesley Lutz are Leisa Lutz, Isiah Lutz. I need to find the brother of Leisa Lutz and brother of Isiah Lutz to find the uncles of Lesley Lutz.
Action 8: RetrieveArticle[Leisa Lutz].
Observation 8: # Leisa Lutz ## Family The sister of Leisa Lutz is Leeann Hackworth.  The brother of Leisa Lutz is Virgil Hackworth.  The mother of Leisa Lutz is Vicki Hackworth.  The father of Leisa Lutz is Ricardo Hackworth.  The son of Leisa Lutz is Lesley Lutz.  The husband of Leisa Lutz is Isiah Lutz.  ## Friends The friends of Leisa Lutz are Leslee Toombs, Eli Smock, Gene Smock.  ## Attributes The date of birth of Leisa Lutz is 1015-11-21.  The occupation of Leisa Lutz is clinical cytogeneticist.  The hobby of Leisa Lutz is geography.  The gender of Leisa Lutz is female.
Thought 9: The brother of Leisa Lutz is Virgil Hackworth. So Virgil Hackward is an uncle of Lesley Lutz, who is a friend of Stacia Toombs. Now I need to find the brother of Isiah Lutz to find more uncles of Lesley Lutz.
Action 9: RetrieveArticle[Isiah Lutz].
Observation 9: # Isiah Lutz ## Family The son of Isiah Lutz is Lesley Lutz.  The wife of Isiah Lutz is Leisa Lutz.  ## Friends The friends of Isiah Lutz are Johnetta Wang, Ricardo Hackworth, Shelli Beltran, Stacia Toombs, Dominique Smock.  ## Attributes The date of birth of Isiah Lutz is 1014-10-18.  The occupation of Isiah Lutz is education administrator.  The hobby of Isiah Lutz is geocaching.  The gender of Isiah Lutz is male.
Thought 10: Isiah Lutz has no brother. So there is only 1 uncle of Lesley Lutz, who is a friend of Stacia Toombs. Now I move on to the next friend. Now I need to retrieve article about Ryan Wang and find how many uncles he has.
Action 10: RetrieveArticle[Ryan Wang].
Observation 10: # Ryan Wang ## Family The daughter of Ryan Wang is Johnetta Wang.  The wife of Ryan Wang is Aida Wang.  ## Friends The friends of Ryan Wang are Shelli Beltran, Stacia Toombs, Virgil Hackworth, Aida Wang.  ## Attributes The date of birth of Ryan Wang is 0982-03-17.  The occupation of Ryan Wang is chief of staff.  The hobby of Ryan Wang is fossil hunting.  The gender of Ryan Wang is male.
Thought 11: Ryan Wang has no parent, hence 0 uncles of Ryan Wang. I have finished searching for the uncles of the friends of Stacia Toombs. The answer is 0, 0, 0, 1, 0. Unique answers are 0, 1.
Action 11: Finish[0{constants.answer_sep}1].
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
    If the answer is a number, output the number like: Finish[5] or Finish[1{constants.answer_sep}2{constants.answer_sep}3].
    If you cannot find an answer to the numerical question, output the 0 answer like: Finish[0].

    You may take as many steps as necessary.
    Here are some examples:
    (START OF EXAMPLES)
    {{examples}}
    (END OF EXAMPLES)

    Now answer the following question:
    Question: {{question}}
    {{scratchpad}}
    """

    def get_prompt(self, prolog_query: bool = False) -> PromptTemplate:
        """Get the ReAct prompt template.

        Args:
            prolog_query: This parameter is not used for ReAct prompts, as they do not support Prolog query generation.

        Returns:
            A PromptTemplate object containing the ReAct prompt template.
        """
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
Question: Who is the sister of Aida Wang?
Action 1: RetrieveArticle[Aida Wang].
Observation 1: # Aida Wang ## Family The sisters of Aida Wang are Barabara Beltran, Vicki Hackworth.  The mother of Aida Wang is Shelli Beltran.  The father of Aida Wang is Dino Beltran.  The daughter of Aida Wang is Johnetta Wang.  The husband of Aida Wang is Ryan Wang.  ## Friends The friends of Aida Wang are Alvaro Smock, Lannie Smock, Leslee Toombs, Ryan Wang.  ## Attributes The date of birth of Aida Wang is 0985-05-30.  The occupation of Aida Wang is personal assistant.  The hobby of Aida Wang is meditation.  The gender of Aida Wang is female.
Action 2: Finish[Barabara Beltran{constants.answer_sep}Vicki Hackworth].

Example 2:
Question: Who is the mother of Ivana Smith?
Action 1: RetrieveArticle[Ivana Smith].
Observation 1: No article exists for the requested entity. Please try retrieving article for another entity.
Action 2: Finish[].

Example 3:
Question: Who is the child of Alvaro Smock?
Action 1: RetrieveArticle[Alvaro Smock].
Observation 1: # Alvaro Smock ## Family The sons of Alvaro Smock are Eli Smock, Gene Smock.  The wife of Alvaro Smock is Lannie Smock.  ## Friends The friends of Alvaro Smock are Dino Beltran, Gene Smock, Aida Wang.  ## Attributes The date of birth of Alvaro Smock is 0867-07-12.  The occupation of Alvaro Smock is osteopath.  The hobby of Alvaro Smock is biology
Action 2: Finish[Eli Smock{constants.answer_sep}Gene Smock].

Example 4:
Question: Who is the friend of the child of Alvaro Smock?
Action 1: RetrieveArticle[Alvaro Smock].
Observation 1: # Alvaro Smock ## Family The sons of Alvaro Smock are Eli Smock, Gene Smock.  The wife of Alvaro Smock is Lannie Smock.  ## Friends The friends of Alvaro Smock are Dino Beltran, Gene Smock, Aida Wang.  ## Attributes The date of birth of Alvaro Smock is 0867-07-12.  The occupation of Alvaro Smock is osteopath.  The hobby of Alvaro Smock is biology.  The gender of Alvaro Smock is male.
Action 2: RetrieveArticle[Eli Smock].
Observation 2: # Eli Smock ## Family The brother of Eli Smock is Gene Smock.  The mother of Eli Smock is Lannie Smock.  The father of Eli Smock is Alvaro Smock.  ## Friends The friends of Eli Smock are Leisa Lutz, Shelli Beltran, Vicki Hackworth, Virgil Hackworth, Alison Smock, Brian Beltran.  ## Attributes The date of birth of Eli Smock is 0901-01-18.  The occupation of Eli Smock is retail manager.  The hobby of Eli Smock is tether car.  The gender of Eli Smock is male.
Action 3: RetrieveArticle[Gene Smock].
Observation 3: # Gene Smock ## Family The brother of Gene Smock is Eli Smock.  The mother of Gene Smock is Lannie Smock.  The father of Gene Smock is Alvaro Smock.  The son of Gene Smock is Williams Smock.  The wife of Gene Smock is Dominique Smock.  ## Friends The friends of Gene Smock are Leeann Hackworth, Leisa Lutz, Ricardo Hackworth, Alvaro Smock, Dominique Smock.  ## Attributes The date of birth of Gene Smock is 0898-08-16.  The occupation of Gene Smock is immunologist.  The hobby of Gene Smock is architecture.  The gender of Gene Smock is male.
Action 4: Finish[Leisa Lutz{constants.answer_sep}Shelli Beltran{constants.answer_sep}Vicki Hackworth{constants.answer_sep}Virgil Hackworth{constants.answer_sep}Alison Smock{constants.answer_sep}Brian Beltran{constants.answer_sep}Leeann Hackworth{constants.answer_sep}Ricardo Hackworth{constants.answer_sep}Dominique Smock].

Example 5:
Question: Who is the aunt of Vicki Hackworth?
Action 1: RetrieveArticle[Vicki Hackworth].
Observation 1: # Vicki Hackworth ## Family The sisters of Vicki Hackworth are Aida Wang, Barabara Beltran.  The mother of Vicki Hackworth is Shelli Beltran.  The father of Vicki Hackworth is Dino Beltran.  The son of Vicki Hackworth is Virgil Hackworth.  The daughters of Vicki Hackworth are Leeann Hackworth, Leisa Lutz.  The husband of Vicki Hackworth is Ricardo Hackworth.  ## Friends The friends of Vicki Hackworth are Brian Beltran, Dominique Smock, Eli Smock.  ## Attributes The date of birth of Vicki Hackworth is 0985-05-30.  The occupation of Vicki Hackworth is police officer.  The hobby of Vicki Hackworth is meditation.  The gender of Vicki Hackworth is female.
Action 2: RetrieveArticle[Shelli Beltran].
Observation 2: # Shelli Beltran ## Family The sister of Shelli Beltran is Stacia Toombs.  The mother of Shelli Beltran is Alison Smock.  The father of Shelli Beltran is Williams Smock.  The daughters of Shelli Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth.  The husband of Shelli Beltran is Dino Beltran.  ## Friends The friends of Shelli Beltran are Brian Beltran, Eli Smock, Isiah Lutz, Leslee Toombs, Lesley Lutz, Ryan Wang.  ## Attributes The date of birth of Shelli Beltran is 0958-03-08.  The occupation of Shelli Beltran is occupational therapist.  The hobby of Shelli Beltran is sociology.  The gender of Shelli Beltran is female.
Action 3: RetrieveArticle[Dino Beltran].
Observation 3: # Dino Beltran ## Family The brother of Dino Beltran is Orlando Beltran.  The mother of Dino Beltran is Daisy Beltran.  The father of Dino Beltran is Brian Beltran.  The daughters of Dino Beltran are Aida Wang, Barabara Beltran, Vicki Hackworth.  The wife of Dino Beltran is Shelli Beltran.  ## Friends The friend of Dino Beltran is Alvaro Smock.  ## Attributes The date of birth of Dino Beltran is 0958-08-09.  The occupation of Dino Beltran is associate professor.  The hobby of Dino Beltran is shogi.  The gender of Dino Beltran is male.
Action 4: Finish[Stacia Toombs].

Example 6:
Question: What is the occupation of the husband of Stacia Toombs?
Action 1: RetrieveArticle[Stacia Toombs].
Observation 1: # Stacia Toombs ## Family The sister of Stacia Toombs is Shelli Beltran.  The mother of Stacia Toombs is Alison Smock.  The father of Stacia Toombs is Williams Smock.  The daughter of Stacia Toombs is Leslee Toombs.  The husband of Stacia Toombs is Wilbert Toombs.  ## Friends The friends of Stacia Toombs are Brian Beltran, Isiah Lutz, Leeann Hackworth, Lesley Lutz, Ryan Wang.  ## Attributes The date of birth of Stacia Toombs is 0959-03-22.  The occupation of Stacia Toombs is actuary.  The hobby of Stacia Toombs is finance.  The gender of Stacia Toombs is female.
Action 2: RetrieveArticle[Wilbert Toombs].
Observation 2: # Wilbert Toombs ## Family The daughter of Wilbert Toombs is Leslee Toombs.  The wife of Wilbert Toombs is Stacia Toombs.  ## Friends ## Attributes The date of birth of Wilbert Toombs is 0956-07-26.  The occupation of Wilbert Toombs is theatre manager.  The hobby of Wilbert Toombs is radio-controlled car racing.  The gender of Wilbert Toombs is male.
Action 3: Finish[theatre manager].

Example 7:
Question: What is the hobby of the daughter-in-law of Lannie Smock?
Action 1: RetrieveArticle[Lannie Smock].
Observation 1: # Lannie Smock ## Family The sons of Lannie Smock are Eli Smock, Gene Smock.  The husband of Lannie Smock is Alvaro Smock.  ## Friends The friends of Lannie Smock are Williams Smock, Aida Wang, Alison Smock.  ## Attributes The date of birth of Lannie Smock is 0867-08-24.  The occupation of Lannie Smock is biomedical scientist.  The hobby of Lannie Smock is bus spotting.  The gender of Lannie Smock is female.
Action 2: RetrieveArticle[Eli Smock].
Observation 2: # Eli Smock ## Family The brother of Eli Smock is Gene Smock.  The mother of Eli Smock is Lannie Smock.  The father of Eli Smock is Alvaro Smock.  ## Friends The friends of Eli Smock are Leisa Lutz, Shelli Beltran, Vicki Hackworth, Virgil Hackworth, Alison Smock, Brian Beltran.  ## Attributes The date of birth of Eli Smock is 0901-01-18.  The occupation of Eli Smock is retail manager.  The hobby of Eli Smock is tether car.  The gender of Eli Smock is male.
Action 3: RetrieveArticle[Gene Smock].
Observation 3: # Gene Smock ## Family The brother of Gene Smock is Eli Smock.  The mother of Gene Smock is Lannie Smock.  The father of Gene Smock is Alvaro Smock.  The son of Gene Smock is Williams Smock.  The wife of Gene Smock is Dominique Smock.  ## Friends The friends of Gene Smock are Leeann Hackworth, Leisa Lutz, Ricardo Hackworth, Alvaro Smock, Dominique Smock.  ## Attributes The date of birth of Gene Smock is 0898-08-16.  The occupation of Gene Smock is immunologist.  The hobby of Gene Smock is architecture.  The gender of Gene Smock is male.
Action 4: RetrieveArticle[Dominique Smock].
Observation 4: # Dominique Smock ## Family The son of Dominique Smock is Williams Smock.  The husband of Dominique Smock is Gene Smock.  ## Friends The friends of Dominique Smock are Gene Smock, Isiah Lutz, Orlando Beltran, Vicki Hackworth.  ## Attributes The date of birth of Dominique Smock is 0897-09-08.  The occupation of Dominique Smock is sports therapist.  The hobby of Dominique Smock is dominoes.  The gender of Dominique Smock is female.
Action 4: Finish[dominoes].

Example 8:
Question: What is the date of birth of the person whose hobby is finance?
Action 1: Search[finance].
Observation 1: (1) Stacia Toombs
Action 2: RetrieveArticle[Stacia Toombs].
Observation 2: # Stacia Toombs ## Family The sister of Stacia Toombs is Shelli Beltran.  The mother of Stacia Toombs is Alison Smock.  The father of Stacia Toombs is Williams Smock.  The daughter of Stacia Toombs is Leslee Toombs.  The husband of Stacia Toombs is Wilbert Toombs.  ## Friends The friends of Stacia Toombs are Brian Beltran, Isiah Lutz, Leeann Hackworth, Lesley Lutz, Ryan Wang.  ## Attributes The date of birth of Stacia Toombs is 0959-03-22.  The occupation of Stacia Toombs is actuary.  The hobby of Stacia Toombs is finance.  The gender of Stacia Toombs is female.
Action 3: Finish[0959-03-22].

Example 9:
Question: Who is the great-granddaughter of the person whose occupation is biomedical scientist?
Action 1: Search[biomedical scientist].
Observation 1: (1) Lannie Smock
Action 2: RetrieveArticle[Lannie Smock].
Observation 2: # Lannie Smock ## Family The sons of Lannie Smock are Eli Smock, Gene Smock.  The husband of Lannie Smock is Alvaro Smock.  ## Friends The friends of Lannie Smock are Williams Smock, Aida Wang, Alison Smock.  ## Attributes The date of birth of Lannie Smock is 0867-08-24.  The occupation of Lannie Smock is biomedical scientist.  The hobby of Lannie Smock is bus spotting.  The gender of Lannie Smock is female.
Action 3: RetrieveArticle[Eli Smock].
Observation 3: # Eli Smock ## Family The brother of Eli Smock is Gene Smock.  The mother of Eli Smock is Lannie Smock.  The father of Eli Smock is Alvaro Smock.  ## Friends The friends of Eli Smock are Leisa Lutz, Shelli Beltran, Vicki Hackworth, Virgil Hackworth, Alison Smock, Brian Beltran.  ## Attributes The date of birth of Eli Smock is 0901-01-18.  The occupation of Eli Smock is retail manager.  The hobby of Eli Smock is tether car.  The gender of Eli Smock is male.
Action 4: RetrieveArticle[Gene Smock].
Observation 4: # Gene Smock ## Family The brother of Gene Smock is Eli Smock.  The mother of Gene Smock is Lannie Smock.  The father of Gene Smock is Alvaro Smock.  The son of Gene Smock is Williams Smock.  The wife of Gene Smock is Dominique Smock.  ## Friends The friends of Gene Smock are Leeann Hackworth, Leisa Lutz, Ricardo Hackworth, Alvaro Smock, Dominique Smock.  ## Attributes The date of birth of Gene Smock is 0898-08-16.  The occupation of Gene Smock is immunologist.  The hobby of Gene Smock is architecture.  The gender of Gene Smock is male.
Action 5: RetrieveArticle[Williams Smock].
Observation 5: # Williams Smock ## Family The mother of Williams Smock is Dominique Smock.  The father of Williams Smock is Gene Smock.  The daughters of Williams Smock are Shelli Beltran, Stacia Toombs.  The wife of Williams Smock is Alison Smock.  ## Friends The friend of Williams Smock is Lannie Smock.  ## Attributes The date of birth of Williams Smock is 0926-04-04.  The occupation of Williams Smock is clinical biochemist.  The hobby of Williams Smock is social studies.  The gender of Williams Smock is male.
Action 5: Finish[Shelli Beltran{constants.answer_sep}Stacia Toombs].

Example 10:
Question: How many friends does Ryan Wang have?
Action 1: RetrieveArticle[Ryan Wang].
Observation 1: # Ryan Wang ## Family The daughter of Ryan Wang is Johnetta Wang.  The wife of Ryan Wang is Aida Wang.  ## Friends The friends of Ryan Wang are Shelli Beltran, Stacia Toombs, Virgil Hackworth, Aida Wang.  ## Attributes The date of birth of Ryan Wang is 0982-03-17.  The occupation of Ryan Wang is chief of staff.  The hobby of Ryan Wang is fossil hunting.  The gender of Ryan Wang is male.
Action 2: Finish[4].

Example 11:
Question: How many friends does the child of Alvaro Smock have?
Action 1: RetrieveArticle[Alvaro Smock].
Observation 1: # Alvaro Smock ## Family The sons of Alvaro Smock are Eli Smock, Gene Smock.  The wife of Alvaro Smock is Lannie Smock.  ## Friends The friends of Alvaro Smock are Dino Beltran, Gene Smock, Aida Wang.  ## Attributes The date of birth of Alvaro Smock is 0867-07-12.  The occupation of Alvaro Smock is osteopath.  The hobby of Alvaro Smock is biology.  The gender of Alvaro Smock is male.
Action 2: RetrieveArticle[Eli Smock].
Observation 2: # Eli Smock ## Family The brother of Eli Smock is Gene Smock.  The mother of Eli Smock is Lannie Smock.  The father of Eli Smock is Alvaro Smock.  ## Friends The friends of Eli Smock are Leisa Lutz, Shelli Beltran, Vicki Hackworth, Virgil Hackworth, Alison Smock, Brian Beltran.  ## Attributes The date of birth of Eli Smock is 0901-01-18.  The occupation of Eli Smock is retail manager.  The hobby of Eli Smock is tether car.  The gender of Eli Smock is male.
Action 3: RetrieveArticle[Gene Smock].
Observation 3: # Gene Smock ## Family The brother of Gene Smock is Eli Smock.  The mother of Gene Smock is Lannie Smock.  The father of Gene Smock is Alvaro Smock.  The son of Gene Smock is Williams Smock.  The wife of Gene Smock is Dominique Smock.  ## Friends The friends of Gene Smock are Leeann Hackworth, Leisa Lutz, Ricardo Hackworth, Alvaro Smock, Dominique Smock.  ## Attributes The date of birth of Gene Smock is 0898-08-16.  The occupation of Gene Smock is immunologist.  The hobby of Gene Smock is architecture.  The gender of Gene Smock is male.
Action 4: Finish[6{constants.answer_sep}5].

Example 12:
Question: How many uncles does the friend of Stacia Toombs have?
Action 1: RetrieveArticle[Stacia Toombs].
Observation 1: # Stacia Toombs ## Family The sister of Stacia Toombs is Shelli Beltran.  The mother of Stacia Toombs is Alison Smock.  The father of Stacia Toombs is Williams Smock.  The daughter of Stacia Toombs is Leslee Toombs.  The husband of Stacia Toombs is Wilbert Toombs.  ## Friends The friends of Stacia Toombs are Brian Beltran, Isiah Lutz, Leeann Hackworth, Lesley Lutz, Ryan Wang.  ## Attributes The date of birth of Stacia Toombs is 0959-03-22.  The occupation of Stacia Toombs is actuary.  The hobby of Stacia Toombs is finance.  The gender of Stacia Toombs is female.
Action 2: RetrieveArticle[Brian Beltran].
Observation 2: # Brian Beltran ## Family The sons of Brian Beltran are Dino Beltran, Orlando Beltran.  The wife of Brian Beltran is Daisy Beltran.  ## Friends The friends of Brian Beltran are Eli Smock, Leeann Hackworth, Shelli Beltran, Stacia Toombs, Vicki Hackworth.  ## Attributes The date of birth of Brian Beltran is 0927-07-27.  The occupation of Brian Beltran is oncologist.  The hobby of Brian Beltran is dolls.  The gender of Brian Beltran is male.
Action 3: RetrieveArticle[Isiah Lutz].
Observation 3: # Isiah Lutz ## Family The son of Isiah Lutz is Lesley Lutz.  The wife of Isiah Lutz is Leisa Lutz.  ## Friends The friends of Isiah Lutz are Johnetta Wang, Ricardo Hackworth, Shelli Beltran, Stacia Toombs, Dominique Smock.  ## Attributes The date of birth of Isiah Lutz is 1014-10-18.  The occupation of Isiah Lutz is education administrator.  The hobby of Isiah Lutz is geocaching.  The gender of Isiah Lutz is male.
Action 4: RetrieveArticle[Leeann Hackworth].
Observation 4: # Leeann Hackworth ## Family The sister of Leeann Hackworth is Leisa Lutz.  The brother of Leeann Hackworth is Virgil Hackworth.  The mother of Leeann Hackworth is Vicki Hackworth.  The father of Leeann Hackworth is Ricardo Hackworth.  ## Friends The friends of Leeann Hackworth are Stacia Toombs, Brian Beltran, Gene Smock.  ## Attributes The date of birth of Leeann Hackworth is 1011-10-25.  The occupation of Leeann Hackworth is music tutor.  The hobby of Leeann Hackworth is research.  The gender of Leeann Hackworth is female.
Action 5: RetrieveArticle[Vicki Hackworth].
Observation 5: # Vicki Hackworth ## Family The sisters of Vicki Hackworth are Aida Wang, Barabara Beltran.  The mother of Vicki Hackworth is Shelli Beltran.  The father of Vicki Hackworth is Dino Beltran.  The son of Vicki Hackworth is Virgil Hackworth.  The daughters of Vicki Hackworth are Leeann Hackworth, Leisa Lutz.  The husband of Vicki Hackworth is Ricardo Hackworth.  ## Friends The friends of Vicki Hackworth are Brian Beltran, Dominique Smock, Eli Smock.  ## Attributes The date of birth of Vicki Hackworth is 0985-05-30.  The occupation of Vicki Hackworth is police officer.  The hobby of Vicki Hackworth is meditation.  The gender of Vicki Hackworth is female.
Action 6: RetrieveArticle[Ricardo Hackworth].
Observation 6: # Ricardo Hackworth ## Family The son of Ricardo Hackworth is Virgil Hackworth.  The daughters of Ricardo Hackworth are Leeann Hackworth, Leisa Lutz.  The wife of Ricardo Hackworth is Vicki Hackworth.  ## Friends The friends of Ricardo Hackworth are Gene Smock, Isiah Lutz, Johnetta Wang.  ## Attributes The date of birth of Ricardo Hackworth is 0983-02-24.  The occupation of Ricardo Hackworth is clinical research associate.  The hobby of Ricardo Hackworth is dairy farming.  The gender of Ricardo Hackworth is male.
Action 7: RetrieveArticle[Lesley Lutz].
Observation 7: # Lesley Lutz ## Family The mother of Lesley Lutz is Leisa Lutz.  The father of Lesley Lutz is Isiah Lutz.  ## Friends The friends of Lesley Lutz are Shelli Beltran, Stacia Toombs.  ## Attributes The date of birth of Lesley Lutz is 1040-01-31.  The occupation of Lesley Lutz is barrister's clerk.  The hobby of Lesley Lutz is canoeing.  The gender of Lesley Lutz is male.
Action 8: RetrieveArticle[Leisa Lutz].
Observation 8: # Leisa Lutz ## Family The sister of Leisa Lutz is Leeann Hackworth.  The brother of Leisa Lutz is Virgil Hackworth.  The mother of Leisa Lutz is Vicki Hackworth.  The father of Leisa Lutz is Ricardo Hackworth.  The son of Leisa Lutz is Lesley Lutz.  The husband of Leisa Lutz is Isiah Lutz.  ## Friends The friends of Leisa Lutz are Leslee Toombs, Eli Smock, Gene Smock.  ## Attributes The date of birth of Leisa Lutz is 1015-11-21.  The occupation of Leisa Lutz is clinical cytogeneticist.  The hobby of Leisa Lutz is geography.  The gender of Leisa Lutz is female.
Action 9: RetrieveArticle[Isiah Lutz].
Observation 9: # Isiah Lutz ## Family The son of Isiah Lutz is Lesley Lutz.  The wife of Isiah Lutz is Leisa Lutz.  ## Friends The friends of Isiah Lutz are Johnetta Wang, Ricardo Hackworth, Shelli Beltran, Stacia Toombs, Dominique Smock.  ## Attributes The date of birth of Isiah Lutz is 1014-10-18.  The occupation of Isiah Lutz is education administrator.  The hobby of Isiah Lutz is geocaching.  The gender of Isiah Lutz is male.
Action 10: RetrieveArticle[Ryan Wang].
Observation 10: # Ryan Wang ## Family The daughter of Ryan Wang is Johnetta Wang.  The wife of Ryan Wang is Aida Wang.  ## Friends The friends of Ryan Wang are Shelli Beltran, Stacia Toombs, Virgil Hackworth, Aida Wang.  ## Attributes The date of birth of Ryan Wang is 0982-03-17.  The occupation of Ryan Wang is chief of staff.  The hobby of Ryan Wang is fossil hunting.  The gender of Ryan Wang is male.
Action 11: Finish[0{constants.answer_sep}1].
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
    If the answer is a number, output the number like: Finish[5] or Finish[1{constants.answer_sep}2{constants.answer_sep}3].
    If you cannot find an answer to the numerical question, output the 0 answer like: Finish[0].

    You may take as many steps as necessary.
    Here are some examples:
    (START OF EXAMPLES)
    {{examples}}
    (END OF EXAMPLES)

    Now answer the following question:
    Question: {{question}}
    {{scratchpad}}
    """

    def get_prompt(self, prolog_query: bool = False) -> PromptTemplate:
        """Get the Act prompt template.

        Args:
            prolog_query: This parameter is not used for Act prompts, as they do not support Prolog query generation.

        Returns:
            A PromptTemplate object containing the Act prompt template.
        """
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
        case "zeroshot-rag":
            return ZeroshotLLMPrompt()
            # return RAGLLMPrompt()
        case "react" | "react->cot-sc":
            match model_name:
                case model_name if model_name in OpenAIChat.SUPPORTED_LLM_NAMES:
                    return ReactLLMPrompt()
                case model_name if model_name in TogetherChat.SUPPORTED_LLM_NAMES:
                    return ReactTogetherPrompt()
                case model_name if model_name in GeminiChat.SUPPORTED_LLM_NAMES:
                    return ReactGeminiPrompt()
                case model_name if model_name in AnthropicChat.SUPPORTED_LLM_NAMES:
                    return ReactLLMPrompt()
                case model_name if is_huggingface_model(model_name):
                    return ReactLLMPrompt()
                case _:
                    raise ValueError(f"Model name {model_name} must be one of {llm.SUPPORTED_LLM_NAMES}.")
        case "act":
            return ActLLMPrompt()
        case _:
            raise ValueError(f"Method {method} not supported.")
