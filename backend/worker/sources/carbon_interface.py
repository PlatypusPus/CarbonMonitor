"""Carbon Interface electricity-emission estimate client."""

import logging

import httpx

from config import get_settings
from schemas.reading import EmissionReading
from worker.sources._common import parse_timestamp

logger = logging.getLogger(__name__)

API_URL = "https://www.carboninterface.com/api/v1/estimates"
ELECTRICITY_UNIT = "kwh"
ESTIMATE_INPUTS = (
    {"country": "us", "electricity_value": 1000},
    {"country": "de", "electricity_value": 500},
)


def fetch_readings() -> list[EmissionReading]:
    settings = get_settings()
    if not settings.carbon_interface_api_key:
        logger.info("Carbon Interface API key not set; skipping")
        return []

    headers = {
        "Authorization": f"Bearer {settings.carbon_interface_api_key}",
        "Content-Type": "application/json",
    }
    readings: list[EmissionReading] = []
    for item in ESTIMATE_INPUTS:
        body = {
            "type": "electricity",
            "electricity_unit": ELECTRICITY_UNIT,
            "electricity_value": item["electricity_value"],
            "country": item["country"],
        }
        try:
            response = httpx.post(API_URL, json=body, headers=headers, timeout=10.0)
            response.raise_for_status()
            attributes = response.json()["data"]["attributes"]
        except (httpx.HTTPError, KeyError) as exc:
            logger.warning("Carbon Interface estimate failed for %s: %s", item["country"], exc)
            continue
        carbon_kg = attributes.get("carbon_kg")
        if carbon_kg is None:
            continue
        readings.append(
            EmissionReading(
                timestamp=parse_timestamp(attributes.get("estimated_at")),
                source="carbon_interface",
                metric="electricity_emissions",
                value=float(carbon_kg),
                unit="kg",
                region=item["country"],
            )
        )
    return readings
