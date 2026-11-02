from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class NewsHeadline(models.Model):
    """Real-time geopolitical & macro news headlines with relevance filter and vector embeddings."""
    title = models.CharField(max_length=500)
    source = models.CharField(max_length=100, db_index=True, help_text="News outlet (Reuters, BBC, Al Jazeera, etc.)")
    url = models.URLField(max_length=1000, unique=True)
    location = models.CharField(max_length=150, blank=True, help_text="Inferred target or origin country/city")
    published_at = models.DateTimeField(db_index=True)
    topic_cluster = models.CharField(max_length=100, blank=True, help_text="PESTLE/Topic classification")
    is_relevant = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Stage 0 relevance gate: True if relevant to macro/geopolitical impact"
    )
    embedding = models.JSONField(
        default=list,
        blank=True,
        help_text="384-dimensional sentence-transformers embedding vector"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "News Headlines"
        ordering = ['-published_at']
        indexes = [
            models.Index(fields=['is_relevant', '-published_at']),
        ]

    def __str__(self):
        status = "[RELEVANT]" if self.is_relevant else "[FILTERED]"
        return f"{status} {self.source}: {self.title[:80]}"


class CommodityLivePrice(models.Model):
    """High-frequency (5-min) ticker observations for key macro commodities and FX pairs."""
    symbol = models.CharField(max_length=50, db_index=True, help_text="Ticker symbol (e.g. GC=F, BZ=F, USD/EGP)")
    name = models.CharField(max_length=100, help_text="Asset description (e.g. Gold Spot, Brent Crude Oil)")
    price = models.FloatField()
    currency = models.CharField(max_length=10, default='USD')
    change_24h_pct = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(db_index=True)

    class Meta:
        verbose_name_plural = "Commodity Live Prices"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['symbol', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.symbol} @ {self.price} {self.currency} ({self.timestamp:%Y-%m-%d %H:%M})"


class WeatherObservation(models.Model):
    """City-level weather conditions on 30-min cadence (7-day rolling window)."""
    city = models.CharField(max_length=100, db_index=True)
    country_code = models.CharField(max_length=3, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    temperature_c = models.FloatField()
    precipitation_mm = models.FloatField(default=0.0)
    wind_speed_kmh = models.FloatField(default=0.0)
    weather_code = models.IntegerField(default=0, help_text="WMO weather interpretation code")
    timestamp = models.DateTimeField(db_index=True)

    class Meta:
        verbose_name_plural = "Weather Observations"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['city', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.city}: {self.temperature_c}°C, precip={self.precipitation_mm}mm ({self.timestamp:%Y-%m-%d %H:%M})"


class HistoricalCrisis(models.Model):
    """Curated grounding corpus of historical economic shocks for RAG analog retrieval."""
    crisis_id = models.CharField(max_length=100, primary_key=True, help_text="Canonical ID (e.g. ukraine-grain-2022)")
    name = models.CharField(max_length=200)
    year = models.PositiveIntegerField()
    region = models.CharField(max_length=100)
    crisis_types = models.JSONField(default=list, help_text="List of categories (debt, currency, food, energy, etc.)")
    summary = models.TextField()
    what_happened = models.TextField(help_text="Detailed factual account of transmission and consequences")
    transmission_channels = models.JSONField(default=list, help_text="Identified transmission pathways (trade, FX, commodity)")
    real_world_outcomes = models.JSONField(default=dict, help_text="Documented empirical shocks to prices, inflation, GDP")
    embedding = models.JSONField(
        default=list,
        blank=True,
        help_text="384-dimensional vector for cosine similarity retrieval"
    )

    class Meta:
        verbose_name_plural = "Historical Crises"
        ordering = ['-year', 'name']

    def __str__(self):
        return f"{self.name} ({self.year}) [{self.crisis_id}]"


class AnalysisCache(models.Model):
    """Caches the 6-stage PocketRipple multi-agent analysis output per headline."""
    STATUS_CHOICES = [
        ('PENDING', 'Pending Stage 1'),
        ('PROCESSING', 'Processing Agent Cascade'),
        ('COMPLETED', 'Fully Validated & Completed'),
        ('REJECTED', 'Failed Sanity Validators'),
        ('FAILED', 'Execution Error'),
    ]

    headline = models.OneToOneField(NewsHeadline, on_delete=models.CASCADE, related_name='analysis')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    
    # 6-Stage Analysis Payload (§16)
    stage_1_trigger = models.JSONField(null=True, blank=True, help_text="PESTLE, scope, tempo")
    stage_2_actors = models.JSONField(null=True, blank=True, help_text="Actors and asymmetry analysis")
    stage_3_transmission = models.JSONField(null=True, blank=True, help_text="Trade, finance, commodity, confidence channels")
    stage_4_impact_matrix = models.JSONField(null=True, blank=True, help_text="Impact severity matrix across sectors")
    stage_5_cascade = models.JSONField(null=True, blank=True, help_text="Cascading effects + Weird Test evaluation")
    stage_6_pocketbook = models.JSONField(
        null=True, 
        blank=True, 
        help_text="Global pocketbook & household action plan (PRE-EMPT, SUBSTITUTE, ADAPT, PROTECT, ADVOCATE)"
    )
    
    historical_matches = models.JSONField(
        default=list, 
        blank=True, 
        help_text="Top-3 retrieved historical crises with similarity scores"
    )
    model_used = models.CharField(max_length=100, blank=True)
    pipeline_version = models.CharField(max_length=20, default='1.0.0')
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Analysis Caches"
        ordering = ['-updated_at']

    def __str__(self):
        return f"Analysis [{self.status}] for Headline #{self.headline_id}"


class UserHousehold(models.Model):
    """User household profile for dynamic, on-the-fly monthly basket and allocation calculation."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='households')
    city = models.CharField(max_length=100, help_text="Target city for local price and inflation adjustments")
    monthly_salary = models.FloatField(help_text="Net monthly household income")
    currency = models.CharField(max_length=10, default='USD')
    monthly_rent = models.FloatField(default=0.0)
    family_size = models.PositiveIntegerField(default=1)
    dietary_constraints = models.JSONField(default=list, blank=True, help_text="List of dietary tags (vegetarian, halal, etc.)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Household in {self.city} (Income: {self.monthly_salary} {self.currency}, Size: {self.family_size})"
