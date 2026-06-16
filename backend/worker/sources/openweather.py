"""OpenWeatherMap Air Pollution client (CO, NO2, PM2.5)."""

import logging
from datetime import datetime, timezone

import httpx

from config import get_settings
from schemas.reading import EmissionReading

logger = logging.getLogger(__name__)

API_URL = "http://api.openweathermap.org/data/2.5/air_pollution"
LOCATIONS = (
    {"label": "London", "lat": 51.5074, "lon": -0.1278},
    {"label": "Mumbai", "lat": 19.0760, "lon": 72.8777},
)
POLLUTANTS = {"co": "air_co", "no2": "air_no2", "pm2_5": "air_pm2_5"}


def _epoch_to_dt(epoch: int | None) -> datetime:
    if epoch is None:
        return datetime.now(timezone.utc)
    return datetime.fromtimestamp(epoch, tz=timezone.utc)


def fetch_readings() -> list[EmissionReading]:
    settings = get_settings()
    if not settings.openweathermap_api_key:
        logger.info("OpenWeatherMap API key not set; skipping")
        return []

    readings: list[EmissionReading] = []
    for loc in LOCATIONS:
        params = {"lat": loc["lat"], "lon": loc["lon"], "appid": settings.openweathermap_api_key}
        try:
            response = httpx.get(API_URL, params=params, timeout=10.0)
            response.raise_for_status()
            entry = response.json()["list"][0]
        except (httpx.HTTPError, KeyError, IndexError) as exc:
            logger.warning("OpenWeatherMap fetch failed for %s: %s", loc["label"], exc)
            continue
        timestamp = _epoch_to_dt(entry.get("dt"))
        components = entry.get("components", {})
        for key, metric in POLLUTANTS.items():
            value = components.get(key)
            if value is None:
                continue
            readings.append(
                EmissionReading(
                    timestamp=timestamp,
                    source="openweathermap",
                    metric=metric,
                    value=float(value),
                    unit="ug/m3",
                    region=loc["label"],
                )
            )
    return readings
