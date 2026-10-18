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

    data["student_number"] = student_number(data)
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

def student_number(data):
    """
    Combines tens and ones into student number 
        data:       single page data
    """
    tens, ones = data.get("tens", []), data.get("ones", [])

    # add together if each has 1 
    if (len(tens) == 1) and (len(ones) == 1):
        return f"{tens[0]}{ones[0]}"
    
    return ""

def flag_duplicates(data):
    """
    Flags duplicate student numbers in same batch as possible errors 
        data:       list of page results
    """
    numbers = [d["student_number"] for d in data if not d["error"]]

    for item in data:
        if (not item["error"]) and (numbers.count(item["student_number"]) > 1):
            item["error"] = True

    return data