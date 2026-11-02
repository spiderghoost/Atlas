import numpy as np
import pandas as pd
from sklearn.metrics import auc, brier_score_loss, precision_recall_curve, roc_auc_score


def temporal_purged_split(
    df: pd.DataFrame, config: dict
) -> tuple[pd.DataFrame, pd.DataFrame]:
    split_cfg = config["split"]
    date_col = config["data"]["date_column"]
    purge_days = split_cfg["purge_days"]
    ordered = df.sort_values(date_col)
    cutoff = ordered[date_col].quantile(1 - split_cfg["test_fraction"])
    cutoff = cutoff - pd.Timedelta(days=purge_days)
    test = ordered[ordered[date_col] >= cutoff]
    train = ordered[ordered[date_col] < cutoff]
    return train, test


def compute_metrics(y_true: np.ndarray, proba: np.ndarray) -> dict:
    p, r, _ = precision_recall_curve(y_true, proba)
    ks = _ks_statistic(y_true, proba)
    return {
        "roc_auc": roc_auc_score(y_true, proba),
        "pr_auc": auc(r, p),
        "brier": brier_score_loss(y_true, proba),
        "ks": ks,
    }


def _ks_statistic(y_true: np.ndarray, proba: np.ndarray) -> float:
    df = pd.DataFrame({"y": y_true, "p": proba})
    pos = df[df["y"] == 1]["p"]
    neg = df[df["y"] == 0]["p"]
    grid = np.linspace(0.0, 1.0, 1000)
    cdf_pos = np.array([(pos <= g).mean() for g in grid])
    cdf_neg = np.array([(neg <= g).mean() for g in grid])
    return float(np.max(np.abs(cdf_pos - cdf_neg)))
