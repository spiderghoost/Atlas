"""
ATLAS Nowcasting Data Builder
==============================
Pulls data directly from the ATLAS database (MacroObservation table)
and shapes it into a clean panel dataset ready for model training.

Panel structure (one row per country-year):
  country_id | year | gdp_growth | inflation | gdp_lag1 | gdp_lag2 |
  inflation_lag1 | ext_debt_pct | reserves_months | current_account_pct |
  gdp_rolling3 | inflation_rolling3 | TARGET_gdp_t1 | TARGET_cpi_t1
"""

import os
import sys
import django
import numpy as np
import pandas as pd

# Setup Django (so we can query the database)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "atlas.settings")
django.setup()

from apps.warehouse.models import MacroObservation

# ── Indicator codes we will use ─────────────────────────────────────────────
INDICATORS = {
    "NY.GDP.MKTP.KD.ZG"  : "gdp_growth",
    "FP.CPI.TOTL.ZG"     : "inflation",
    "DT.DOD.DECT.GN.ZS"  : "ext_debt_pct",
    "FI.RES.TOTL.MO"     : "reserves_months",
    "BN.CAB.XOKA.GD.ZS"  : "current_account_pct",
    "NY.GNP.PCAP.KD.ZG"  : "gni_pc_growth",
}

MIN_YEAR = 2000
MAX_YEAR = 2024
MIN_ROWS_PER_COUNTRY = 8   # drop countries with fewer than 8 usable years


def load_panel() -> pd.DataFrame:
    """
    Query the database and return a wide panel DataFrame.
    One row = one country × one year.
    """
    records = (
        MacroObservation.objects
        .filter(indicator_id__in=list(INDICATORS.keys()),
                year__gte=MIN_YEAR, year__lte=MAX_YEAR)
        .values("country_id", "indicator_id", "year", "value")
    )

    # Long → Wide pivot
    df_long = pd.DataFrame.from_records(records)
    if df_long.empty:
        raise RuntimeError("No data found. Run: python manage.py fetch_wdi --all")

    df_long["col"] = df_long["indicator_id"].map(INDICATORS)
    df_wide = (
        df_long
        .pivot_table(index=["country_id", "year"], columns="col", values="value")
        .reset_index()
    )
    df_wide.columns.name = None
    return df_wide


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build lag features, rolling averages, and the two prediction targets.

    Features created:
      • gdp_lag1, gdp_lag2          – GDP growth 1 and 2 years ago
      • inflation_lag1               – CPI 1 year ago
      • gdp_rolling3                 – 3-year rolling average of GDP growth
      • inflation_rolling3           – 3-year rolling average of inflation
      • delta_gdp                    – year-on-year change in GDP growth

    Targets (what the model must predict):
      • target_gdp_t1                – GDP growth NEXT year  (regression)
      • target_cpi_t1                – Inflation NEXT year   (regression)
    """
    df = df.sort_values(["country_id", "year"]).copy()

    for col in ["gdp_growth", "inflation", "ext_debt_pct",
                "reserves_months", "current_account_pct", "gni_pc_growth"]:
        if col not in df.columns:
            df[col] = np.nan

    g = df.groupby("country_id")

    # Lags
    df["gdp_lag1"]       = g["gdp_growth"].shift(1)
    df["gdp_lag2"]       = g["gdp_growth"].shift(2)
    df["inflation_lag1"] = g["inflation"].shift(1)

    # Rolling 3-year means
    df["gdp_rolling3"]       = g["gdp_growth"].transform(lambda s: s.shift(1).rolling(3).mean())
    df["inflation_rolling3"] = g["inflation"].transform(lambda s: s.shift(1).rolling(3).mean())

    # Year-on-year delta
    df["delta_gdp"] = df["gdp_growth"] - df["gdp_lag1"]

    # Targets (shift backwards = look one year ahead)
    df["target_gdp_t1"] = g["gdp_growth"].shift(-1)
    df["target_cpi_t1"] = g["inflation"].shift(-1)

    return df


def get_training_data(target: str = "gdp") -> tuple[pd.DataFrame, pd.Series, list[str]]:
    """
    Returns (X, y, feature_names) ready for model training.

    target: "gdp"  → predict target_gdp_t1
            "cpi"  → predict target_cpi_t1
    """
    target_col = f"target_{target}_t1"
    feature_cols = [
        "gdp_growth", "gdp_lag1", "gdp_lag2",
        "inflation", "inflation_lag1",
        "gdp_rolling3", "inflation_rolling3", "delta_gdp",
        "ext_debt_pct", "reserves_months",
        "current_account_pct", "gni_pc_growth",
    ]

    df = load_panel()
    df = engineer_features(df)

    # Keep only rows where target exists
    df = df.dropna(subset=[target_col])

    # Require at least some features (drop if >50% features missing)
    df = df.dropna(subset=["gdp_growth", "gdp_lag1"])  # absolute minimum

    # Drop countries with very few rows
    min_rows = 5 if target == "cpi" else MIN_ROWS_PER_COUNTRY
    counts = df.groupby("country_id")[target_col].count()
    valid_countries = counts[counts >= min_rows].index
    df = df[df["country_id"].isin(valid_countries)].copy()

    # Only keep columns that actually exist
    available_features = [c for c in feature_cols if c in df.columns]

    X = df[available_features + ["country_id", "year"]].copy()
    y = df[target_col].copy()

    print(f"[DataBuilder] Panel shape: {df.shape}")
    print(f"[DataBuilder] Countries  : {df['country_id'].nunique()}")
    print(f"[DataBuilder] Year range : {df['year'].min()} - {df['year'].max()}")
    print(f"[DataBuilder] Features   : {available_features}")
    print(f"[DataBuilder] Target     : {target_col}  (n={len(y)})")

    return X, y, available_features


if __name__ == "__main__":
    X, y, feats = get_training_data("gdp")
    print(X.describe())
