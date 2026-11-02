from django.core.management.base import BaseCommand
from apps.warehouse.etl import seed_indicators, fetch_and_seed_countries

class Command(BaseCommand):
    help = "Seeds core Indicator Metadata catalog and fetches global sovereign country list from World Bank API."

    def handle(self, *args, **options):
        self.stdout.write("1. Seeding core macroeconomic indicator metadata...")
        ind_count = seed_indicators()
        self.stdout.write(self.style.SUCCESS(f"Successfully seeded/updated {ind_count} core indicators."))

        self.stdout.write("2. Fetching sovereign countries from World Bank API...")
        try:
            c_count = fetch_and_seed_countries()
            self.stdout.write(self.style.SUCCESS(f"Successfully seeded/updated {c_count} sovereign countries."))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"World Bank API fetch encountered error: {e}. Falling back to default country list."))
            from apps.warehouse.models import Country
            default_countries = [
                ("USA", "US", "United States", "North America", "High income", "Washington, D.C.", 38.8951, -77.0364),
                ("EGY", "EG", "Egypt, Arab Rep.", "Middle East & North Africa", "Lower middle income", "Cairo", 30.0444, 31.2357),
                ("GBR", "GB", "United Kingdom", "Europe & Central Asia", "High income", "London", 51.5074, -0.1278),
                ("DEU", "DE", "Germany", "Europe & Central Asia", "High income", "Berlin", 52.5200, 13.4050),
                ("CHN", "CN", "China", "East Asia & Pacific", "Upper middle income", "Beijing", 39.9042, 116.4074),
                ("JPN", "JP", "Japan", "East Asia & Pacific", "High income", "Tokyo", 35.6762, 139.6503),
                ("KEN", "KE", "Kenya", "Sub-Saharan Africa", "Lower middle income", "Nairobi", -1.2921, 36.8219),
                ("UKR", "UA", "Ukraine", "Europe & Central Asia", "Lower middle income", "Kyiv", 50.4501, 30.5234),
                ("LKA", "LK", "Sri Lanka", "South Asia", "Lower middle income", "Colombo", 6.9271, 79.8612),
                ("GHA", "GH", "Ghana", "Sub-Saharan Africa", "Lower middle income", "Accra", 5.6037, -0.1870),
            ]
            for iso3, iso2, name, reg, inc, cap, lat, lon in default_countries:
                Country.objects.update_or_create(
                    iso3=iso3,
                    defaults={
                        "iso2": iso2, "name": name, "region": reg,
                        "income_group": inc, "capital": cap,
                        "latitude": lat, "longitude": lon
                    }
                )
            self.stdout.write(self.style.SUCCESS(f"Seeded {len(default_countries)} baseline countries."))
