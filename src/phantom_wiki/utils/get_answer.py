import logging

from pyswip import Variable
import re

from ..facts.database import Database
from . import decode


def get_answer(
    all_queries: list[list[list[str]]],
    db: Database,
    answers: str,
    return_solution_traces: bool = False,
    multi_threading: bool = False,
) -> tuple[list[dict[str, str]], list[str]]:
    """Retrieves answers for a given set of logical queries from the database.

    Args:
        all_queries (list[list[list[str]]]): A list of list of list of queries to be evaluated against the database.
            Each query is a list of logical predicates. Each list of list of queries follows a single template.
            Example: [["child(Y_2, Y_3)", "sister(Elisa, Y_2)"]]
        db (Database): The database instance used to resolve the queries.
        answers (str): A placeholder variable representing the expected answer.
            Example: "Y_3"
        return_solution_traces (bool, optional): Whether to return intermediate solution traces 
            (i.e., step-by-step mappings of placeholders to values). Defaults to False.
        multi_threading (bool, optional): Whether to enable concurrent query execution. Defaults to False.


    Returns:
            - `final_results`: A list of strings representing the final answer(s) derived from the query.

        `solution_traces`: list(list(list[dict[str, str]]))
            A list of list of list dictionaries with the results along the "path trace" to the final answer
        `final_results`: list(list(list[str]))
            The final results of the list of list of queries

    Example:
    ```python
    queries = [
        [
            ["child(Y_2, Y_3)", "sister(Elisa, Y_2)"],
            ["parent(Y_4, Y_5)", "brother(John, Y_4)"]
        ],
        [
            ["ancestor(Y_6, Y_7)", "cousin(Mike, Y_6)"]
        ]
    ]

    solution_traces, final_results = get_answer(queries, db, "Y_3", return_solution_traces=True)
    ```

    **Expected Output:**
    ```
    solution_traces = [
        [
            [
                {"Y_2": "Alice", "Y_3": "Bob"},
                {"Y_4": "David", "Y_5": "Eve"}
            ]
        ],
        [
            [
                {"Y_6": "Sarah", "Y_7": "Tom"}
            ]
        ]
    ]

    final_results = [
        [
            ["Bob", "Eve"]
        ],
        [
            ["Tom"]
        ]
    ]
    ```
    """
    # All the solution traces
    all_solution_traces, all_final_results = [], []

    # Preprocessing of all the queries, ie. reversing and joining
    for i in range(len(all_queries)):
        for j in range(len(all_queries[i])):
            reversed_query = all_queries[i][j][::-1]
            all_queries[i][j] = ", ".join(reversed_query)

    # We flatten the list of queries to be able to batch query them
    flattened_all_queries = [item for sublist in all_queries for item in sublist]
    temp_query_results = db.batch_query(flattened_all_queries, multi_threading)

    # We then restructure the query results to match the original structure
    all_query_results = []
    c = 0
    for i in range(len(all_queries)):
        all_query_results.append([])
        for j in range(len(all_queries[i])):
            all_query_results[i].append(temp_query_results[c])
            c+=1

    for j in range(len(all_queries)):
        # This iterates through the templates queries
        query_results = all_query_results[j] # These are thus the query results for one template
        answer = answers[j] # This is the answer for one template

        solution_traces = []
        final_results = []
        
        for query_result in query_results:
            # Here, we iterate through query results of one single template

            if return_solution_traces:
                solution_trace: list[dict[str, str]] = [
                    {k: decode(v) for k, v in x.items()} for x in query_result
                ]
                # solution_trace can contain duplicate dictionaries, keep only unique ones
                # frozenset is used to make the dictionaries hashable, and set to remove duplicates
                unique_solution_trace = set(frozenset(d.items()) for d in solution_trace)
                solution_trace = [dict(s) for s in unique_solution_trace]

                # For aggregation questions, prolog will create a Variable type for the final placeholder of the query
                # We remove this from the solution traces because
                # - it is not useful for solution traces column in the dataset
                # - the Variable object is not JSON serializable and cannot be dumped into a file
                # TODO Anmol: implement this. I'm getting segfault whatever I do.
                # for trace in solution_trace:
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
                solution_trace = []

            final_result = [str(decode(x[answer])) for x in query_result]
            final_result = sorted(set(final_result))

            solution_traces.append(solution_trace)
            final_results.append(final_result)

        all_solution_traces.append(solution_traces)
        all_final_results.append(final_results)

    return all_solution_traces, all_final_results