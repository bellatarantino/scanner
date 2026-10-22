"""Grab the answers from the raw extracted data and flag problems"""

def validate(scores, config, name):
    """
    Picks the marked bubbles in each region 
        scores:     brightness per bubble
        config:     config file 
        path:       page name
    """
    ratio = config["scoring"]["filled_ratio"]
    data = {"path": name, "error": False}

    for k, v in scores.items():
        values = v["brightness"]
        data[k] = pick_answers(values, ratio)

        # wrong number of bubbles found
        if len(values) != config["bubbles"][k]:
            data["error"] = True

        # 0 or 2+ marks 
        if len(data[k]) != 1:
            data["error"] = True

    return data

def pick_answers(scores, threshold=0.8):
    """
    Returns indices of bubbles chosen as answers
        values:     bubble brightness
        threshold:      threshold for classification as answer
    """
    if not scores:
        return []

    lightest = max(scores)
    return [i for i, v in enumerate(scores) if v < threshold * lightest]