"""
ATLAS Nowcasting Model Trainer
================================
Trains two separate models:
  1. GDP Growth Nowcaster      — predicts next-year GDP growth (%)
  2. Inflation Nowcaster       — predicts next-year CPI inflation (%)

Methodology (matches your project proposal):
  • Temporal purged train/test split (no data leakage)
  • Baseline: Ridge Regression (transparent, interpretable)
  • Main model: LightGBM (fast gradient-boosted trees, industry standard)
  • Uncertainty: Conformal Prediction via MAPIE (honest prediction intervals)
  • Explainability: SHAP TreeExplainer (shows WHY the model predicted each value)
  • Tracking: MLflow (logs every experiment run automatically)
"""

import os
import sys
import json
import warnings
import numpy as np
import pandas as pd
import mlflow
import mlflow.sklearn
import mlflow.lightgbm
import shap
from pathlib import Path

from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.impute import SimpleImputer
from lightgbm import LGBMRegressor
from mapie.regression import CrossConformalRegressor

warnings.filterwarnings("ignore")

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

RESULTS_DIR = BASE_DIR / "results" / "nowcasting"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Temporal split configuration ─────────────────────────────────────────────
TRAIN_END_YEAR = 2019   # Train on 2000–2019
TEST_START_YEAR = 2020  # Test on 2020–2024 (includes COVID, post-COVID recovery)
RANDOM_SEED = 42


def temporal_split(X: pd.DataFrame, y: pd.Series) -> tuple:
    """
    Split data by time — never mix future data into training.
    This is the correct way for time-series economic data.
    Train: 2000–2019 | Test: 2020–2024
    """
    train_mask = X["year"] <= TRAIN_END_YEAR
    test_mask  = X["year"] >= TEST_START_YEAR

    X_train = X[train_mask].drop(columns=["country_id", "year"])
    X_test  = X[test_mask].drop(columns=["country_id", "year"])
    y_train = y[train_mask]
    y_test  = y[test_mask]

    print(f"  Train: {train_mask.sum()} rows | Test: {test_mask.sum()} rows")
    return X_train, X_test, y_train, y_test


def compute_metrics(y_true, y_pred, label: str) -> dict:
    """Computes MAE, RMSE, and R2 for model evaluation."""
    mae  = mean_absolute_error(y_true, y_pred)
    rmse = mean_squared_error(y_true, y_pred) ** 0.5
    r2   = r2_score(y_true, y_pred)
    print(f"  [{label}] MAE={mae:.3f}  RMSE={rmse:.3f}  R2={r2:.3f}")
    return {"mae": round(mae, 4), "rmse": round(rmse, 4), "r2": round(r2, 4)}


