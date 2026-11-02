import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests
import polars as pl
from django.conf import settings
from apps.warehouse.models import Country, IndicatorMetadata, MacroObservation

WORLD_BANK_BASE_URL = "http://api.worldbank.org/v2"

# Key core indicators across the 8 macro dimensions required by ATLAS
CORE_INDICATORS = [
    {
        "indicator_code": "NY.GDP.MKTP.KD.ZG",
        "name": "GDP Growth (Annual %)",
        "category": "economy",
        "source": "WDI",
        "unit": "%",
        "periodicity": "Annual",
        "description": "Annual percentage growth rate of GDP at market prices based on constant local currency."
    },
    {
        "indicator_code": "FP.CPI.TOTL.ZG",
        "name": "Inflation, Consumer Prices (Annual %)",
        "category": "inflation",
        "source": "WDI",
        "unit": "%",
        "periodicity": "Annual",
        "description": "Inflation as measured by the consumer price index reflects the annual percentage change in the cost to the average consumer."
    },
    {
        "indicator_code": "DT.DOD.DECT.GN.ZS",
        "name": "External Debt Stocks (% of GNI)",
        "category": "debt",
        "source": "WDI",
        "unit": "% of GNI",
        "periodicity": "Annual",
        "description": "Total external debt stocks to gross national income. Indicator of long-term external solvency."
    },
    {
        "indicator_code": "BN.CAB.XOKA.GD.ZS",
        "name": "Current Account Balance (% of GDP)",
        "category": "trade",
        "source": "WDI",
        "unit": "% of GDP",
        "periodicity": "Annual",
        "description": "Current account balance is the sum of net exports of goods and services, net primary income, and net secondary income."
    },
    {
        "indicator_code": "FI.RES.TOTL.MO",
        "name": "Total Reserves in Months of Imports",
        "category": "debt",
        "source": "WDI",
        "unit": "Months",
        "periodicity": "Annual",
        "description": "Total reserves comprise holdings of monetary gold, SDRs, and reserve position in the IMF, measured in months of imports."
    },
    {
        "indicator_code": "AG.PRD.FOOD.XD",
        "name": "Food Production Index (2014-2016 = 100)",
        "category": "food_energy",
        "source": "WDI",
        "unit": "Index",
        "periodicity": "Annual",
        "description": "Food production index covers food crops that are considered edible and that contain nutrients."
    },
    {
        "indicator_code": "SI.POV.DDAY",
        "name": "Poverty Headcount Ratio at $2.15 a Day (2017 PPP) (% of population)",
        "category": "social",
        "source": "WDI",
        "unit": "%",
        "periodicity": "Annual",
        "description": "Percentage of the population living on less than $2.15 a day at 2017 international prices."
    },
]


def seed_indicators() -> int:
    """Populates master IndicatorMetadata table with the core ATLAS indicator set."""
    created_count = 0
    for meta in CORE_INDICATORS:
        _, created = IndicatorMetadata.objects.update_or_create(
            indicator_code=meta["indicator_code"],
            defaults={
                "name": meta["name"],
                "category": meta["category"],
                "source": meta["source"],
                "unit": meta["unit"],
                "periodicity": meta["periodicity"],
                "description": meta["description"],
                "quality_score": 1.0,
            }
        )
        if created:
            created_count += 1
    return created_count


def fetch_and_seed_countries() -> int:
    """
    Fetches global sovereign country metadata from the World Bank API,
    caching raw payload to data/raw/countries_wb.json and loading Country records.
    """
    url = f"{WORLD_BANK_BASE_URL}/country?format=json&per_page=350"
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    payload = resp.json()

    raw_cache_path = settings.RAW_DATA_DIR / "countries_wb.json"
    with open(raw_cache_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    data_entries = payload[1] if len(payload) > 1 else []
    created_count = 0

    for item in data_entries:
        iso3 = item.get("id", "").strip().upper()
        if not iso3 or len(iso3) != 3:
            continue

        region_info = item.get("region", {})
        region_name = region_info.get("value", "") if isinstance(region_info, dict) else ""
        if region_name == "Aggregates":
            continue # Prioritize sovereign states

        income_info = item.get("incomeLevel", {})
        income_name = income_info.get("value", "") if isinstance(income_info, dict) else ""

        lat = None
        lon = None
        try:
            if item.get("latitude"):
                lat = float(item["latitude"])
            if item.get("longitude"):
                lon = float(item["longitude"])
        except ValueError:
            pass

        _, created = Country.objects.update_or_create(
            iso3=iso3,
            defaults={
                "iso2": item.get("iso2Code", "").strip().upper(),
                "name": item.get("name", "").strip(),
                "region": region_name,
                "income_group": income_name,
                "capital": item.get("capitalCity", "").strip(),
                "latitude": lat,
                "longitude": lon,
            }
        )
        if created:
            created_count += 1

    return created_count


def fetch_wdi_observations(indicator_code: str, start_year: int = 1995, end_year: int = 2024) -> int:
    """
    Fetches historical macro observations for a given indicator across all countries
    from the World Bank API, uses Polars for validation, caches to Parquet, and upserts to database.
    """
    url = f"{WORLD_BANK_BASE_URL}/country/all/indicator/{indicator_code}?date={start_year}:{end_year}&format=json&per_page=15000"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    payload = resp.json()

    if len(payload) < 2 or not payload[1]:
        return 0

    records = []
    for row in payload[1]:
        country_id = row.get("countryiso3code", "").strip().upper()
        val = row.get("value")
        date_str = row.get("date")
        if country_id and val is not None and date_str:
            try:
                yr = int(date_str)
                records.append({
                    "country_id": country_id,
                    "year": yr,
                    "value": float(val)
                })
            except (ValueError, TypeError):
                continue

    if not records:
        return 0

    # Polars DataFrame processing & caching
    df = pl.DataFrame(records)
    cache_path = settings.RAW_DATA_DIR / f"{indicator_code}.parquet"
    df.write_parquet(cache_path)

    # Filter to countries present in the Country table
    existing_countries = set(Country.objects.values_list('iso3', flat=True))
    valid_rows = df.filter(pl.col("country_id").is_in(existing_countries))

    indicator_obj = IndicatorMetadata.objects.get(indicator_code=indicator_code)

    # Bulk upsert observations
    obs_to_create = []
    # To prevent unique constraint collision on repeated runs, fetch existing keys
    existing_keys = set(
        MacroObservation.objects.filter(indicator=indicator_obj)
        .values_list('country_id', 'year')
    )

    for row in valid_rows.iter_rows(named=True):
        key = (row["country_id"], row["year"])
        if key not in existing_keys:
            obs_to_create.append(
                MacroObservation(
                    country_id=row["country_id"],
                    indicator=indicator_obj,
                    year=row["year"],
                    value=row["value"],
                    source="WDI",
                    is_imputed=False
                )
            )

    MacroObservation.objects.bulk_create(obs_to_create, batch_size=2000)
    return len(obs_to_create)
