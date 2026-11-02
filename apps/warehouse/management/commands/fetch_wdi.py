from django.core.management.base import BaseCommand
from apps.warehouse.etl import fetch_wdi_observations, CORE_INDICATORS

class Command(BaseCommand):
    help = "Fetches historical time-series observations from the World Bank WDI API."

    def add_arguments(self, parser):
        parser.add_argument('--indicator', type=str, default='NY.GDP.MKTP.KD.ZG', help="Indicator code (e.g. NY.GDP.MKTP.KD.ZG)")
        parser.add_argument('--all', action='store_true', help="Fetch all core indicators")
        parser.add_argument('--start', type=int, default=2000, help="Start year (default: 2000)")
        parser.add_argument('--end', type=int, default=2024, help="End year (default: 2024)")

    def handle(self, *args, **options):
        start_yr = options['start']
        end_yr = options['end']

        if options['all']:
            for item in CORE_INDICATORS:
                code = item["indicator_code"]
                self.stdout.write(f"Fetching {item['name']} ({code}) [{start_yr}-{end_yr}]...")
                try:
                    count = fetch_wdi_observations(code, start_year=start_yr, end_year=end_yr)
                    self.stdout.write(self.style.SUCCESS(f"Saved {count} observations for {code}."))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed to fetch {code}: {e}"))
        else:
            code = options['indicator']
            self.stdout.write(f"Fetching indicator {code} [{start_yr}-{end_yr}]...")
            try:
                count = fetch_wdi_observations(code, start_year=start_yr, end_year=end_yr)
                self.stdout.write(self.style.SUCCESS(f"Saved {count} observations for {code}."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to fetch {code}: {e}"))
