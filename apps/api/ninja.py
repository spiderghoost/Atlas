from datetime import datetime, timezone
from typing import List, Optional
from ninja import NinjaAPI, Query
from django.shortcuts import get_object_or_404
from django.db.models import Q

from apps.warehouse.models import Country, IndicatorMetadata, MacroObservation, DataQualityAudit
from apps.realtime.models import NewsHeadline, CommodityLivePrice, WeatherObservation, HistoricalCrisis, AnalysisCache, UserHousehold
from apps.api.schemas import (
    CountrySchema, IndicatorSchema, MacroObservationSchema, DataQualityAuditSchema,
    HeadlineSchema, CommodityPriceSchema, WeatherObservationSchema, HistoricalCrisisSchema,
    HeadlineDetailSchema, HouseholdInputSchema, HouseholdBasketResponseSchema, BasketItemSchema,
    WealthAllocationSchema
)

api = NinjaAPI(
    title="ATLAS Global Economic Intelligence API",
    version="1.0.0",
    description="Institution-grade macroeconomic data warehouse, real-time geopolitical ripple tracker, and personal resilience endpoints."
)


@api.get("/health", tags=["System"])
def health_check(request):
    return {
        "status": "healthy",
        "service": "ATLAS Backend API",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ============================================================================
# MACRO DATA WAREHOUSE ENDPOINTS
# ============================================================================

@api.get("/macro/countries", response=List[CountrySchema], tags=["Macro Warehouse"])
def list_countries(request, region: Optional[str] = None, income_group: Optional[str] = None):
    qs = Country.objects.all()
    if region:
        qs = qs.filter(region__icontains=region)
    if income_group:
        qs = qs.filter(income_group__icontains=income_group)
    return [
        CountrySchema(
            iso3=c.iso3, iso2=c.iso2, name=c.name, region=c.region,
            income_group=c.income_group, capital=c.capital,
            latitude=c.latitude, longitude=c.longitude
        ) for c in qs
    ]


@api.get("/macro/indicators", response=List[IndicatorSchema], tags=["Macro Warehouse"])
def list_indicators(request, category: Optional[str] = None, search: Optional[str] = None):
    qs = IndicatorMetadata.objects.all()
    if category:
        qs = qs.filter(category=category)
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(indicator_code__icontains=search))
    return [
        IndicatorSchema(
            indicator_code=i.indicator_code, name=i.name, category=i.category,
            source=i.source, unit=i.unit, periodicity=i.periodicity,
            description=i.description, quality_score=i.quality_score
        ) for i in qs
    ]


@api.get("/macro/observations", response=List[MacroObservationSchema], tags=["Macro Warehouse"])
def get_observations(request, country: str, indicator: str, start_year: Optional[int] = None, end_year: Optional[int] = None):
    qs = MacroObservation.objects.filter(country_id=country.upper(), indicator_id=indicator)
    if start_year:
        qs = qs.filter(year__gte=start_year)
    if end_year:
        qs = qs.filter(year__lte=end_year)
    return [
        MacroObservationSchema(
            country_iso3=o.country_id, indicator_code=o.indicator_id,
            year=o.year, value=o.value, source=o.source, is_imputed=o.is_imputed
        ) for o in qs.order_by('year')
    ]


@api.get("/macro/quality-audits", response=List[DataQualityAuditSchema], tags=["Macro Warehouse"])
def get_quality_audits(request, country: Optional[str] = None, indicator: Optional[str] = None):
    qs = DataQualityAudit.objects.all()
    if country:
        qs = qs.filter(country_id=country.upper())
    if indicator:
        qs = qs.filter(indicator_id=indicator)
    return [
        DataQualityAuditSchema(
            country_iso3=q.country_id, indicator_code=q.indicator_id,
            missing_fraction=q.missing_fraction, last_observed_year=q.last_observed_year,
            staleness_score=q.staleness_score, is_anomaly_detected=q.is_anomaly_detected
        ) for q in qs
    ]


# ============================================================================
# REAL-TIME & PERSONAL LAYER ENDPOINTS (§16)
# ============================================================================

