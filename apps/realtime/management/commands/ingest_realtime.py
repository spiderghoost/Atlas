from django.core.management.base import BaseCommand
from apps.realtime.services.rss_ingest import ingest_rss_feeds
from apps.realtime.services.market_ingest import ingest_commodity_prices
from apps.realtime.services.weather_ingest import ingest_city_weather

class Command(BaseCommand):
    help = "Executes the 24/7 real-time ingestion cycle (RSS news, commodity prices, and city weather)."

    def add_arguments(self, parser):
        parser.add_argument('--feed-only', action='store_true', help="Only ingest RSS headlines")
        parser.add_argument('--price-only', action='store_true', help="Only ingest commodity and FX prices")
        parser.add_argument('--weather-only', action='store_true', help="Only ingest city weather")

    def handle(self, *args, **options):
        run_all = not (options.get('feed_only') or options.get('price_only') or options.get('weather_only'))

        if run_all or options.get('feed_only'):
            self.stdout.write("1. Polling RSS news feeds and applying Stage 0 relevance gate...")
            rss_stats = ingest_rss_feeds()
            self.stdout.write(self.style.SUCCESS(
                f"   RSS Ingest: {rss_stats.get('total_processed', 0)} processed, "
                f"{rss_stats.get('relevant_saved', 0)} relevant saved, "
                f"{rss_stats.get('filtered_saved', 0)} filtered saved, "
                f"{rss_stats.get('duplicates', 0)} duplicates skipped."
            ))

        if run_all or options.get('price_only'):
            self.stdout.write("2. Polling benchmark commodities and FX market rates...")
            price_stats = ingest_commodity_prices()
            self.stdout.write(self.style.SUCCESS(
                f"   Market Ingest: {price_stats.get('success', 0)} ticker quotes updated, "
                f"{price_stats.get('failed', 0)} failed."
            ))

        if run_all or options.get('weather_only'):
            self.stdout.write("3. Polling regional city weather conditions...")
            weather_stats = ingest_city_weather()
            self.stdout.write(self.style.SUCCESS(
                f"   Weather Ingest: {weather_stats.get('success', 0)} cities updated, "
                f"{weather_stats.get('failed', 0)} failed."
            ))
