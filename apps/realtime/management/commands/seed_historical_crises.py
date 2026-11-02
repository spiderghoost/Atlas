from django.core.management.base import BaseCommand
from apps.realtime.models import HistoricalCrisis
from apps.realtime.services.crises_corpus import HISTORICAL_CRISES_DATA

class Command(BaseCommand):
    help = "Seeds curated historical crisis corpus for RAG analog grounding (§16)."

    def handle(self, *args, **options):
        self.stdout.write("Seeding curated historical crises corpus into database...")
        created_count = 0
        updated_count = 0

        for item in HISTORICAL_CRISES_DATA:
            obj, created = HistoricalCrisis.objects.update_or_create(
                crisis_id=item["crisis_id"],
                defaults={
                    "name": item["name"],
                    "year": item["year"],
                    "region": item["region"],
                    "crisis_types": item["crisis_types"],
                    "summary": item["summary"],
                    "what_happened": item["what_happened"],
                    "transmission_channels": item["transmission_channels"],
                    "real_world_outcomes": item["real_world_outcomes"],
                    "embedding": [] # Ready for pgvector 384-d embeddings
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Historical Crises Seed Finished: {created_count} added, {updated_count} updated. Total active: {HistoricalCrisis.objects.count()}"
        ))
