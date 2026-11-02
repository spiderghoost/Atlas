from django.test import TestCase, Client
from apps.realtime.models import NewsHeadline, CommodityLivePrice, WeatherObservation, HistoricalCrisis
from apps.realtime.services.relevance_gate import evaluate_relevance
from apps.realtime.services.crises_corpus import HISTORICAL_CRISES_DATA


class RealtimeTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_relevance_gate_positive(self):
        is_rel, cluster = evaluate_relevance(
            title="Central Bank raises interest rates by 50bps to combat soaring inflation",
            summary="Monetary policy tightening expected to dampen GDP growth."
        )
        self.assertTrue(is_rel)
        self.assertEqual(cluster, "Macroeconomic & Financial")

    def test_relevance_gate_food_cluster(self):
        is_rel, cluster = evaluate_relevance(
            title="Drought severely damages national wheat and grain harvest",
            summary="Emergency food reserves tapped as prices climb."
        )
        self.assertTrue(is_rel)
        self.assertEqual(cluster, "Food Security & Agriculture")

    def test_relevance_gate_negative(self):
        is_rel, cluster = evaluate_relevance(
            title="Local celebrity wins tennis tournament championship",
            summary="Fans celebrate across the stadium after three-set victory."
        )
        self.assertFalse(is_rel)
        self.assertEqual(cluster, "Unrelated")

    def test_historical_crises_corpus_integrity(self):
        self.assertGreaterEqual(len(HISTORICAL_CRISES_DATA), 5)
        ukr = next((c for c in HISTORICAL_CRISES_DATA if c["crisis_id"] == "ukraine-grain-2022"), None)
        self.assertIsNotNone(ukr)
        self.assertEqual(ukr["year"], 2022)
        self.assertIn("food_security", ukr["crisis_types"])

    def test_api_health_endpoint(self):
        resp = self.client.get('/api/health')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")

    def test_household_basket_optimizer_api(self):
        payload = {
            "city": "Cairo",
            "monthly_salary": 2000.0,
            "currency": "USD",
            "monthly_rent": 500.0,
            "family_size": 4,
            "dietary_constraints": ["halal"]
        }
        resp = self.client.post(
            '/api/personal/basket/optimize',
            data=payload,
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["disposable_income"], 1500.0)
        self.assertGreater(len(data["items"]), 3)
        # Verify action badges are present
        badges = [item["action_badge"] for item in data["items"]]
        self.assertIn("PRE-EMPT", badges)
        self.assertIn("SUBSTITUTE", badges)

    def test_wealth_guard_api(self):
        payload = {
            "city": "London",
            "monthly_salary": 4000.0,
            "currency": "GBP",
            "monthly_rent": 1500.0,
            "family_size": 2,
            "dietary_constraints": []
        }
        resp = self.client.post(
            '/api/personal/wealth/allocate',
            data=payload,
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["liquid_currency_buffer_pct"], 0.50)
        self.assertEqual(data["gold_pct"], 0.25)
        self.assertEqual(data["bulk_buying_buffer_pct"], 0.25)
