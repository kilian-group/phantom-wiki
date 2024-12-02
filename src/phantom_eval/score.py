def match(
        pred: str, 
        true: str, 
        exact: bool = True
    ) -> bool:
    """
    Simple score function that checks if the prediction is equal to the true answer
    """
    if exact:
        return pred == true
    return pred.find(true) != -1


def precision(
        pred: str, 
        true: str,
        sep: str = ", "
    ) -> float:
    """
    Assume:
    - true is an arbitrary string, which can be empty, separated by spaces/commas/etc
    - pred is a string of words separated by `sep`
    """
    if len(pred) == 0 or len(true) == 0:
        return 0
    count = 0
    pred = set(pred.split(sep))
    for word in pred:
        count += word in true

    return count / len(pred)


def recall(
        pred: str, 
        true: str,
        sep: str = ", "
    ) -> float:
    """
    Assume:
    - true is a string of words separated by `sep`
    - pred is an arbitrary string, which can be empty, separated by spaces/commas/etc
    """
    if len(pred) == 0 or len(true) == 0:
        return 0
    count = 0
    true = set(true.split(sep))
    for word in true:
        count += word in pred

    return count / len(true)


def f1(
        pred: str, 
        true: str,
        sep: str = ", "
    ) -> float:
    if len(pred) == 0 or len(true) == 0:
        return 0
    pres = precision(pred, true, sep)
    rec = recall(pred, true, sep)
    if pres + rec == 0:
        return 0

    return 2 * pres * rec / (pres + rec)