@api.get("/realtime/headlines", response=List[HeadlineSchema], tags=["PocketRipple (Real-Time)"])
def list_headlines(request, relevant_only: bool = True, limit: int = 50):
    qs = NewsHeadline.objects.all()
    if relevant_only:
        qs = qs.filter(is_relevant=True)
    return [
        HeadlineSchema(
            id=h.id, title=h.title, source=h.source, url=h.url,
            location=h.location, published_at=h.published_at,
            topic_cluster=h.topic_cluster, is_relevant=h.is_relevant
        ) for h in qs[:limit]
    ]


@api.get("/realtime/headlines/{headline_id}", response=HeadlineDetailSchema, tags=["PocketRipple (Real-Time)"])
def get_headline_detail(request, headline_id: int):
    h = NewsHeadline.objects.get(id=headline_id)
    cache = getattr(h, 'analysis', None)
    return HeadlineDetailSchema(
        id=h.id,
        title=h.title,
        source=h.source,
        url=h.url,
        location=h.location,
        published_at=h.published_at,
        is_relevant=h.is_relevant,
        status=cache.status if cache else "PENDING",
        stage_1_trigger=cache.stage_1_trigger if cache else None,
        stage_2_actors=cache.stage_2_actors if cache else None,
        stage_3_transmission=cache.stage_3_transmission if cache else None,
        stage_4_impact_matrix=cache.stage_4_impact_matrix if cache else None,
        stage_5_cascade=cache.stage_5_cascade if cache else None,
        stage_6_pocketbook=cache.stage_6_pocketbook if cache else None,
        historical_matches=cache.historical_matches if cache else [],
    )


@api.get("/realtime/commodities", response=List[CommodityPriceSchema], tags=["PocketRipple (Real-Time)"])
def get_commodity_prices(request):
    # Return latest price per unique symbol
    symbols = CommodityLivePrice.objects.values_list('symbol', flat=True).distinct()
    latest_prices = []
    for sym in symbols:
        p = CommodityLivePrice.objects.filter(symbol=sym).order_by('-timestamp').first()
        if p:
            latest_prices.append(CommodityPriceSchema(
                symbol=p.symbol, name=p.name, price=p.price,
                currency=p.currency, change_24h_pct=p.change_24h_pct,
                timestamp=p.timestamp
            ))
    return latest_prices


@api.get("/realtime/weather", response=List[WeatherObservationSchema], tags=["PocketRipple (Real-Time)"])
def get_weather(request, city: Optional[str] = None):
    qs = WeatherObservation.objects.all()
    if city:
        qs = qs.filter(city__icontains=city)
    # Return most recent observation per city
    cities = qs.values_list('city', flat=True).distinct()
    obs_list = []
    for c in cities:
        w = WeatherObservation.objects.filter(city=c).order_by('-timestamp').first()
        if w:
            obs_list.append(WeatherObservationSchema(
                city=w.city, country_code=w.country_code,
                temperature_c=w.temperature_c, precipitation_mm=w.precipitation_mm,
                wind_speed_kmh=w.wind_speed_kmh, weather_code=w.weather_code,
                timestamp=w.timestamp
            ))
    return obs_list


@api.get("/realtime/crises", response=List[HistoricalCrisisSchema], tags=["Historical Crises Grounding"])
def list_historical_crises(request, region: Optional[str] = None):
    qs = HistoricalCrisis.objects.all()
    if region:
        qs = qs.filter(region__icontains=region)
    return [
        HistoricalCrisisSchema(
            crisis_id=c.crisis_id, name=c.name, year=c.year,
            region=c.region, crisis_types=c.crisis_types,
            summary=c.summary, what_happened=c.what_happened,
            transmission_channels=c.transmission_channels,
            real_world_outcomes=c.real_world_outcomes
        ) for c in qs
    ]


# ============================================================================
# PERSONAL RESILIENCE: BASKET & WEALTH GUARD (§16)
# ============================================================================

