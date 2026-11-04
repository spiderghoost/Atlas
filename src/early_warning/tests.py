"""
ATLAS Crisis Early Warning Unit Tests
======================================
Tests ground-truth labeling, feature engineering, and inference engine.
"""

import os
import sys
import django
import pandas as pd
from pathlib import Path
from unittest.mock import patch

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "atlas.settings")
django.setup()

from django.test import TestCase
from src.early_warning.crisis_labels import label_crises, IMF_HISTORICAL_CRISES
from src.early_warning.inference import get_early_warning_model_card, get_country_crisis_risk


class CrisisLabelTests(TestCase):
    def test_imf_crises_corpus_presence(self):
        """IMF crises database must contain documented sovereign distress episodes."""
        self.assertIn(("LKA", 2022), IMF_HISTORICAL_CRISES)
        self.assertIn(("ARG", 2001), IMF_HISTORICAL_CRISES)
        self.assertIn(("GRC", 2011), IMF_HISTORICAL_CRISES)
        self.assertIn(("EGY", 2016), IMF_HISTORICAL_CRISES)
        self.assertIn(("UKR", 2014), IMF_HISTORICAL_CRISES)

    def test_label_crises_identifies_imf_episode(self):
        """label_crises() must assign is_crisis_now=1 to documented IMF episodes."""
        dummy_df = pd.DataFrame([
            {"country_id": "LKA", "year": 2021, "inflation": 7.0, "ext_debt_pct": 80.0, "reserves_months": 3.0, "gdp_growth": 3.5},
            {"country_id": "LKA", "year": 2022, "inflation": 45.0, "ext_debt_pct": 110.0, "reserves_months": 1.2, "gdp_growth": -7.8},
            {"country_id": "LKA", "year": 2023, "inflation": 20.0, "ext_debt_pct": 105.0, "reserves_months": 2.0, "gdp_growth": -2.3},
        ])
        labeled = label_crises(dummy_df)
        self.assertEqual(labeled.loc[labeled["year"] == 2022, "is_crisis_now"].values[0], 1)
        # 2021 should have target_crisis_t1 = 1 (leads the 2022 crisis!)
        self.assertEqual(labeled.loc[labeled["year"] == 2021, "target_crisis_t1"].values[0], 1)

    def test_quantitative_distress_trigger(self):
        """Hyperinflation and extreme debt distress must trigger crisis flags."""
        dummy_df = pd.DataFrame([
            {"country_id": "XYZ", "year": 2018, "inflation": 65.0, "ext_debt_pct": 95.0, "reserves_months": 1.5, "gdp_growth": -8.0},
            {"country_id": "XYZ", "year": 2019, "inflation": 10.0, "ext_debt_pct": 40.0, "reserves_months": 5.0, "gdp_growth": 4.0},
        ])
        labeled = label_crises(dummy_df)
        self.assertEqual(labeled.loc[labeled["year"] == 2018, "is_crisis_now"].values[0], 1)
        self.assertEqual(labeled.loc[labeled["year"] == 2019, "is_crisis_now"].values[0], 0)


class EWSInferenceTests(TestCase):
    def test_model_card_graceful(self):
        """get_early_warning_model_card() returns None or valid dict."""
        card = get_early_warning_model_card("1y")
        self.assertIn(card.__class__.__name__, ["NoneType", "dict"])

    def test_country_risk_graceful(self):
        """get_country_crisis_risk() handles non-existent countries cleanly."""
        risk = get_country_crisis_risk("NON_EXISTENT_ISO", "1y")
        self.assertIsNone(risk)
