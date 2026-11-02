from django.contrib import admin
from .models import NewsHeadline, CommodityLivePrice, WeatherObservation, HistoricalCrisis, AnalysisCache, UserHousehold

@admin.register(NewsHeadline)
class NewsHeadlineAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'published_at', 'is_relevant', 'topic_cluster')
    list_filter = ('is_relevant', 'source', 'published_at')
    search_fields = ('title', 'location', 'topic_cluster')

@admin.register(CommodityLivePrice)
class CommodityLivePriceAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'price', 'currency', 'change_24h_pct', 'timestamp')
    list_filter = ('symbol', 'currency')
    search_fields = ('symbol', 'name')

@admin.register(WeatherObservation)
class WeatherObservationAdmin(admin.ModelAdmin):
    list_display = ('city', 'temperature_c', 'precipitation_mm', 'wind_speed_kmh', 'timestamp')
    list_filter = ('city',)
    search_fields = ('city',)

@admin.register(HistoricalCrisis)
class HistoricalCrisisAdmin(admin.ModelAdmin):
    list_display = ('crisis_id', 'name', 'year', 'region')
    search_fields = ('crisis_id', 'name', 'region', 'summary')
    list_filter = ('year', 'region')

@admin.register(AnalysisCache)
class AnalysisCacheAdmin(admin.ModelAdmin):
    list_display = ('headline', 'status', 'model_used', 'pipeline_version', 'created_at')
    list_filter = ('status', 'model_used')

@admin.register(UserHousehold)
class UserHouseholdAdmin(admin.ModelAdmin):
    list_display = ('city', 'monthly_salary', 'currency', 'family_size', 'created_at')
    list_filter = ('city', 'currency')
