from django.contrib import admin
from .models import Country, IndicatorMetadata, MacroObservation, DataQualityAudit, Watchlist, AlertRule, AlertHistory

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('iso3', 'name', 'region', 'income_group')
    search_fields = ('iso3', 'name', 'region')
    list_filter = ('region', 'income_group')

@admin.register(IndicatorMetadata)
class IndicatorMetadataAdmin(admin.ModelAdmin):
    list_display = ('indicator_code', 'name', 'category', 'source', 'periodicity', 'quality_score')
    search_fields = ('indicator_code', 'name')
    list_filter = ('category', 'source', 'periodicity')

@admin.register(MacroObservation)
class MacroObservationAdmin(admin.ModelAdmin):
    list_display = ('country', 'indicator', 'year', 'value', 'source')
    search_fields = ('country__iso3', 'country__name', 'indicator__indicator_code')
    list_filter = ('year', 'source')
    raw_id_fields = ('country', 'indicator')

@admin.register(DataQualityAudit)
class DataQualityAuditAdmin(admin.ModelAdmin):
    list_display = ('country', 'indicator', 'missing_fraction', 'last_observed_year', 'staleness_score', 'is_anomaly_detected')
    list_filter = ('is_anomaly_detected',)
    raw_id_fields = ('country', 'indicator')

@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at')
    filter_horizontal = ('countries',)

@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ('country', 'indicator', 'operator', 'threshold_value', 'channel', 'is_active')
    list_filter = ('is_active', 'channel', 'operator')

@admin.register(AlertHistory)
class AlertHistoryAdmin(admin.ModelAdmin):
    list_display = ('rule', 'country', 'triggered_at', 'indicator_value')
    list_filter = ('triggered_at',)