@api.post("/personal/basket/optimize", response=HouseholdBasketResponseSchema, tags=["Personal Resilience"])
def optimize_household_basket(request, payload: HouseholdInputSchema):
    """
    Deterministic household basket optimizer: takes household constraints and produces
    itemized monthly allocations across Kitchen, Transport, and Utilities with action badges.
    """
    disposable = max(0.0, payload.monthly_salary - payload.monthly_rent)
    
    # Baseline breakdown percentages of disposable income
    kitchen_share = 0.50
    transport_share = 0.25
    utilities_share = 0.25

    kitchen_budget = disposable * kitchen_share
    transport_budget = disposable * transport_share
    utilities_budget = disposable * utilities_share

    items = [
        BasketItemSchema(
            category="Kitchen",
            item="Staple Grains & Bread (Rice, Flour)",
            allocated_amount=round(kitchen_budget * 0.35, 2),
            share_of_budget_pct=round(kitchen_share * 0.35 * 100, 1),
            action_badge="PRE-EMPT",
            rationale="Global grain supply risks suggest purchasing 2-month bulk buffers before price shocks."
        ),
        BasketItemSchema(
            category="Kitchen",
            item="Proteins & Dairy",
            allocated_amount=round(kitchen_budget * 0.40, 2),
            share_of_budget_pct=round(kitchen_share * 0.40 * 100, 1),
            action_badge="SUBSTITUTE",
            rationale="Rotate towards locally produced legumes and plant proteins if imported beef/dairy rises."
        ),
        BasketItemSchema(
            category="Kitchen",
            item="Cooking Oil & Condiments",
            allocated_amount=round(kitchen_budget * 0.25, 2),
            share_of_budget_pct=round(kitchen_share * 0.25 * 100, 1),
            action_badge="PROTECT",
            rationale="Edible oil indices are volatile; lock in 60-day household inventory."
        ),
        BasketItemSchema(
            category="Transport",
            item="Commute & Fuel",
            allocated_amount=round(transport_budget * 0.75, 2),
            share_of_budget_pct=round(transport_share * 0.75 * 100, 1),
            action_badge="ADAPT",
            rationale="Brent crude movements impact transit; combine trip legs and leverage public transit passes."
        ),
        BasketItemSchema(
            category="Transport",
            item="Vehicle Maintenance & Spares",
            allocated_amount=round(transport_budget * 0.25, 2),
            share_of_budget_pct=round(transport_share * 0.25 * 100, 1),
            action_badge="PRE-EMPT",
            rationale="Imported spare parts carry currency depreciation risk; inspect essential parts early."
        ),
        BasketItemSchema(
            category="Utilities",
            item="Electricity & Heating Gas",
            allocated_amount=round(utilities_budget * 0.70, 2),
            share_of_budget_pct=round(utilities_share * 0.70 * 100, 1),
            action_badge="ADAPT",
            rationale="Peak tariff hours and winter heating adjustments reduce bill strain."
        ),
        BasketItemSchema(
            category="Utilities",
            item="Water & Municipal Services",
            allocated_amount=round(utilities_budget * 0.30, 2),
            share_of_budget_pct=round(utilities_share * 0.30 * 100, 1),
            action_badge="PROTECT",
            rationale="Essential fixed utility allocation."
        )
    ]

    return HouseholdBasketResponseSchema(
        city=payload.city,
        currency=payload.currency,
        disposable_income=disposable,
        items=items,
        generated_at=datetime.now(timezone.utc)
    )


@api.post("/personal/wealth/allocate", response=WealthAllocationSchema, tags=["Personal Resilience"])
def allocate_personal_wealth(request, payload: HouseholdInputSchema):
    """
    Deterministic salary allocation card: recommends split between local-currency liquid buffer,
    gold allocation, and bulk essential buying.
    """
    disposable = max(0.0, payload.monthly_salary - payload.monthly_rent)
    
    # Allocation policy based on inflation regime
    liquid_pct = 0.50
    gold_pct = 0.25
    bulk_pct = 0.25

    return WealthAllocationSchema(
        liquid_currency_buffer_pct=liquid_pct,
        gold_pct=gold_pct,
        bulk_buying_buffer_pct=bulk_pct,
        liquid_currency_buffer_amount=round(disposable * liquid_pct, 2),
        gold_amount=round(disposable * gold_pct, 2),
        bulk_buying_buffer_amount=round(disposable * bulk_pct, 2),
        recommendations=[
            "Keep 50% in local currency cash buffer to cover 3–6 months of fixed household commitments.",
            "Allocate 25% to fractional physical gold / gold bullion as a hedge against currency depreciation.",
            "Deploy 25% into bulk purchases of non-perishable pantry and household essentials before tariff increases."
        ]
    )
