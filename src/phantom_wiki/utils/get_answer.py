import json
import logging

from ..facts.database import Database
from . import decode


def get_answer(
    query: list[str],
    db: Database,
    answer: str,
    add_intermediate_answers: bool = False
) -> tuple[list[str], list[str]]:
    """Get the answer to a query from the database

    Args:
        query (list[str]): The query to be answered
            Example: [child(Y_2, Y_3), sister(Elisa, Y_2)]
        db (Database): The database to query
        answer (str): The answer to the query as a placeholder
            Example: "Y_3"
        add_intermediate_answers (bool, optional): Whether to add intermediate answers to the results.
            Defaults to False.

    Returns:
        intermediate_answers: list[dict[str, str]]
            A list of dictionaries with the results along the "path" to the final answer
        final_results: list[str] 
            The final results of the entire query

    Example:
    ```python
    query = [child(Y_2, Y_3), sister(Elisa, Y_2)]
    intermediate_answers, final_results = get_answer(query, db, "Y_3", add_intermediate_answers=True)
    ```
    outputs `[{"Y_2": "Alice", "Y_3": "Bob"}], ["Bob"]`.
    Each dictionary in the intermediate_answers list is a sequence of placeholders and values towards a final answer.
    There can be multiple final answers, and so multiple dictionaries in intermediate_answers.
    """
    reversed_query = query[::-1]
    if add_intermediate_answers:
        intermediate_answers: list[dict[str, str]] = [
            {k: decode(v) for k, v in x.items()}
            for x in db.query(", ".join(reversed_query))
        ]
        # intermediate_answers can contain duplicate dictionaries, keep only unique ones
        # frozenset is used to make the dictionaries hashable, and set to remove duplicates
        unique_intermediate_answers = set(frozenset(d.items()) for d in intermediate_answers)
        intermediate_answers = [dict(s) for s in unique_intermediate_answers]
    else:
        logging.warning("Skipping intermediate answers")
        intermediate_answers = []

    final_results = [decode(x[answer]) for x in db.query(", ".join(reversed_query))]
    final_results = sorted(set(final_results))

    return intermediate_answers, final_results