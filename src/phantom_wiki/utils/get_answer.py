from ..facts.database import Database


def get_answer(query: list[str], db: Database, answer: str):
    """Get the answer to a query from the database

    Args:
        query (list[str]): The query to be answered
        db (Database): The database to query
        answer (str): The answer to the query

    Returns:
        all_results: list[dict]
            A list of dictionaries with the results of each subquery
        final_results: list[str] 
            The final results of the entire query
            
    """
    all_results=[]
    reversed_query = query[::-1]
    # to get intermediate answers, we get the answer for each subset of the query, each time incremented by one subquery
    for i in range(len(reversed_query)):
        partial_results = db.query(", ".join(reversed_query[:i+1]))
        unique_dicts = {tuple(sorted(d.items())) for d in partial_results}
        unique_list = [dict(items) for items in unique_dicts]
        # some of the values are of Variable type which is not hashable type so we need to convert them to str
        unique_list = [{k: str(v) for k, v in d.items()} for d in unique_list]
        partial_results = sorted(unique_list, key=lambda x: tuple(x.items()))
        all_results.append(partial_results)
    final_results = [str(x[answer]) for x in db.query(", ".join(reversed_query))]
    final_results = sorted(set(final_results))

    return all_results, final_results