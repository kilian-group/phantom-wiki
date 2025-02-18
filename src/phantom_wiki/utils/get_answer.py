import logging

from pyswip import Variable

from ..facts.database import Database
from . import decode


def get_answer(
    all_queries: list[list[list[str]]],
    db: Database,
    answers: list[str],
    skip_solution_traces: bool = False,
    multi_threading: bool = False,
) -> tuple[list[list[list[dict[str, str]]]], list[list[list[str]]]]:
    """Retrieves answers for a given set of logical queries from the database.

    Args:
        all_queries (list[list[list[str]]]): A structured collection of logical
            queries to be evaluated against the database.
            - Organized as [# of template types] x [# of questions per template] x [subqueries per query].
            - Each query consists of a list of logical predicates expressed as strings.
            - Example:
                ```
                [
                    ["child(Y_2, Y_3)", "sister(Elisa, Y_2)"],
                    ["parent(Y_2, Y_3)", "brother(John, Y_2)"]
                ],
                [
                    ["ancestor(Y_6, Y_7)", "cousin(Mike, Y_6)"]
                    ["ancestor(Y_6, Y_7)", "nephew(Mike, Y_6)"]
                ]
                ```
        db (Database): The database instance used to resolve the queries.
        answers (list[str]): A list of placeholder variables for the expected answers
            for each template type.
            - The length of `answers` must match the number of template types
            (1st dimension of `all_queries`).
            - Example: `["Y_3", "Y_5"]` means extracting `Y_3` for the first template
            type and `Y_5` for the second.
        skip_solution_traces (bool, optional): Flag to skip solution traces, which describe the
            intermediate steps towards final answer. Defaults to False, in which case the
            returned list is non-empty.
        multi_threading (bool, optional): If `True`, enables parallel query execution for
            performance improvements. Defaults to `False`.


    Returns: (tuple)

        `all_solution_traces` (list[list[list[dict[str, str]]]]):
            - A structured list containing intermediate solution traces for each query.
            - Set up as [# of template types] x [# of questions per template] x [solution traces per query].
            - Matches the structure of `all_queries`.
            - Each trace contains a list of dictionaries mapping query variables to their resolved values.

        `all_final_results` (list[list[list[str]]]):
            - The final resolved answers extracted for each query.
            - Organized as [# of template types] x [# of questions per template] x [results per query].
            - Matches the structure of `all_queries`.
            - Each sublist contains a list of string results.

    Example:
    ```python
    queries = [
        [
            ["child(Y_2, Y_3)", "sister(Elisa, Y_2)"],
            ["parent(Y_2, Y_3)", "brother(John, Y_2)"]
        ],
        [
            ["ancestor(Y_6, Y_7)", "cousin(Mike, Y_6)"]
            ["ancestor(Y_6, Y_7)", "nephew(Mike, Y_6)"]
        ]
    ]

    solution_traces, final_results = get_answer(queries, db, ["Y_3", "Y_7"])
    ```

    **Expected Output:**
    ```
    solution_traces = [
        [
            [
                [{"Y_2": "Alice", "Y_3": "Bob"}, {"Y_2": "Alice", "Y_3": "Rupert"}],
                [{"Y_2": "David", "Y_3": "Eve"}]
            ]
        ],
        [
            [
                [{"Y_6": "Sarah", "Y_7": "Tom"}]
                [{"Y_6": "George", "Y_7": "Jack"}]
            ]
        ]
    ]

    final_results = [
        [
            [
                ["Bob", "Rupert"],
                ["Eve"]
            ]
        ],
        [
            [
                ["Tom"],
                ["Jack"]
            ]
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
            c += 1

    for j in range(len(all_queries)):
        # This iterates through the templates queries
        query_results = all_query_results[j]  # These are thus the query results for one template
        answer = answers[j]  # This is the answer for one template

        solution_traces = []
        final_results = []

        for query_result in query_results:
            # Here, we iterate through query results of one single template

            if skip_solution_traces:
                logging.warning("Skipping solution traces")
                solution_trace = []

            else:
                # NOTE: for aggregation questions, prolog will create a Variable type
                # for the final placeholder of the query. These have indeterminate values,
                # and are not useful for solution traces. Moreover, decoding them and
                # saving them to a file (as part of solution_traces) will cause a segfault.
                # Hence, only decode values that are not Variables
                solution_trace: list[dict[str, str]] = [
                    {k: decode(v) for k, v in x.items() if not isinstance(v, Variable)} for x in query_result
                ]
                # solution_trace can contain duplicate dictionaries, keep only unique ones
                # frozenset is used to make the dictionaries hashable, and set to remove duplicates
                unique_solution_trace = {frozenset(d.items()) for d in solution_trace}
                solution_trace = [dict(s) for s in unique_solution_trace]

            final_result = [str(decode(x[answer])) for x in query_result]
            final_result = sorted(set(final_result))

            solution_traces.append(solution_trace)
            final_results.append(final_result)

        all_solution_traces.append(solution_traces)
        all_final_results.append(final_results)

    return all_solution_traces, all_final_results
