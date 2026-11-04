"""
ATLAS Crisis Early Warning Data Builder
========================================
Builds the feature matrix and ground-truth early warning targets
for systemic economic crisis prediction (banking, currency, and debt crises).

Target:
  target_crisis_t1 : 1 if country enters or experiences a crisis in year t+1
"""

import os
import sys
import django
import numpy as np
import pandas as pd
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "atlas.settings")
django.setup()

from apps.warehouse.models import MacroObservation
from src.early_warning.crisis_labels import label_crises

INDICATORS = {
    "NY.GDP.MKTP.KD.ZG": "gdp_growth",
    "FP.CPI.TOTL.ZG": "inflation",
    "DT.DOD.DECT.GN.ZS": "ext_debt_pct",
    "FI.RES.TOTL.MO": "reserves_months",
    "BN.CAB.XOKA.GD.ZS": "current_account_pct",
    "NY.GNP.PCAP.KD.ZG": "gni_pc_growth",
}

MIN_YEAR = 2000
MAX_YEAR = 2024
MIN_ROWS_PER_COUNTRY = 6


def load_early_warning_panel() -> pd.DataFrame:
    """Queries MacroObservation and shapes into wide country-year panel."""
    records = (
        MacroObservation.objects
        .filter(indicator_id__in=list(INDICATORS.keys()),
                year__gte=MIN_YEAR, year__lte=MAX_YEAR)
        .values("country_id", "indicator_id", "year", "value")
    )

    df_long = pd.DataFrame.from_records(records)
    if df_long.empty:
        raise RuntimeError("No macroeconomic data found in database.")

    df_long["col"] = df_long["indicator_id"].map(INDICATORS)
    df_wide = (
        df_long
        .pivot_table(index=["country_id", "year"], columns="col", values="value")
        .reset_index()
    )
    df_wide.columns.name = None
    return df_wide


def engineer_early_warning_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Constructs leading crisis vulnerability indicators:
      • Lags & moving averages (trend analysis)
      • Velocity features (reserve drain, debt build-up rate)
      • Compound vulnerability ratios (debt-to-reserves, twin deficit proxy)
    """
    df = df.sort_values(["country_id", "year"]).copy()

    for col in ["gdp_growth", "inflation", "ext_debt_pct",
                "reserves_months", "current_account_pct", "gni_pc_growth"]:
        if col not in df.columns:
            df[col] = np.nan

    g = df.groupby("country_id")

    # 1. Lags
    df["gdp_lag1"] = g["gdp_growth"].shift(1)
    df["gdp_lag2"] = g["gdp_growth"].shift(2)
    df["inflation_lag1"] = g["inflation"].shift(1)
    df["debt_lag1"] = g["ext_debt_pct"].shift(1)
    df["reserves_lag1"] = g["reserves_months"].shift(1)
    df["ca_lag1"] = g["current_account_pct"].shift(1)

    # 2. Velocity / Momentum features (speed of deterioration)
    df["delta_reserves_1y"] = df["reserves_months"] - df["reserves_lag1"]
    df["delta_debt_1y"] = df["ext_debt_pct"] - df["debt_lag1"]
    df["delta_inflation_1y"] = df["inflation"] - df["inflation_lag1"]
    df["delta_gdp_1y"] = df["gdp_growth"] - df["gdp_lag1"]

    # 3. Compound Vulnerability Ratios
    # High debt combined with thin foreign exchange reserves
    df["debt_to_reserves_ratio"] = df["ext_debt_pct"] / (df["reserves_months"].clip(lower=0.5))

    # Reserve drain shock flag: reserves dropped by more than 2 months of imports
    df["reserve_depletion_shock"] = (df["delta_reserves_1y"] < -1.5).astype(float)

    # Inflation surge flag: inflation doubled from prior year
    df["inflation_surge_flag"] = (
        (df["inflation"] > 15.0) & (df["delta_inflation_1y"] > 5.0)
    ).astype(float)

    # 4. Apply IMF Ground-Truth Crisis Labels
    df = label_crises(df)

    return df


def get_early_warning_data(horizon: str = "1y") -> tuple[pd.DataFrame, pd.Series, list[str]]:
    """
    Prepares training matrices for crisis early warning.

    horizon:
      "1y" -> predicts crisis in year t+1 (target_crisis_t1)
      "2y" -> predicts crisis in next 2 years (target_crisis_2y_window)
    """
    target_col = "target_crisis_t1" if horizon == "1y" else "target_crisis_2y_window"

    feature_cols = [
        "ext_debt_pct",
        "reserves_months",
        "inflation",
        "gdp_growth",
        "current_account_pct",
        "gni_pc_growth",
        "debt_to_reserves_ratio",
        "delta_reserves_1y",
        "delta_debt_1y",
        "delta_inflation_1y",
        "delta_gdp_1y",
        "reserve_depletion_shock",
        "inflation_surge_flag",
        "gdp_lag1",
        "inflation_lag1",
    ]

    df = load_early_warning_panel()
    df = engineer_early_warning_features(df)

    # Filter rows with valid targets
    df = df.dropna(subset=[target_col])

    # Keep countries with adequate records
    counts = df.groupby("country_id")[target_col].count()
    valid_countries = counts[counts >= MIN_ROWS_PER_COUNTRY].index
    df = df[df["country_id"].isin(valid_countries)].copy()

    available_features = [c for c in feature_cols if c in df.columns]

    X = df[available_features + ["country_id", "year"]].copy()
    y = df[target_col].astype(int)

    crisis_count = int(y.sum())
    total_count = len(y)
    crisis_pct = (crisis_count / total_count) * 100

    print(f"[EWS DataBuilder] Panel shape : {df.shape}")
    print(f"[EWS DataBuilder] Countries   : {df['country_id'].nunique()}")
    print(f"[EWS DataBuilder] Year range  : {int(df['year'].min())} - {int(df['year'].max())}")
    print(f"[EWS DataBuilder] Features    : {len(available_features)} predictors")
    print(f"[EWS DataBuilder] Class Dist  : {total_count - crisis_count} Normal | {crisis_count} Crisis ({crisis_pct:.1f}% positive)")

    return X, y, available_features


if __name__ == "__main__":
    X, y, feats = get_early_warning_data("1y")
    print("Class distribution:\n", y.value_counts())
