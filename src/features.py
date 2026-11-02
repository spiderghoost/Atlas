import numpy as np
import pandas as pd


def build_features(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    out = df.copy()
    for name in config["features"]["derived"]:
        out[name] = _derive(name, out)
    return out


def _derive(name: str, df: pd.DataFrame) -> pd.Series:
    if name == "dti":
        return df["dti"] if "dti" in df else pd.Series(np.nan, index=df.index)
    if name == "income_to_loan":
        return df["annual_inc"] / df["loan_amnt"].clip(lower=1)
    if name == "utilization":
        return df["revol_bal"] / df["revol_lim"].clip(lower=1)
    if name == "derog_markers":
        return df["delinq_2yrs"] + df["pub_rec"]
    if name == "inq_last_6m":
        return df["inq_last_6mths"]
    raise ValueError(f"unknown derived feature: {name}")
