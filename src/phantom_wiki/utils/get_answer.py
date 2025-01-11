from ..facts.database import Database
import logging

def get_answer(query: list[str], db: Database, answer: str):
    """Get the answer to a query from the database

    Args:
        query (list[str]): The query to be answered
            Example: [child(Y_2, Y_3), sister(Elisa, Y_2)]
        db (Database): The database to query
        answer (str): The answer to the query as a placeholder
            Example: "Y_3"

    Returns:
        all_results: list[dict]
            A list of dictionaries with the results of each subquery
        final_results: list[str] 
            The final results of the entire query

    Solve the query in reverse order: 
    First query the db with sister(Elisa, Y_2) and get ['Y_2': "Alice"] 
    Then query the db with child(Y_2, Y_3), sister(Elisa, Y_2) and get ['Y_3': "Bob", 'Y_2': "Alice"] 
    so all_results in this case is [{'Y_2': "Alice"}, {'Y_3': "Bob", 'Y_2': "Alice"}] 
    and final_results is ["Bob"] 
            
    """
    all_results=[]
    reversed_query = query[::-1]
    # to get intermediate answers, we get the answer for each subset of the query, each time incremented by one subquery
    for i in range(len(reversed_query)):
        intermediate_query =  ", ".join(reversed_query[:i+1])
        partial_results = db.query(intermediate_query)
        unique_results = {
            tuple(sorted((k, str(v)) for k, v in d.items()))
            for d in partial_results
        }
        unique_list = [dict(items) for items in unique_results] # list of dicts

        partial_results = sorted(unique_list, key=lambda x: tuple(x.items()))
        all_results.append(partial_results)
    final_results = [str(x[answer]) for x in db.query(", ".join(reversed_query))]
    final_results = sorted(set(final_results))

    return all_results, final_results