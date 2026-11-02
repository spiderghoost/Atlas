from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import polars as pl
from apps.warehouse.models import Country, IndicatorMetadata, MacroObservation, DataQualityAudit


def run_data_quality_audit(indicator_code: Optional[str] = None, window_start: int = 2000, window_end: int = 2024) -> Dict[str, Any]:
    """
    Executes automated data quality health audit across country time-series:
    - Calculates missingness fraction against the target year range
    - Detects series staleness
    - Identifies statistical outliers / rate-of-change anomalies
    """
    total_years = (window_end - window_start) + 1
    current_year = datetime.now(timezone.utc).year

    ind_qs = IndicatorMetadata.objects.all()
    if indicator_code:
        ind_qs = ind_qs.filter(indicator_code=indicator_code)

    stats = {"audited_series": 0, "anomalies_detected": 0, "stale_series": 0}

    for ind in ind_qs:
        obs_qs = MacroObservation.objects.filter(
            indicator=ind,
            year__gte=window_start,
            year__lte=window_end
        ).values('country_id', 'year', 'value')

        if not obs_qs.exists():
            continue

        df = pl.DataFrame(list(obs_qs))
        
        # Group by country to compute missingness and staleness
        countries = df["country_id"].unique().to_list()
        for cid in countries:
            country_df = df.filter(pl.col("country_id") == cid).sort("year")
            observed_count = len(country_df)
            missing_frac = round(max(0.0, (total_years - observed_count) / total_years), 3)

            last_year = country_df["year"].max()
            staleness = float(current_year - last_year) if last_year else float(total_years)
            if staleness > 2.0:
                stats["stale_series"] += 1

            # Anomaly check: compute absolute difference between consecutive years
            is_anomaly = False
            anomaly_info = {}
            if observed_count >= 5:
                vals = country_df["value"].drop_nulls().to_numpy()
                diffs = [abs(vals[i] - vals[i-1]) for i in range(1, len(vals))]
                if diffs:
                    mean_diff = sum(diffs) / len(diffs)
                    max_diff = max(diffs)
                    if mean_diff > 0 and max_diff > (mean_diff * 4.0):
                        is_anomaly = True
                        stats["anomalies_detected"] += 1
                        anomaly_info = {
                            "type": "sudden_shock_or_glitch",
                            "max_step_change": round(max_diff, 2),
                            "mean_step_change": round(mean_diff, 2)
                        }

            DataQualityAudit.objects.update_or_create(
                country_id=cid,
                indicator=ind,
                defaults={
                    "missing_fraction": missing_frac,
                    "last_observed_year": last_year,
                    "staleness_score": staleness,
                    "is_anomaly_detected": is_anomaly,
                    "anomaly_details": anomaly_info
                }
            )
            stats["audited_series"] += 1

    return stats
