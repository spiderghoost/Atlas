from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Country(models.Model):
    """Reference table of sovereign countries and regional aggregates."""
    iso3 = models.CharField(max_length=3, primary_key=True, help_text="ISO 3166-1 alpha-3 code (e.g. USA, EGY)")
    iso2 = models.CharField(max_length=2, blank=True, help_text="ISO 3166-1 alpha-2 code")
    name = models.CharField(max_length=150, help_text="Official country or territory name")
    region = models.CharField(max_length=100, db_index=True, blank=True, help_text="World Bank geographic region")
    income_group = models.CharField(max_length=50, db_index=True, blank=True, help_text="World Bank income classification")
    capital = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Countries"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.iso3})"


class IndicatorMetadata(models.Model):
    """Master catalog of macroeconomic and development indicators."""
    CATEGORY_CHOICES = [
        ('economy', 'Economy & Growth'),
        ('debt', 'Debt & Fiscal'),
        ('trade', 'Trade & Balance of Payments'),
        ('inflation', 'Prices & Inflation'),
        ('food_energy', 'Food & Energy Security'),
        ('social', 'Poverty & Social Indicators'),
        ('governance', 'Governance & Institutions'),
        ('climate', 'Climate & Environment'),
    ]

    indicator_code = models.CharField(max_length=100, primary_key=True, help_text="Unique indicator code (e.g. NY.GDP.MKTP.KD.ZG)")
    name = models.CharField(max_length=255, help_text="Human-readable indicator title")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, db_index=True)
    source = models.CharField(max_length=50, default='WDI', db_index=True, help_text="Data provider (WDI, IMF, FAO, FRED)")
    unit = models.CharField(max_length=50, blank=True, help_text="Unit of measurement (% of GDP, USD, Index)")
    periodicity = models.CharField(max_length=50, default='Annual')
    description = models.TextField(blank=True)
    quality_score = models.FloatField(default=1.0, help_text="Composite data quality/reliability score (0.0 to 1.0)")

    class Meta:
        verbose_name_plural = "Indicator Metadata"
        ordering = ["category", "name"]

    def __str__(self):
        return f"{self.name} [{self.indicator_code}]"


class MacroObservation(models.Model):
    """Core analytical time series data warehouse table."""
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='observations')
    indicator = models.ForeignKey(IndicatorMetadata, on_delete=models.CASCADE, related_name='observations')
    year = models.PositiveIntegerField(db_index=True)
    value = models.FloatField(null=True, blank=True)
    source = models.CharField(max_length=50, default='WDI')
    is_imputed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Macro Observations"
        constraints = [
            models.UniqueConstraint(fields=['country', 'indicator', 'year'], name='unique_country_indicator_year')
        ]
        indexes = [
            models.Index(fields=['country', 'year']),
            models.Index(fields=['indicator', 'year']),
            models.Index(fields=['indicator', 'country']),
        ]
        ordering = ['-year', 'country']

    def __str__(self):
        return f"{self.country_id} - {self.indicator_id} ({self.year}): {self.value}"


class DataQualityAudit(models.Model):
    """Audit metric recording missingness, staleness, and anomalies per country-indicator series."""
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='quality_audits')
    indicator = models.ForeignKey(IndicatorMetadata, on_delete=models.CASCADE, related_name='quality_audits')
    missing_fraction = models.FloatField(default=0.0, help_text="Fraction of missing years in the audited range")
    last_observed_year = models.PositiveIntegerField(null=True, blank=True)
    staleness_score = models.FloatField(default=0.0, help_text="Years elapsed since last observation")
    is_anomaly_detected = models.BooleanField(default=False)
    anomaly_details = models.JSONField(default=dict, blank=True)
    last_audited_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['country', 'indicator'], name='unique_country_indicator_audit')
        ]

    def __str__(self):
        return f"Audit {self.country_id} / {self.indicator_id}: missing={self.missing_fraction:.1%}, staleness={self.staleness_score}"


class Watchlist(models.Model):
    """Saved portfolio of countries monitored by an organization or user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlists', null=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    countries = models.ManyToManyField(Country, related_name='watchlists')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class AlertRule(models.Model):
    """User-defined macroeconomic and risk threshold trigger."""
    OPERATOR_CHOICES = [
        ('GT', '> Greater than'),
        ('GTE', '>= Greater or equal'),
        ('LT', '< Less than'),
        ('LTE', '<= Less or equal'),
    ]

    watchlist = models.ForeignKey(Watchlist, on_delete=models.CASCADE, null=True, blank=True, related_name='alerts')
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True, blank=True, related_name='alerts')
    indicator = models.ForeignKey(IndicatorMetadata, on_delete=models.CASCADE, related_name='alerts')
    operator = models.CharField(max_length=5, choices=OPERATOR_CHOICES, default='GT')
    threshold_value = models.FloatField()
    channel = models.CharField(max_length=20, default='in_app', choices=[('in_app', 'In-App'), ('email', 'Email')])
    frequency = models.CharField(max_length=20, default='realtime', choices=[('realtime', 'Real-time'), ('daily', 'Daily Digest')])
    is_active = models.BooleanField(default=True)
    last_triggered = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        c_label = self.country_id or (self.watchlist.name if self.watchlist else "All")
        return f"Alert: {c_label} {self.indicator_id} {self.operator} {self.threshold_value}"


class AlertHistory(models.Model):
    """Audit log of triggered alerts with explanatory context."""
    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name='history')
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    triggered_at = models.DateTimeField(auto_now_add=True)
    indicator_value = models.FloatField()
    shap_summary = models.TextField(blank=True, help_text="Plain-language explanation of contributing drivers")

    class Meta:
        ordering = ['-triggered_at']
