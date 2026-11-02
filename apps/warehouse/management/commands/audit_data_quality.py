from django.core.management.base import BaseCommand
from apps.warehouse.quality import run_data_quality_audit

class Command(BaseCommand):
    help = "Runs data quality, completeness, and anomaly health checks on macro observations."

    def add_arguments(self, parser):
        parser.add_argument('--indicator', type=str, default=None, help="Filter audit to a specific indicator")
        parser.add_argument('--start', type=int, default=2000, help="Audit start year")
        parser.add_argument('--end', type=int, default=2024, help="Audit end year")

    def handle(self, *args, **options):
        self.stdout.write("Running data quality health audit across data warehouse...")
        results = run_data_quality_audit(
            indicator_code=options['indicator'],
            window_start=options['start'],
            window_end=options['end']
        )
        self.stdout.write(self.style.SUCCESS(
            f"Quality Audit Completed: {results['audited_series']} series evaluated, "
            f"{results['stale_series']} stale series identified, "
            f"{results['anomalies_detected']} rate-of-change anomalies flagged."
        ))
