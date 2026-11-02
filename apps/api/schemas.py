from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# --- Warehouse Schemas ---

class CountrySchema(BaseModel):
    iso3: str
    iso2: Optional[str] = None
    name: str
    region: Optional[str] = None
    income_group: Optional[str] = None
    capital: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class IndicatorSchema(BaseModel):
    indicator_code: str
    name: str
    category: str
    source: str
    unit: Optional[str] = None
    periodicity: str
    description: Optional[str] = None
    quality_score: float


class MacroObservationSchema(BaseModel):
    country_iso3: str
    indicator_code: str
    year: int
    value: Optional[float]
    source: str
    is_imputed: bool


class DataQualityAuditSchema(BaseModel):
    country_iso3: str
    indicator_code: str
    missing_fraction: float
    last_observed_year: Optional[int]
    staleness_score: float
    is_anomaly_detected: bool


# --- Real-Time & Personal Layer Schemas ---

class HeadlineSchema(BaseModel):
    id: int
    title: str
    source: str
    url: str
    location: Optional[str] = None
    published_at: datetime
    topic_cluster: Optional[str] = None
    is_relevant: bool


class CommodityPriceSchema(BaseModel):
    symbol: str
    name: str
    price: float
    currency: str
    change_24h_pct: Optional[float]
    timestamp: datetime


class WeatherObservationSchema(BaseModel):
    city: str
    country_code: Optional[str] = None
    temperature_c: float
    precipitation_mm: float
    wind_speed_kmh: float
    weather_code: int
    timestamp: datetime


class HistoricalCrisisSchema(BaseModel):
    crisis_id: str
    name: str
    year: int
    region: str
    crisis_types: List[str]
    summary: str
    what_happened: str
    transmission_channels: List[str]
    real_world_outcomes: Dict[str, Any]


class HeadlineDetailSchema(BaseModel):
    id: int
    title: str
    source: str
    url: str
    location: Optional[str]
    published_at: datetime
    is_relevant: bool
    status: str
    stage_1_trigger: Optional[Dict[str, Any]] = None
    stage_2_actors: Optional[Dict[str, Any]] = None
    stage_3_transmission: Optional[Dict[str, Any]] = None
    stage_4_impact_matrix: Optional[Dict[str, Any]] = None
    stage_5_cascade: Optional[Dict[str, Any]] = None
    stage_6_pocketbook: Optional[Dict[str, Any]] = None
    historical_matches: Optional[List[Dict[str, Any]]] = None


# --- Household & Wealth Schemas ---

class HouseholdInputSchema(BaseModel):
    city: str = Field(..., description="Target city for local pricing and weather context")
    monthly_salary: float = Field(..., gt=0, description="Monthly income in specified currency")
    currency: str = Field("USD", description="Currency symbol")
    monthly_rent: float = Field(0.0, ge=0)
    family_size: int = Field(1, ge=1)
    dietary_constraints: List[str] = Field(default_factory=list)


class BasketItemSchema(BaseModel):
    category: str # Kitchen, Transport, Utilities
    item: str
    allocated_amount: float
    share_of_budget_pct: float
    action_badge: str # PRE-EMPT, SUBSTITUTE, ADAPT, PROTECT, ADVOCATE
    rationale: str


class HouseholdBasketResponseSchema(BaseModel):
    city: str
    currency: str
    disposable_income: float
    items: List[BasketItemSchema]
    generated_at: datetime


class WealthAllocationSchema(BaseModel):
    liquid_currency_buffer_pct: float
    gold_pct: float
    bulk_buying_buffer_pct: float
    liquid_currency_buffer_amount: float
    gold_amount: float
    bulk_buying_buffer_amount: float
    recommendations: List[str]
