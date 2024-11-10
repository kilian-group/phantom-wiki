# To generate questions from the command line, run the following command:
# python -m phantom_wiki -op <output path>
# For example:
#   python -m phantom_wiki -op out

import janus_swi as janus

from ..utils import generate_unique_id

# %%
def get_question_answers(atom_val, atom_name, rules):
    question_answers = []
    for predicate, args in rules:
        if atom_name in args:
            # print(predicate, args)
            query = f"{predicate}({','.join(args)})"
            # print(query)
            result = janus.query_once(query, {atom_name: atom_val})
            # print(result)

            question = "{atom} is the {predicate} of who?".format(predicate=predicate, atom=atom_val)
            # print("Question: ", question)
            answer = result['Y']
            # print("Answer: ", answer)
            unique_id = generate_unique_id()
            question_answers.append({'id':unique_id, 'question':question, 'answer': answer})
    return question_answers