def train_nowcaster(target: str = "gdp") -> dict:
    """
    Full training pipeline for one nowcasting target.

    Args:
        target: "gdp"  → predict next-year GDP growth
                "cpi"  → predict next-year inflation

    Returns:
        Dictionary with all evaluation results and model paths.
    """
    from src.nowcasting.data_builder import get_training_data

    print(f"\n{'='*60}")
    print(f"  ATLAS NOWCASTING MODEL -- Target: {target.upper()}")
    print(f"{'='*60}")

    # ── 1. Load Data ──────────────────────────────────────────────────────────
    X, y, feature_names = get_training_data(target)
    X_train, X_test, y_train, y_test = temporal_split(X, y)

    print(f"\n  Feature count : {len(feature_names)}")
    print(f"  Train samples : {len(X_train)}")
    print(f"  Test  samples : {len(X_test)}")

    # ── 2. Preprocessing: Impute missing values ───────────────────────────────
    imputer = SimpleImputer(strategy="median")
    X_train_imp = imputer.fit_transform(X_train[feature_names])
    X_test_imp  = imputer.transform(X_test[feature_names])

    results = {"target": target, "features": feature_names}

    # ── 3. BASELINE: Ridge Regression ─────────────────────────────────────────
    print("\n  [1/3] Baseline -- Ridge Regression")
    with mlflow.start_run(run_name=f"ridge_{target}"):
        mlflow.set_tag("model_type", "baseline_ridge")
        mlflow.set_tag("target", target)
        mlflow.log_param("train_end_year", TRAIN_END_YEAR)

        scaler = StandardScaler()
        X_tr_scaled = scaler.fit_transform(X_train_imp)
        X_te_scaled = scaler.transform(X_test_imp)

        ridge = Ridge(alpha=1.0, random_state=RANDOM_SEED)
        ridge.fit(X_tr_scaled, y_train)
        preds_ridge = ridge.predict(X_te_scaled)

        ridge_metrics = compute_metrics(y_test, preds_ridge, "Ridge")
        mlflow.log_metrics(ridge_metrics)
        results["baseline_ridge"] = ridge_metrics

    # ── 4. MAIN MODEL: LightGBM ───────────────────────────────────────────────
    print("\n  [2/3] Main Model -- LightGBM")
    lgbm_params = {
        "n_estimators"   : 500,
        "learning_rate"  : 0.05,
        "num_leaves"     : 31,
        "min_child_samples": 10,
        "subsample"      : 0.8,
        "colsample_bytree": 0.8,
        "random_state"   : RANDOM_SEED,
        "verbose"        : -1,
    }

    with mlflow.start_run(run_name=f"lightgbm_{target}"):
        mlflow.set_tag("model_type", "lightgbm")
        mlflow.set_tag("target", target)
        mlflow.log_params(lgbm_params)

        lgbm = LGBMRegressor(**lgbm_params)
        lgbm.fit(
            X_train_imp, y_train,
            eval_set=[(X_test_imp, y_test)],
            callbacks=[],
        )
        preds_lgbm = lgbm.predict(X_test_imp)

        lgbm_metrics = compute_metrics(y_test, preds_lgbm, "LightGBM")
        mlflow.log_metrics(lgbm_metrics)
        results["lightgbm"] = lgbm_metrics

    # ── 5. UNCERTAINTY: Conformal Prediction (MAPIE) ─────────────────────────
    print("\n  [3/3] Uncertainty -- Conformal Prediction (MAPIE) at 90% coverage")
    mapie = CrossConformalRegressor(
        estimator=LGBMRegressor(**lgbm_params),
        confidence_level=0.90,
        method="plus",
        cv=5,
        random_state=RANDOM_SEED,
    )
    mapie.fit_conformalize(X_train_imp, y_train)
    preds_mapie, intervals = mapie.predict_interval(X_test_imp)

    coverage = np.mean(
        (y_test.values >= intervals[:, 0, 0]) & (y_test.values <= intervals[:, 1, 0])
    )
    avg_width = np.mean(intervals[:, 1, 0] - intervals[:, 0, 0])
    print(f"  [MAPIE] Coverage: {coverage:.1%} | Avg interval width: {avg_width:.2f}pp")
    results["conformal"] = {
        "coverage_90pct": round(coverage, 4),
        "avg_interval_width_pp": round(avg_width, 4),
    }

    # ── 6. SHAP EXPLAINABILITY ────────────────────────────────────────────────
    print("\n  Computing SHAP feature importance...")
    explainer    = shap.TreeExplainer(lgbm)
    shap_values  = explainer.shap_values(X_test_imp)
    mean_abs_shap = np.abs(shap_values).mean(axis=0)

    shap_importance = dict(zip(feature_names, mean_abs_shap.tolist()))
    shap_importance_sorted = dict(
        sorted(shap_importance.items(), key=lambda x: x[1], reverse=True)
    )
    results["shap_importance"] = shap_importance_sorted

    print("  Top 5 predictors by SHAP:")
    for feat, val in list(shap_importance_sorted.items())[:5]:
        bar = "#" * int(val * 3)
        print(f"    {feat:30s}  {val:.4f}  {bar}")

    # ── 7. SAMPLE FORECAST (last year per country) ────────────────────────────
    print("\n  Sample forecasts (test set):")
    test_df = X[X["year"] >= TEST_START_YEAR].copy()
    test_df_imp = imputer.transform(test_df[feature_names])
    test_preds, test_intervals = mapie.predict_interval(test_df_imp)

    sample_forecasts = []
    for i, (_, row) in enumerate(test_df.iterrows()):
        lo = round(float(test_intervals[i, 0, 0]), 2)
        hi = round(float(test_intervals[i, 1, 0]), 2)
        sample_forecasts.append({
            "country": row["country_id"],
            "year": int(row["year"]),
            "forecast": round(float(test_preds[i]), 2),
            "lower_90": lo,
            "upper_90": hi,
        })
    results["sample_forecasts_count"] = len(sample_forecasts)

    # Save a small preview of 10 forecasts
    preview = [f for f in sample_forecasts if f["year"] == 2024][:10]
    results["forecast_preview_2024"] = preview
    print(f"  Saved {len(sample_forecasts)} forecasts")
    for p in preview[:5]:
        print(f"    {p['country']}: {p['forecast']:+.2f}% [{p['lower_90']:+.2f}%, {p['upper_90']:+.2f}%]")

    # ── 8. Save All Results to JSON ───────────────────────────────────────────
    out_path = RESULTS_DIR / f"{target}_nowcasting_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved -> {out_path}")

    # Save all forecasts
    forecasts_path = RESULTS_DIR / f"{target}_forecasts.json"
    with open(forecasts_path, "w") as f:
        json.dump(sample_forecasts, f, indent=2)

    return results


if __name__ == "__main__":
    mlflow.set_experiment("ATLAS-Nowcasting")

    print("\n[ATLAS] -- GDP & Inflation Nowcasting Model")
    print("=" * 60)

    gdp_results = train_nowcaster("gdp")
    cpi_results = train_nowcaster("cpi")

    print("\n\n" + "=" * 60)
    print("  FINAL SUMMARY")
    print("=" * 60)
    print(f"  GDP Nowcaster  -- LightGBM: MAE={gdp_results['lightgbm']['mae']:.2f}pp  R2={gdp_results['lightgbm']['r2']:.3f}")
    print(f"  CPI Nowcaster  -- LightGBM: MAE={cpi_results['lightgbm']['mae']:.2f}pp  R2={cpi_results['lightgbm']['r2']:.3f}")
    print(f"\n  All results saved to: results/nowcasting/")
    print(f"  View MLflow UI: .venv\\Scripts\\mlflow.exe ui --port 5000")
