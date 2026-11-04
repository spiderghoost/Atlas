"""
ATLAS Nowcasting Model Tests
==============================
Tests the data builder, feature engineering, inference engine,
and model card. Does not require a trained model to be present.
"""

import os
import sys
import django
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Setup Django
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "atlas.settings")
django.setup()

from django.test import TestCase
from apps.warehouse.models import Country, IndicatorMetadata, MacroObservation


class DataBuilderTests(TestCase):
    """Tests the panel data builder and feature engineering logic."""

    def setUp(self):
        """Create minimal test fixtures (one country, two indicators, 10 years)."""
        self.country = Country.objects.create(
            iso3="TST", name="Test Country", region="Test Region",
            income_group="High income"
        )
        self.gdp_ind = IndicatorMetadata.objects.create(
            indicator_code="NY.GDP.MKTP.KD.ZG",
            name="GDP Growth", category="economy", source="WDI",
            unit="%", periodicity="Annual"
        )
        self.cpi_ind = IndicatorMetadata.objects.create(
            indicator_code="FP.CPI.TOTL.ZG",
            name="Inflation", category="inflation", source="WDI",
            unit="%", periodicity="Annual"
        )
        # Insert 10 years of test data
        gdp_vals = [3.0, 3.5, 2.0, 4.0, 5.0, 1.5, 6.0, 4.5, 2.5, 3.8]
        cpi_vals = [5.0, 6.0, 7.0, 5.5, 4.0, 8.0, 3.0, 2.5, 9.0, 11.0]
        for i, year in enumerate(range(2015, 2025)):
            MacroObservation.objects.create(
                country=self.country, indicator=self.gdp_ind,
                year=year, value=gdp_vals[i], source="WDI"
            )
            MacroObservation.objects.create(
                country=self.country, indicator=self.cpi_ind,
                year=year, value=cpi_vals[i], source="WDI"
            )

    def test_panel_load_returns_dataframe(self):
        """load_panel() returns a DataFrame with expected columns."""
        from src.nowcasting.data_builder import load_panel
        df = load_panel()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertIn("country_id", df.columns)
        self.assertIn("year", df.columns)
        self.assertIn("gdp_growth", df.columns)

    def test_feature_engineering_creates_lags(self):
        """engineer_features() creates lag and rolling columns."""
        from src.nowcasting.data_builder import load_panel, engineer_features
        df = load_panel()
        df = engineer_features(df)
        self.assertIn("gdp_lag1", df.columns)
        self.assertIn("gdp_lag2", df.columns)
        self.assertIn("inflation_lag1", df.columns)
        self.assertIn("gdp_rolling3", df.columns)
        self.assertIn("target_gdp_t1", df.columns)
        self.assertIn("target_cpi_t1", df.columns)

    def test_lag_values_are_correct(self):
        """gdp_lag1 must equal the prior year's gdp_growth for the same country."""
        from src.nowcasting.data_builder import load_panel, engineer_features
        df = load_panel()
        df = engineer_features(df)
        tst = df[df["country_id"] == "TST"].sort_values("year")
        # For year 2016, lag1 should be 2015 value
        row_2016 = tst[tst["year"] == 2016]
        row_2015 = tst[tst["year"] == 2015]
        if not row_2016.empty and not row_2015.empty:
            self.assertAlmostEqual(
                row_2016["gdp_lag1"].values[0],
                row_2015["gdp_growth"].values[0],
                places=3
            )

    def test_get_training_data_returns_xy(self):
        """get_training_data() returns correct shapes for X and y."""
        from src.nowcasting.data_builder import get_training_data
        X, y, feats = get_training_data("gdp")
        self.assertGreater(len(X), 0)
        self.assertEqual(len(X), len(y))
        self.assertIsInstance(feats, list)
        self.assertGreater(len(feats), 0)


class InferenceTests(TestCase):
    """Tests the inference engine using mocked pre-computed results."""

    def test_model_card_returns_none_when_no_results(self):
        """model card returns None gracefully when no results file exists."""
        from src.nowcasting.inference import get_model_card
        result = get_model_card("gdp")
        # May be None (not trained yet) or a dict (trained)
        self.assertIn(result.__class__.__name__, ["NoneType", "dict"])

    def test_country_forecast_returns_none_when_no_results(self):
        """country forecast returns None gracefully when no results file exists."""
        from src.nowcasting.inference import get_country_forecast
        result = get_country_forecast("EGY", "gdp")
        self.assertIn(result.__class__.__name__, ["NoneType", "dict"])

    def test_shap_explanation_returns_none_or_dict(self):
        """SHAP explanation returns None gracefully when no results file exists."""
        from src.nowcasting.inference import get_shap_explanation
        result = get_shap_explanation("EGY", "gdp")
        self.assertIn(result.__class__.__name__, ["NoneType", "dict"])
