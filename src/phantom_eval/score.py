def match(
        pred: str, 
        true: str, 
        exact: bool = True
    ):
    """
    Simple score function that checks if the prediction is equal to the true answer
    """
    if exact:
        return pred == true
    return pred.find(true) != -1
