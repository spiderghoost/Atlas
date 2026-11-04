"""
ATLAS Systemic Crisis Early Warning Classifier Trainer
========================================================
Implements the methodology defined in the ATLAS research paper:
  • Problem: Supervised binary classification (Predicts crisis in year t+1)
  • Baseline: Logistic Regression (IMF standard baseline, Laeven & Valencia 2020)
  • Main Model: XGBoost Classifier (tree ensemble capturing non-linear distress thresholds)
  • Explainability: SHAP TreeExplainer (feature attributions per country, Lundberg & Lee 2017)
  • Tracking: MLflow integration for experiment auditability
"""

import os
import sys
import json
import warnings
import numpy as np
import pandas as pd
import mlflow
import mlflow.sklearn
import mlflow.xgboost
import shap
import joblib
from pathlib import Path

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score,
    brier_score_loss,
    confusion_matrix,
)
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

RESULTS_DIR = BASE_DIR / "results" / "early_warning"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_END_YEAR = 2019
TEST_START_YEAR = 2020
RANDOM_SEED = 42


def temporal_split(X: pd.DataFrame, y: pd.Series) -> tuple:
    """
    Splits by time to strictly avoid forward-looking data leakage.
    Train: 2000-2019 | Test: 2020-2024 (real-world out-of-time evaluation)
    """
    train_mask = X["year"] <= TRAIN_END_YEAR
    test_mask = X["year"] >= TEST_START_YEAR

    X_train = X[train_mask].drop(columns=["country_id", "year"])
    X_test = X[test_mask].drop(columns=["country_id", "year"])
    y_train = y[train_mask]
    y_test = y[test_mask]

    print(f"  Train: {train_mask.sum()} samples (crises={int(y_train.sum())}) | Test: {test_mask.sum()} samples (crises={int(y_test.sum())})")
    return X_train, X_test, y_train, y_test


