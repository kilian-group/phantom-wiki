import logging

from phantom_eval import constants
from phantom_eval.llm import LLMChatResponse
from phantom_wiki.facts.database import Database


def split_prolog_query(query: str) -> tuple[list[str], str | None]:
    """Split a compound Prolog query into individual queries and get final variable.
    This is a helper function for get_prolog_results that is used for debugging purposes.

    Args:
        query: A Prolog query string like "?- hobby(X, 'bus spotting'), father(X, Y)."

    Returns:
        Tuple of (list of query strings, final variable letter or None)
        Example: (["hobby(X, 'bus spotting')", "father(X, Y)"], "Y")
    """

    # First clean up the full query
    query = query.strip()
    if query.startswith("?-"):
        query = query[2:].strip()
    if query.endswith("."):
        query = query[:-1].strip()

    # Split on comma but respect parentheses and quotes
    queries = []
    current = []
    paren_count = 0
    in_quotes = False

    for char in query:
        if char == "'" and not in_quotes:
            in_quotes = True
            current.append(char)
        elif char == "'" and in_quotes:
            in_quotes = False
            current.append(char)
        elif char == "(" and not in_quotes:
            paren_count += 1
            current.append(char)
        elif char == ")" and not in_quotes:
            paren_count -= 1
            current.append(char)
        elif char == "," and paren_count == 0 and not in_quotes:
            queries.append("".join(current).strip())
            current = []
        else:
            current.append(char)

    if current:
        queries.append("".join(current).strip())

    # Get final variable from last predicate
    final_variable = None
    if queries:
        last_pred = queries[-1]
        variables = [c for c in last_pred if c.isupper()]
        if variables:
            final_variable = variables[-1]

    return queries, final_variable


def get_prolog_results(
    responses: list[LLMChatResponse], db: Database, logger: logging.Logger, debug: bool = False
) -> list[dict]:
    """Process a list of Prolog query responses and retrieve results from the database.

    This function takes a list of responses containing Prolog queries, executes them against
    the provided database, and returns the results along with any variable bindings. It handles
    errors gracefully, logging them and stopping execution if a query fails. The function can
    operate in a debug mode, which executes the sub-queries as separate queries, allowing for
    detailed tracking of each query's execution.

    Args:
        responses: A list of LLMChatResponse objects, each containing a Prolog query string
                   to be executed.
        db: An instance of the Database class used to execute the Prolog queries.
        logger: A logging.Logger instance used to log errors and debug information.
        debug: A boolean flag indicating whether to run in debug mode. If set to True, the
               function will execute all sub-queries as separate queries, allowing for
               detailed tracking of each query's execution. If False, it will treat the
               entire query as a single compound query.

    Returns:
        A list of dictionaries, each containing the final value of the target variable,
        the original query string, and a list of query results. Each result includes the
        executed query, any sub-queries added, the result of the query, and the variable
        bindings at that point in execution.

        Example:
        [
            {
                'final_value': 'some_value',
                'query': "hobby(X, 'bus spotting'), father(X, Y)",
                'query_results': [
                    {
                        'query': "hobby(X, 'bus spotting')",
                        'sub_query_added': "hobby(X, 'bus spotting')",
                        'result': [{'X': 'John'}],
                        'variables': {}
                    },
                    ...
                ]
            },
            ...
        ]
    """

    prolog_results = []
    for response in responses:
        query_results = []
        pred_query = response.pred
        sub_queries, target_variable = split_prolog_query(pred_query)
        if not debug:
            sub_queries = [pred_query]

        # Build the compound query incrementally
        compound_query = ""
        variable_bindings = {}

        for sub_query in sub_queries:
            try:
                # Add this sub_query to compound query
                if compound_query:
                    compound_query += f", {sub_query}"
                else:
                    compound_query = sub_query

                # Execute the compound query up to this point
                result = db.query(compound_query)

                # Convert any bytes in the result to strings
                decoded_result = []
                if result:
                    for binding in result:
                        decoded_binding = {}
                        for key, value in binding.items():
                            if isinstance(value, bytes):
                                decoded_binding[key] = value.decode("utf-8")
                            else:
                                # NOTE: the first if-statement doesn't seem to handle
                                # the case when the value is a Variable
                                # so I just convert everything else to a string
                                decoded_binding[key] = str(value)
                        decoded_result.append(decoded_binding)

                # Store result and variable bindings
                query_results.append(
                    {
                        "query": compound_query,
                        "sub_query_added": sub_query,
                        "result": decoded_result,
                        "variables": variable_bindings.copy(),
                    }
                )

                # Update variable bindings from result
                if decoded_result:
                    for binding in decoded_result:
                        variable_bindings.update(binding)

            except Exception as e:
                logger.error(f"Query failed: {compound_query}")
                logger.error(f"Error: {str(e)}")
                query_results.append(
                    {
                        "query": compound_query,
                        "sub_query_added": sub_query,
                        "error": str(e),
                        "variables": variable_bindings.copy(),
                    }
                )
                break  # Stop if any part fails

        # Get final value for target variable
        final_value = set()
        if query_results and query_results[-1].get("result") and target_variable:
            for binding in query_results[-1]["result"]:
                if target_variable in binding:
                    final_value.add(binding[target_variable])
        if len(final_value) == 0:
            # NOTE: the score functions expect a string, so we need to return an empty string
            final_value_str = ""
        elif len(final_value) == 1:
            final_value_str = str(final_value.pop())
        else:
            # NOTE: the score functions expect a string, so we need to join the list using a separator
            final_value_str = constants.answer_sep.join([str(v) for v in list(final_value)])

        prolog_results.append(
            {"final_value": final_value_str, "query": pred_query, "query_results": query_results}
        )
    return prolog_results
