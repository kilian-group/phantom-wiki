def match(pred: str, true: str, exact: bool = True):
    """
    Simple score function that checks if the prediction is equal to the true answer
    """
    if exact:
        return pred == true
    return pred.find(true) != -1


def precision(pred, true):
    count = 0
    pred = set(pred.split(" "))
    for word in pred:
        count += word in true

    return count / len(pred)


def recall(pred, true):
    count = 0
    true = set(true.split(" "))
    for word in true:
        count += word in pred

    return count / len(true)


def f1(pred, true):
    pres = precision(pred, true)
    rec = recall(pred, true)

    return 2 * pres * rec / (pres + rec)
