from datetime import datetime, timezone
import email.utils
import feedparser
from typing import List, Dict, Any
from apps.realtime.models import NewsHeadline
from apps.realtime.services.relevance_gate import evaluate_relevance

RSS_FEEDS = [
    {"source": "BBC World", "url": "http://feeds.bbci.co.uk/news/world/rss.xml"},
    {"source": "BBC Business", "url": "http://feeds.bbci.co.uk/news/business/rss.xml"},
    {"source": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml"},
    {"source": "CNBC World", "url": "https://search.cnbc.com/rs/search/view.html?partnerId=2000&keywords=economy&sort=date&format=xml"},
]


def parse_pub_date(entry) -> datetime:
    """Safely extracts and parses publication date from feed entry."""
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    if hasattr(entry, 'published'):
        try:
            parsed = email.utils.parsedate_to_datetime(entry.published)
            return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except Exception:
            pass
    return datetime.now(timezone.utc)


def ingest_rss_feeds() -> Dict[str, Any]:
    """
    Ingests live RSS headlines, applies Stage 0 relevance gate,
    and deduplicates by URL before persisting to NewsHeadline table.
    """
    stats = {"total_processed": 0, "relevant_saved": 0, "filtered_saved": 0, "duplicates": 0}

    for feed_info in RSS_FEEDS:
        source_name = feed_info["source"]
        feed_url = feed_info["url"]
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                stats["total_processed"] += 1
                link = getattr(entry, 'link', None)
                title = getattr(entry, 'title', '').strip()
                summary = getattr(entry, 'summary', '').strip()

                if not link or not title:
                    continue

                if NewsHeadline.objects.filter(url=link).exists():
                    stats["duplicates"] += 1
                    continue

                pub_date = parse_pub_date(entry)
                is_rel, cluster = evaluate_relevance(title, summary)

                NewsHeadline.objects.create(
                    title=title,
                    source=source_name,
                    url=link,
                    published_at=pub_date,
                    topic_cluster=cluster,
                    is_relevant=is_rel,
                    embedding=[] # To be populated by Celery embedding job
                )

                if is_rel:
                    stats["relevant_saved"] += 1
                else:
                    stats["filtered_saved"] += 1

        except Exception as e:
            stats[f"error_{source_name}"] = str(e)

    return stats
