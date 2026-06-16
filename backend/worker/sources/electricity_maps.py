"""Electricity Maps grid carbon-intensity client."""

import logging

import httpx

from config import get_settings
from schemas.reading import EmissionReading
from worker.sources._common import parse_timestamp

logger = logging.getLogger(__name__)

API_URL = "https://api.electricitymap.org/v3/carbon-intensity/latest"
ZONES = ("DE", "FR")


def fetch_readings() -> list[EmissionReading]:
    settings = get_settings()
    if not settings.electricity_maps_api_key:
        logger.info("Electricity Maps API key not set; skipping")
        return []

    headers = {"auth-token": settings.electricity_maps_api_key}
    readings: list[EmissionReading] = []
    for zone in ZONES:
        try:
            response = httpx.get(API_URL, params={"zone": zone}, headers=headers, timeout=10.0)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            logger.warning("Electricity Maps fetch failed for zone %s: %s", zone, exc)
            continue
        intensity = data.get("carbonIntensity")
        if intensity is None:
            continue
        readings.append(
            EmissionReading(
                timestamp=parse_timestamp(data.get("datetime")),
                source="electricity_maps",
                metric="grid_carbon_intensity",
                value=float(intensity),
                unit="gCO2eq/kWh",
                region=zone,
            )
        )
    return readings
