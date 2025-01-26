import logging

from pyswip import Variable

from ..facts.database import Database
from . import decode


def get_answer(
    query: list[str],
    db: Database,
    answer: str,
    return_solution_traces: bool = False
) -> tuple[list[dict[str, str]], list[str]]:
    """Get the answer to a query from the database

    Args:
        query (list[str]): The query to be answered
            Example: [child(Y_2, Y_3), sister(Elisa, Y_2)]
        db (Database): The database to query
        answer (str): The answer to the query as a placeholder
            Example: "Y_3"
        return_solution_traces (bool, optional): Flag to return solution traces (intermediate results).
            Defaults to False, in which case the returned list is empty.

    Returns:
        solution_traces: list[dict[str, str]]
            A list of dictionaries with the results along the "path trace" to the final answer
        final_results: list[str] 
            The final results of the entire query

    Example:
    ```python
    query = [child(Y_2, Y_3), sister(Elisa, Y_2)]
    solution_traces, final_results = get_answer(query, db, "Y_3", return_solution_traces=True)
    ```
    outputs `[{"Y_2": "Alice", "Y_3": "Bob"}], ["Bob"]`.
    Each dictionary in the solution_traces list is a sequence of placeholders and values towards a final answer.
    There can be multiple final answers, and so multiple dictionaries in solution_traces.
    """
    # Evaluate the reversed query
    reversed_query = query[::-1]
    query_result: list[dict] = db.query(", ".join(reversed_query))

    if return_solution_traces:
        solution_traces: list[dict[str, str]] = [
            {k: decode(v) for k, v in x.items()} for x in query_result
        ]
        # solution_traces can contain duplicate dictionaries, keep only unique ones
        # frozenset is used to make the dictionaries hashable, and set to remove duplicates
        unique_solution_traces = set(frozenset(d.items()) for d in solution_traces)
        solution_traces = [dict(s) for s in unique_solution_traces]

        # For aggregation questions, prolog will create a Variable type for the final placeholder of the query
        # We remove this from the solution traces because
        # - it is not useful for solution traces column in the dataset
        # - the Variable object is not JSON serializable and cannot be dumped into a file
        # TODO Anmol: implement this. I'm getting segfault whatever I do.
        # for trace in solution_traces:
        #     for k, v in trace.items():
        #         if isinstance(v, Variable):
        #             print(k, v)
        #             trace[k] = ""
            # # Find keys to delete and only iterate through them, to avoid modifying the dictionary while iterating
            # # or causing a segfault (there are lots of keys in trace, so we only want to use a generator)
            # keys_to_delete = [k for k, v in trace.items() if isinstance(v, Variable)]
            # for k in keys_to_delete:
            #     del trace[k]

    else:
        logging.warning("Skipping solution traces")
        solution_traces = []

    final_results = [str(decode(x[answer])) for x in query_result]
    final_results = sorted(set(final_results))

    return solution_traces, final_results