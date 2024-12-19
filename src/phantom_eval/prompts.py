prompt = "Given following table of data about an individual, {} {}"  # question, data

extra = {
    "stepbystep": "Think carefully step by step.",
    "verify": "Verify that your answer aligns with the given data.",
    "instruction": "Please carefully follow the instructions to provide an accurate answer.",
}

format = {
    "plain": "Please respond with only your answer and no other text.",
    "answer: with ex": "Please finish your response with Answer: <your answer>, for example, if the answer was yes, you should finish your response with Answer: yes",
    "answer:": "Please finish your answer with Answer: <your answer>",
}


from .score import match

def score_answer(response, true, scoring=match, key_text="answer: "):
    response = response.lower()
    if key_text is None:
        return response == true
    answer_index = response.rfind(key_text)
    if answer_index == -1:
        return False
    return scoring(response[answer_index + len(key_text) :], true)


def evaluate(data, model, prompt, score):
    correct = 0
    for input, true in data:
        input_prompt = prompt.format(*input)
        pred = model(input_prompt)
        correct += score(pred, true)

    return correct


data = [
    (
        (
            "He was born in 1987 in the state of asw234782. He married his childhood sweetheart kdjhf948 in 2004 and had two beautiful children tuty33545 and 2534bdjd.",
            "What is the name of the spouse of asw234782?",
        ),
        "kdjhf948",
    ),
    (
        (
            "He was born in 1987 in the state of asw234782. He married his childhood sweetheart kdjhf948 in 2004 and had two beautiful children tuty33545 and 2534bdjd.",
            "Where was he born?",
        ),
        "asw234782",
    ),
    (
        (
            "He was born in 1987 in the state of asw234782. He married his childhood sweetheart kdjhf948 in 2004 and had two beautiful children tuty33545 and 2534bdjd.",
            "When was he born?",
        ),
        "1987",
    ),
]


# evaluate(
#     data,
#     print,
#     " ".join([prompt, extra["stepbystep"], format["plain"]]),
#     lambda x, y: True,
# )

# prompt, extra["stepbystep"], format["answer:"]
answers = [
    """Sure! Let's work through this step-by-step to determine the name of the spouse of "asw234782":

The person being described was born in 1987 in a state called "asw234782".
This person got married to someone named "kdjhf948" in 2004.
As a result of their marriage, they had two children together: "tuty33545" and "2534bdjd".
So, based on the information provided, the name of the spouse of "asw234782" is "kdjhf948".

Answer: kdjhf948""",
    """Thank you for providing me with this information! Based on the given data, I can determine where he was born as follows:

The first letter of the state name is "A".
The second letter of the state name is "S".
The third letter of the state name is "W".
Therefore, the person was born in the state of ASW234782.

Answer: ASW234782""",
    """To determine when the person was born, we need to follow these steps based on the given information:

Step 1: Find the year of marriage from the information provided.
The person got married in 2004.

Step 2: Calculate the age difference between the date of birth and the year of marriage.
Year of marriage - Date of birth = X (where X is the number of years)
X = 2004 - 1987 = 17 years

Step 3: Determine the exact date of birth using the age at the time of marriage.
Since the person was born 17 years before their marriage, they were born in:
Date of birth = Year of marriage + Age at marriage - 17
Date of birth = 2004 + 17 - 17 = 2004

Answer: The person was born in 2004.""",
]


# for answer, (_, true) in zip(answers, data):
#     print(score_answer(answer, true))


"""
Zero-shot prompts
"""
ZEROSHOT_PROMPT = """{evidence}
Answer the following question:
{question}

The output should be one of the following:
- A name (if there is only one correct answer)
- A list of names separated by commas (if there are multiple correct answers)
- A number (if the answer is a number)
DO NOT include any additional information in the output.
"""