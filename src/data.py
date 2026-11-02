import pandas as pd


def load_raw(config: dict) -> pd.DataFrame:
    path = config["data"]["raw_path"]
    df = pd.read_csv(path, low_memory=False)
    df[config["data"]["date_column"]] = pd.to_datetime(df[config["data"]["date_column"]])
    return df


def clean(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    target = config["data"]["target_column"]
    out = df.copy()
    out = out[out[target].notna()]
    out = out.drop_duplicates(subset=[config["data"]["id_column"]])
    return out
