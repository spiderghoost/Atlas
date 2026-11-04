"""
ATLAS Nowcasting Inference Engine
====================================
Loads trained models and produces forecasts for any country on demand.
Called by the Django API endpoint: GET /api/nowcast/{country_iso3}
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR   = BASE_DIR / "results" / "nowcasting"


def get_country_forecast(country_iso3: str, target: str = "gdp") -> Optional[dict]:
    """
    Returns the latest model forecast for a given country.

    Args:
        country_iso3 : 3-letter ISO code (e.g. 'EGY', 'USA', 'KEN')
        target       : 'gdp' or 'cpi'

    Returns:
        dict with forecast, lower_90, upper_90 or None if not found.
    """
    forecasts_path = RESULTS_DIR / f"{target}_forecasts.json"
    if not forecasts_path.exists():
        return None

    with open(forecasts_path) as f:
        forecasts = json.load(f)

    # Find most recent forecast for this country
    country_fc = sorted(
        [r for r in forecasts if r["country"] == country_iso3.upper()],
        key=lambda x: x["year"],
        reverse=True
    )
    return country_fc[0] if country_fc else None


def get_shap_explanation(country_iso3: str, target: str = "gdp") -> Optional[dict]:
    """
    Returns SHAP-based plain-language explanation of the drivers.
    """
    results_path = RESULTS_DIR / f"{target}_nowcasting_results.json"
    if not results_path.exists():
        return None

    with open(results_path) as f:
        results = json.load(f)

    shap = results.get("shap_importance", {})
    top3 = list(shap.items())[:3]

    FEATURE_LABELS = {
        "gdp_growth"         : "current GDP growth",
        "gdp_lag1"           : "last year's GDP growth",
        "gdp_lag2"           : "GDP growth 2 years ago",
        "inflation"          : "current inflation rate",
        "inflation_lag1"     : "last year's inflation",
        "gdp_rolling3"       : "3-year GDP growth trend",
        "inflation_rolling3" : "3-year inflation trend",
        "delta_gdp"          : "change in GDP momentum",
        "ext_debt_pct"       : "external debt level",
        "reserves_months"    : "import reserve coverage",
        "current_account_pct": "current account balance",
        "gni_pc_growth"      : "income per capita growth",
    }

    drivers = [
        {"feature": feat, "label": FEATURE_LABELS.get(feat, feat), "importance": round(imp, 4)}
        for feat, imp in top3
    ]

    return {"target": target, "country": country_iso3, "top_drivers": drivers}


def get_model_card(target: str = "gdp") -> Optional[dict]:
    """
    Returns a summary of the model's performance metrics (the 'model card').
    Shown on the ATLAS platform so users know how trustworthy the prediction is.
    """
    results_path = RESULTS_DIR / f"{target}_nowcasting_results.json"
    if not results_path.exists():
        return None

    with open(results_path) as f:
        results = json.load(f)

    target_label = "GDP Growth (%)" if target == "gdp" else "Inflation (%)"
    baseline = results.get("baseline_ridge", {})
    lgbm     = results.get("lightgbm", {})
    conf     = results.get("conformal", {})

    return {
        "target"           : target_label,
        "train_period"     : "2000 – 2019",
        "test_period"      : "2020 – 2024",
        "main_model"       : "LightGBM (gradient boosted trees)",
        "baseline_model"   : "Ridge Regression",
        "lightgbm_mae_pp"  : lgbm.get("mae"),
        "lightgbm_rmse_pp" : lgbm.get("rmse"),
        "lightgbm_r2"      : lgbm.get("r2"),
        "baseline_mae_pp"  : baseline.get("mae"),
        "baseline_r2"      : baseline.get("r2"),
        "conformal_coverage": conf.get("coverage_90pct"),
        "conformal_width_pp": conf.get("avg_interval_width_pp"),
        "note": (
            "Prediction intervals represent a 90% confidence range. "
            "All numbers come from validated ML models, never from the AI agent."
        )
    }


if __name__ == "__main__":
    print("=== ATLAS Nowcasting Inference ===\n")
    for iso3 in ["EGY", "USA", "KEN", "GHA", "IND"]:
        fc = get_country_forecast(iso3, "gdp")
        if fc:
            print(f"  {iso3}: GDP {fc['forecast']:+.2f}% [{fc['lower_90']:+.2f}%, {fc['upper_90']:+.2f}%]")
        else:
            print(f"  {iso3}: No forecast available — run train.py first")

    print()
    mc = get_model_card("gdp")
    if mc:
        print("=== GDP Model Card ===")
        for k, v in mc.items():
            print(f"  {k}: {v}")
