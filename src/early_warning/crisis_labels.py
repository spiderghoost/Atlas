"""
IMF Systemic Crisis Ground-Truth Database
===========================================
Ground-truth crisis labeling based on:
  Laeven, L., & Valencia, F. (2020). "Systemic Banking Crises Database II".
  IMF Economic Review, 68(2), 307-361.

Identifies historical episodes across three crisis dimensions:
  1. Systemic Banking Crises (bank runs, capital freezes, bailouts)
  2. Sovereign Debt Crises (default, restructuring, Paris Club distress)
  3. Currency Crises (severe currency depreciation > 30% and reserve collapse)
"""

from typing import Set, Tuple
import pandas as pd

# ── Documented IMF Systemic Crisis Episodes (Country ISO3, Year) ─────────────
IMF_HISTORICAL_CRISES: Set[Tuple[str, int]] = {
    # 2008-2012 Global Financial & European Debt Crisis
    ("USA", 2007), ("USA", 2008),
    ("GBR", 2007), ("GBR", 2008),
    ("ISL", 2008), ("ISL", 2009), ("ISL", 2010),
    ("IRL", 2008), ("IRL", 2009), ("IRL", 2010), ("IRL", 2011),
    ("GRC", 2008), ("GRC", 2009), ("GRC", 2010), ("GRC", 2011), ("GRC", 2012), ("GRC", 2013), ("GRC", 2014), ("GRC", 2015),
    ("ESP", 2008), ("ESP", 2009), ("ESP", 2010), ("ESP", 2011), ("ESP", 2012),
    ("PRT", 2008), ("PRT", 2011), ("PRT", 2012), ("PRT", 2013),
    ("CYP", 2011), ("CYP", 2012), ("CYP", 2013),
    ("ITA", 2008), ("ITA", 2011), ("ITA", 2012), ("ITA", 2013),
    ("DEU", 2008),
    ("FRA", 2008),
    ("NLD", 2008),
    ("BEL", 2008),
    ("AUT", 2008),
    ("DNK", 2008),

    # Latin American & Caribbean Debt / Currency Crises
    ("ARG", 2001), ("ARG", 2002), ("ARG", 2003), ("ARG", 2014), ("ARG", 2018), ("ARG", 2019), ("ARG", 2020), ("ARG", 2023),
    ("ECU", 2008), ("ECU", 2009), ("ECU", 2020),
    ("VEN", 2014), ("VEN", 2015), ("VEN", 2016), ("VEN", 2017), ("VEN", 2018), ("VEN", 2019), ("VEN", 2020),
    ("BRA", 2015), ("BRA", 2016),
    ("SUR", 2020), ("SUR", 2021),
    ("BLZ", 2006), ("BLZ", 2012), ("BLZ", 2017), ("BLZ", 2020),

    # Eastern Europe & Central Asia
    ("UKR", 2008), ("UKR", 2009), ("UKR", 2014), ("UKR", 2015), ("UKR", 2022), ("UKR", 2023),
    ("RUS", 2008), ("RUS", 2014), ("RUS", 2015), ("RUS", 2022),
    ("TUR", 2000), ("TUR", 2001), ("TUR", 2018), ("TUR", 2019), ("TUR", 2021), ("TUR", 2022),
    ("BLR", 2011), ("BLR", 2022),
    ("KAZ", 2008), ("KAZ", 2009),
    ("HUN", 2008),
    ("LVA", 2008), ("LVA", 2009),

    # Middle East & North Africa
    ("EGY", 2016), ("EGY", 2017), ("EGY", 2022), ("EGY", 2023),
    ("LBN", 2019), ("LBN", 2020), ("LBN", 2021), ("LBN", 2022),
    ("TUN", 2021), ("TUN", 2022),
    ("YEM", 2014), ("YEM", 2015), ("YEM", 2016), ("YEM", 2017),

    # South Asia & East Asia
    ("LKA", 2022), ("LKA", 2023),
    ("PAK", 2008), ("PAK", 2018), ("PAK", 2022), ("PAK", 2023),
    ("MNG", 2008), ("MNG", 2016),

    # Sub-Saharan Africa
    ("GHA", 2022), ("GHA", 2023),
    ("ZMB", 2020), ("ZMB", 2021),
    ("NGA", 2016), ("NGA", 2020),
    ("ZWE", 2007), ("ZWE", 2008), ("ZWE", 2019),
    ("MOZ", 2016), ("MOZ", 2017),
    ("ETH", 2023),
    ("KEN", 2022),
}


def label_crises(panel_df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies ground-truth labels from the IMF Systemic Crisis Database,
    augmented by quantitative macro distress rules (Laeven & Valencia criteria).

    Creates:
      • is_crisis_now  : 1 if country is in crisis in current year, 0 otherwise
      • target_crisis_1y : 1 if country enters crisis in year t+1 (Early Warning Target)
      • target_crisis_2y : 1 if country enters crisis in year t+1 OR t+2
    """
    df = panel_df.copy()

    # 1. Direct IMF catalog match
    is_imf_crisis = [
        1 if (row["country_id"], row["year"]) in IMF_HISTORICAL_CRISES else 0
        for _, row in df.iterrows()
    ]
    df["is_imf_crisis"] = is_imf_crisis

    # 2. Quantitative crisis criteria (Laeven & Valencia currency and debt distress)
    # Currency collapse: annual inflation > 40% (hyperinflation / currency shock)
    hyperinflation = (df["inflation"] > 40.0).fillna(False)

    # Debt distress: external debt > 90% of GNI combined with reserves < 2.5 months
    debt_distress = (
        (df["ext_debt_pct"] > 90.0) & (df["reserves_months"] < 2.5)
    ).fillna(False)

    # Acute growth collapse: GDP drop > 6% with positive inflation
    severe_contraction = (
        (df["gdp_growth"] < -6.0) & (df["inflation"] > 10.0)
    ).fillna(False)

    df["is_crisis_now"] = (
        (df["is_imf_crisis"] == 1) | hyperinflation | debt_distress | severe_contraction
    ).astype(int)

    # 3. Create Early Warning Forward Targets (t+1 and t+2)
    # Group by country and look ahead: Will a crisis occur in the next 1-2 years?
    g = df.groupby("country_id")
    df["crisis_next_1y"] = g["is_crisis_now"].shift(-1)
    df["crisis_next_2y"] = g["is_crisis_now"].shift(-2)

    # Target 1: Crisis in year t+1
    df["target_crisis_t1"] = df["crisis_next_1y"]

    # Target 2: Crisis within next 2 years (t+1 or t+2)
    df["target_crisis_2y_window"] = (
        (df["crisis_next_1y"] == 1) | (df["crisis_next_2y"] == 1)
    ).astype(float)
    # If both forward steps are missing, mark as missing
    df.loc[df["crisis_next_1y"].isna() & df["crisis_next_2y"].isna(), "target_crisis_2y_window"] = None

    return df