def compute_classification_metrics(y_true, y_prob, threshold: float = 0.30, label: str = "Model") -> dict:
    """
    Computes comprehensive crisis detection metrics:
    AUC-ROC, PR-AUC, Precision, Recall, F1, and Brier score.
    """
    y_pred = (y_prob >= threshold).astype(int)

    auc_roc = roc_auc_score(y_true, y_prob)
    pr_auc = average_precision_score(y_true, y_prob)
    rec = recall_score(y_true, y_pred, zero_division=0)
    prec = precision_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    brier = brier_score_loss(y_true, y_prob)

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    print(f"  [{label}] ROC-AUC={auc_roc:.3f} | PR-AUC={pr_auc:.3f} | Recall={rec:.1%} | Precision={prec:.1%} | F1={f1:.3f} | Brier={brier:.3f}")
    print(f"         TP={tp}, FP={fp}, TN={tn}, FN={fn} (at threshold {threshold:.2f})")

    return {
        "roc_auc": round(float(auc_roc), 4),
        "pr_auc": round(float(pr_auc), 4),
        "recall": round(float(rec), 4),
        "precision": round(float(prec), 4),
        "f1": round(float(f1), 4),
        "brier_score": round(float(brier), 4),
        "confusion_matrix": {"tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn)},
    }


def train_early_warning_system(horizon: str = "1y") -> dict:
    """
    Full training and evaluation pipeline for the Crisis Early Warning Classifier.
    """
    from src.early_warning.data_builder import get_early_warning_data

    print(f"\n{'='*65}")
    print(f"  ATLAS CRISIS EARLY WARNING SYSTEM -- Horizon: {horizon.upper()}")
    print(f"{'='*65}")

    # 1. Load Data
    X, y, feature_names = get_early_warning_data(horizon)
    X_train, X_test, y_train, y_test = temporal_split(X, y)

    # 2. Impute missing values with median
    imputer = SimpleImputer(strategy="median")
    X_train_imp = imputer.fit_transform(X_train[feature_names])
    X_test_imp = imputer.transform(X_test[feature_names])

    # Calculate class imbalance weighting ratio for XGBoost
    neg_count = int((y_train == 0).sum())
    pos_count = max(1, int((y_train == 1).sum()))
    scale_pos_weight = float(neg_count / pos_count)

    results = {
        "horizon": horizon,
        "features": feature_names,
        "class_balance_train": {"normal": neg_count, "crisis": pos_count, "ratio": round(scale_pos_weight, 2)},
    }

    # ── 3. BASELINE MODEL: Logistic Regression (IMF Econometric Benchmark) ────
    print("\n  [1/3] Baseline Model -- Logistic Regression (L2 / Balanced)")
    with mlflow.start_run(run_name=f"baseline_logistic_ews_{horizon}"):
        mlflow.set_tag("module", "early_warning")
        mlflow.set_tag("model_type", "logistic_regression")
        mlflow.log_param("horizon", horizon)

        scaler = StandardScaler()
        X_tr_scaled = scaler.fit_transform(X_train_imp)
        X_te_scaled = scaler.transform(X_test_imp)

        logit = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=RANDOM_SEED)
        logit.fit(X_tr_scaled, y_train)
        probs_logit = logit.predict_proba(X_te_scaled)[:, 1]

        logit_metrics = compute_classification_metrics(y_test, probs_logit, threshold=0.35, label="Logistic")
        mlflow.log_metrics({k: v for k, v in logit_metrics.items() if isinstance(v, (int, float))})
        results["baseline_logistic"] = logit_metrics

    # ── 4. MAIN MODEL: XGBoost Classifier ─────────────────────────────────────
    print("\n  [2/3] Main Model -- XGBoost Classifier (Tree Ensemble)")
    xgb_params = {
        "n_estimators": 400,
        "max_depth": 4,
        "learning_rate": 0.03,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "scale_pos_weight": scale_pos_weight * 0.7, # tuned imbalance penalty
        "random_state": RANDOM_SEED,
        "eval_metric": "aucpr",
        "use_label_encoder": False,
    }

    with mlflow.start_run(run_name=f"xgboost_ews_{horizon}"):
        mlflow.set_tag("module", "early_warning")
        mlflow.set_tag("model_type", "xgboost")
        mlflow.log_params(xgb_params)

        xgb_model = XGBClassifier(**xgb_params)
        xgb_model.fit(
            X_train_imp, y_train,
            eval_set=[(X_test_imp, y_test)],
            verbose=False,
        )
        probs_xgb = xgb_model.predict_proba(X_test_imp)[:, 1]

        xgb_metrics = compute_classification_metrics(y_test, probs_xgb, threshold=0.30, label="XGBoost")
        mlflow.log_metrics({k: v for k, v in xgb_metrics.items() if isinstance(v, (int, float))})
        results["xgboost"] = xgb_metrics

    # ── 5. SHAP EXPLAINABILITY (Lundberg & Lee 2017) ───────────────────────────
    print("\n  [3/3] Explainability -- Game-Theoretic SHAP Attributions")
    explainer = shap.TreeExplainer(xgb_model)
    shap_values = explainer.shap_values(X_test_imp)
    mean_abs_shap = np.abs(shap_values).mean(axis=0)

    shap_importance = dict(zip(feature_names, mean_abs_shap.tolist()))
    shap_sorted = dict(sorted(shap_importance.items(), key=lambda x: x[1], reverse=True))
    results["shap_importance"] = shap_sorted

    print("  Top 5 Leading Indicators of Crisis Vulnerability (SHAP):")
    for feat, val in list(shap_sorted.items())[:5]:
        bar = "#" * int(val * 15)
        print(f"    {feat:25s}  {val:.4f}  {bar}")

    # ── 6. GENERATE COUNTRY RISK PROFILES & FORWARD PROJECTIONS ────────────────
    from src.early_warning.data_builder import load_early_warning_panel, engineer_early_warning_features
    full_panel = load_early_warning_panel()
    full_panel = engineer_early_warning_features(full_panel)

    recent_panel = full_panel[full_panel["year"] >= TEST_START_YEAR].copy()
    recent_panel_imp = imputer.transform(recent_panel[feature_names])
    probs_all = xgb_model.predict_proba(recent_panel_imp)[:, 1]

    country_risk_scores = []
    for i, (_, row) in enumerate(recent_panel.iterrows()):
        p = float(probs_all[i])
        tier = "High" if p >= 0.35 else ("Moderate" if p >= 0.15 else "Low")
        base_yr = int(row["year"])
        fc_yr = base_yr + 1
        country_risk_scores.append({
            "country": row["country_id"],
            "year": base_yr,
            "base_data_year": base_yr,
            "forecast_year": fc_yr,
            "forecast_window": f"{fc_yr} - {max(fc_yr, 2026)}",
            "crisis_probability": round(p, 4),
            "crisis_probability_pct": round(p * 100, 1),
            "risk_tier": tier,
        })

    # Save trained model artifact for online inference
    model_artifact = {
        "model": xgb_model,
        "imputer": imputer,
        "features": feature_names,
    }
    joblib.dump(model_artifact, RESULTS_DIR / f"early_warning_{horizon}_model.joblib")

    # Save to disk
    out_results = RESULTS_DIR / f"early_warning_{horizon}_results.json"
    with open(out_results, "w") as f:
        json.dump(results, f, indent=2)

    out_preds = RESULTS_DIR / f"early_warning_{horizon}_predictions.json"
    with open(out_preds, "w") as f:
        json.dump(country_risk_scores, f, indent=2)

    print(f"\n  Results saved -> {out_results}")
    print(f"  Model artifact saved -> {RESULTS_DIR / f'early_warning_{horizon}_model.joblib'}")
    print(f"  Country risk scores saved -> {out_preds} ({len(country_risk_scores)} total predictions)")

    # Print a sample of latest forward projections
    max_year = max(c["base_data_year"] for c in country_risk_scores)
    latest_risks = [c for c in country_risk_scores if c["base_data_year"] == max_year][:8]
    print(f"\n  Sample Forward Projections (Base Data: {max_year} -> Forecast: {max_year + 1}-2026):")
    for r in latest_risks:
        print(f"    {r['country']} (Data: {r['base_data_year']} -> Forecast {r['forecast_window']}): {r['crisis_probability_pct']:5.1f}% risk  [{r['risk_tier']:8s}]")

    return results


if __name__ == "__main__":
    mlflow.set_experiment("ATLAS-Crisis-Early-Warning")
    res = train_early_warning_system("1y")
    print(f"\nTraining complete. Main XGBoost ROC-AUC: {res['xgboost']['roc_auc']:.3f} (vs Logistic {res['baseline_logistic']['roc_auc']:.3f})")
