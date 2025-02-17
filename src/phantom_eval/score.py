from phantom_eval import constants
from phantom_eval.utils import normalize_pred


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
    normalized_preds: set[str] = normalize_pred(pred, sep)
    normalized_trues: set[str] = normalize_pred(true, sep)
    count = 0
    for word in normalized_preds:
        count += word in normalized_trues

    return count / len(normalized_preds)


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
    normalized_preds: set[str] = normalize_pred(pred, sep)
    normalized_trues: set[str] = normalize_pred(true, sep)
    count = 0
    for word in normalized_trues:
        count += word in normalized_preds

    return count / len(normalized_trues)


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
