from django.test import TestCase
from apps.warehouse.models import Country, IndicatorMetadata, MacroObservation, DataQualityAudit
from apps.warehouse.etl import seed_indicators
from apps.warehouse.quality import run_data_quality_audit


class WarehouseModelTests(TestCase):
    def setUp(self):
        self.country = Country.objects.create(
            iso3="USA",
            iso2="US",
            name="United States",
            region="North America",
            income_group="High income"
        )
        self.indicator = IndicatorMetadata.objects.create(
            indicator_code="NY.GDP.MKTP.KD.ZG",
            name="GDP Growth (Annual %)",
            category="economy",
            source="WDI",
            unit="%",
            periodicity="Annual"
        )

    def test_macro_observation_creation(self):
        obs = MacroObservation.objects.create(
            country=self.country,
            indicator=self.indicator,
            year=2023,
            value=2.5,
            source="WDI"
        )
        self.assertEqual(obs.country.iso3, "USA")
        self.assertEqual(obs.indicator.indicator_code, "NY.GDP.MKTP.KD.ZG")
        self.assertEqual(obs.value, 2.5)

    def test_indicator_seeding(self):
        count = seed_indicators()
        self.assertGreaterEqual(count, 1)
        self.assertTrue(IndicatorMetadata.objects.filter(indicator_code="FP.CPI.TOTL.ZG").exists())

    def test_quality_audit_calculation(self):
        # Create a time series for audit test
        for yr, val in [(2020, 1.2), (2021, 2.3), (2022, 2.8), (2023, 2.5), (2024, 2.1)]:
            MacroObservation.objects.create(
                country=self.country,
                indicator=self.indicator,
                year=yr,
                value=val
            )
        stats = run_data_quality_audit(indicator_code=self.indicator.indicator_code, window_start=2020, window_end=2024)
        self.assertEqual(stats["audited_series"], 1)
        audit = DataQualityAudit.objects.get(country=self.country, indicator=self.indicator)
        self.assertEqual(audit.missing_fraction, 0.0)
        self.assertEqual(audit.last_observed_year, 2024)
