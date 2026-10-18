"""Write scanned results to CSV files"""

import os
import pandas as pd


def export(data, config, out_dir=None):
    """
    Writes all page results to one CSV
        data:       list of page results from validate.py
        config:     config file 
        out_dir:    output folder (defaults to config path)
    """
    out = config["output"]
    out_dir = out_dir or out["folder"]

    os.makedirs(out_dir, exist_ok=True)
    table = to_table(data, out["columns"])
    table.to_csv(os.path.join(out_dir, out["filename"]), index=False)

def to_table(rows, columns):
    """
    Builds a DataFrame with fixed columns
        rows:       list of page results
        columns:    column names
    """
    cleaned = [
        {
            k: mapping(v) 
            for k, v in row.items()
        } 
        for row in rows]
    
    return pd.DataFrame(cleaned, columns=columns, dtype=object).fillna("")

def mapping(item):
    """
    Turns answer lists into clean CSV values.
        item:       a single cell 
    """
    if type(item) != list:
        return item
    if len(item) == 1:
        return item[0]
    if type(item) == str:
        return item
    return ",".join(str(i) for i in item)