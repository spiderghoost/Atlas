import argparse
import inspect
import json

import pandas as pd
from sklearn.model_selection import train_test_split

from src.config import ensure_dirs, load_config
from src.data import clean, load_raw
from src.evaluate import compute_metrics, temporal_purged_split
from src.features import build_features
from src.models import fit_lightgbm_monotone, fit_logistic

DEFAULT_FEATURES = ["dti", "income_to_loan", "utilization", "derog_markers", "inq_last_6m"]


def _select_features(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    columns = config["data"]["feature_columns"] or DEFAULT_FEATURES
    available = [c for c in columns if c in df.columns]
    return df[available]


def run(config_path: str) -> None:
    config = load_config(config_path)
    ensure_dirs(config)
    seed = config["model"]["seed"]

    df = load_raw(config)
    df = clean(df, config)
    df = build_features(df, config)
    df = df.dropna(subset=[config["data"]["target_column"]])

    train, test = temporal_purged_split(df, config)
    target = config["data"]["target_column"]
    X_train, X_test = _select_features(train, config), _select_features(test, config)
    y_train, y_test = train[target].values, test[target].values

    results = {}
    results["logistic"] = _eval_model(
        fit_logistic, X_train, y_train, X_test, y_test,
        config["model"]["baseline_logistic"], seed,
    )
    results["lightgbm_monotone"] = _eval_model(
        fit_lightgbm_monotone, X_train, y_train, X_test, y_test,
        config["model"]["lightgbm_monotone"], seed,
    )

    out_path = f"{config['outputs']['results_dir']}/baselines.json"
    with open(out_path, "w") as fh:
        json.dump(results, fh, indent=2)
    print(json.dumps(results, indent=2))
    print(f"wrote {out_path}")


def _eval_model(fit_fn, X_train, y_train, X_test, y_test, params, seed):
    params = dict(params)
    params.setdefault("random_state", seed)
    kwargs = {}
    if "eval_X" in inspect.signature(fit_fn).parameters and "early_stopping_rounds" in params:
        X_train, X_val, y_train, y_val = train_test_split(
            X_train, y_train, test_size=0.15, random_state=seed, stratify=y_train
        )
        kwargs.update(eval_X=X_val, eval_y=y_val)
    clf = fit_fn(X_train, y_train, params, **kwargs)
    proba = clf.predict_proba(X_test)[:, 1]
    return compute_metrics(y_test, proba)


def main() -> None:
    parser = argparse.ArgumentParser(description="Deterministic baseline pipeline")
    parser.add_argument("--config", default="configs/default.yaml")
    args = parser.parse_args()
    run(args.config)


if __name__ == "__main__":
    main()
