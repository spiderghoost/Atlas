"""
ATLAS Crisis Early Warning Inference Engine
=============================================
Provides real-time crisis risk evaluation, risk categorization,
and SHAP driver breakdowns for any sovereign economy.
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = BASE_DIR / "results" / "early_warning"


def get_country_crisis_risk(country_iso3: str, horizon: str = "1y") -> Optional[Dict[str, Any]]:
    """
    Returns the latest systemic crisis probability and risk tier for a country.
    """
    preds_file = RESULTS_DIR / f"early_warning_{horizon}_predictions.json"
    if not preds_file.exists():
        return None

    with open(preds_file) as f:
        preds = json.load(f)

    country_records = sorted(
        [r for r in preds if r["country"] == country_iso3.upper()],
        key=lambda x: x["year"],
        reverse=True,
    )
    if not country_records:
        return None

    latest = country_records[0]
    explanation = get_crisis_shap_explanation(country_iso3, horizon)

    return {
        "country": country_iso3.upper(),
        "horizon": "1-Year Forward Window",
        "crisis_probability": latest["crisis_probability"],
        "crisis_probability_pct": latest["crisis_probability_pct"],
        "risk_tier": latest["risk_tier"], # Low, Moderate, High
        "evaluation_year": latest["year"],
        "forecast_window": f"{latest['year'] + 1}",
        "top_vulnerability_drivers": explanation.get("drivers", []) if explanation else [],
    }


def get_crisis_shap_explanation(country_iso3: str, horizon: str = "1y") -> Optional[Dict[str, Any]]:
    """
    Returns game-theoretic SHAP attributions explaining why the country
    is in its respective risk tier.
    """
    results_file = RESULTS_DIR / f"early_warning_{horizon}_results.json"
    if not results_file.exists():
        return None

    with open(results_file) as f:
        results = json.load(f)

    shap_dict = results.get("shap_importance", {})
    top4 = list(shap_dict.items())[:4]

    FEATURE_HUMAN_LABELS = {
        "ext_debt_pct": "External Debt Stock (% of GNI)",
        "reserves_months": "Foreign Exchange Reserve Coverage",
        "inflation": "Consumer Price Inflation Rate",
        "gdp_growth": "Real GDP Growth Momentum",
        "debt_to_reserves_ratio": "Debt-to-Reserve Stress Ratio",
        "delta_reserves_1y": "Annual Reserve Depletion Rate",
        "delta_debt_1y": "Annual Debt Accumulation Velocity",
        "current_account_pct": "Current Account Balance (% of GDP)",
        "reserve_depletion_shock": "Sudden Reserve Drain Shock",
        "inflation_surge_flag": "Accelerating Inflation Surge",
        "gni_pc_growth": "GNI Per Capita Growth",
    }

    drivers = [
        {
            "indicator": feat,
            "label": FEATURE_HUMAN_LABELS.get(feat, feat),
            "shap_importance": round(val, 4),
        }
        for feat, val in top4
    ]

    return {"country": country_iso3.upper(), "drivers": drivers}


def get_early_warning_model_card(horizon: str = "1y") -> Optional[Dict[str, Any]]:
    """
    Returns transparent audit card benchmarking XGBoost against Logistic Regression.
    """
    results_file = RESULTS_DIR / f"early_warning_{horizon}_results.json"
    if not results_file.exists():
        return None

    with open(results_file) as f:
        results = json.load(f)

    xgb = results.get("xgboost", {})
    logit = results.get("baseline_logistic", {})

    return {
        "system": "ATLAS Systemic Crisis Early Warning System (Module 1)",
        "prediction_target": "Systemic Crisis (Banking, Currency, or Sovereign Debt Default in t+1)",
        "ground_truth_source": "IMF Systemic Banking Crises Database (Laeven & Valencia 2020)",
        "train_period": "2000 - 2019",
        "test_period": "2020 - 2024 (Out-of-sample stress evaluation)",
        "models_evaluated": {
            "main_model": "XGBoost Classifier (Gradient-Boosted Trees)",
            "baseline_model": "Logistic Regression (L2 / Balanced, IMF standard)",
        },
        "performance_comparison": {
            "xgboost_roc_auc": xgb.get("roc_auc"),
            "baseline_roc_auc": logit.get("roc_auc"),
            "xgboost_pr_auc": xgb.get("pr_auc"),
            "baseline_pr_auc": logit.get("pr_auc"),
            "xgboost_recall": xgb.get("recall"),
            "xgboost_precision": xgb.get("precision"),
            "xgboost_f1": xgb.get("f1"),
            "xgboost_brier_score": xgb.get("brier_score"),
        },
        "class_balance_training": results.get("class_balance_train", {}),
        "explainability": "Game-theoretic SHAP attributions (Lundberg & Lee 2017)",
    }


def get_global_risk_rankings(horizon: str = "1y", limit: int = 50) -> List[Dict[str, Any]]:
    """
    Returns list of countries ranked from highest to lowest crisis risk.
    """
    preds_file = RESULTS_DIR / f"early_warning_{horizon}_predictions.json"
    if not preds_file.exists():
        return []

    with open(preds_file) as f:
        preds = json.load(f)

    # Get latest year available across countries
    max_yr = max(r["year"] for r in preds)
    latest_all = [r for r in preds if r["year"] == max_yr]
    ranked = sorted(latest_all, key=lambda x: x["crisis_probability"], reverse=True)

    return ranked[:limit]


if __name__ == "__main__":
    print("=== ATLAS Crisis Early Warning Inference ===\n")
    card = get_early_warning_model_card("1y")
    if card:
        print("Model Card:", json.dumps(card, indent=2))
