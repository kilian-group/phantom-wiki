from phantom_eval import constants


def normalize_pred(pred: str, sep: str) -> set[str]:
    """
    Normalize the prediction by splitting and stripping whitespace the answers.

    Args:
        pred (str): The prediction string of format "A<sep>B<sep>C".
        sep (str): The separator used to split the prediction.

    Returns:
        set[str]: A set of normalized answers.
    """
    # Operations:
    # 1. Split by separator
    # 2. Strip whitespace
    # 3. Lowercase
    # 4. Convert to set to remove duplicates
    return set(
        map(str.lower,
        map(str.strip,
            pred.split(sep)
        ))
    )


def exact_match(
        pred: str, 
        true: str, 
        sep: str = constants.answer_sep,
    ) -> bool:
    """
    Simple score function that checks if the prediction is equal to the true answer
    """
    return normalize_pred(pred, sep) == normalize_pred(true, sep)


def precision(
        pred: str, 
        true: str,
        sep: str = constants.answer_sep,
    ) -> float:
    """
    Assume:
    - true is an arbitrary string, which can be empty, separated by spaces/commas/etc
    - pred is a string of words separated by `sep`
    """
    count = 0
    pred = set(pred.split(sep))
    for word in pred:
        count += word in true

    return count / len(pred)


def recall(
        pred: str, 
        true: str,
        sep: str = constants.answer_sep,
    ) -> float:
    """
    Assume:
    - true is a string of words separated by `sep`
    - pred is an arbitrary string, which can be empty, separated by spaces/commas/etc
    """
    count = 0
    true = set(true.split(sep))
    for word in true:
        count += word in pred

    return count / len(true)


def f1(
        pred: str, 
        true: str,
        sep: str = constants.answer_sep,
    ) -> float:
    pres = precision(pred, true, sep)
    rec = recall(pred, true, sep)
    if pres + rec == 0:
        return 0

    return 2 * pres * rec / (pres + rec)
