"""Ship normalized readings to the Logstash HTTP input as NDJSON."""

import json
import logging

import httpx

from config import get_settings
from schemas.reading import EmissionReading

logger = logging.getLogger(__name__)


def ship_readings(readings: list[EmissionReading]) -> bool:
    if not readings:
        return True
    body = "\n".join(json.dumps(reading.model_dump(mode="json")) for reading in readings)
    try:
        response = httpx.post(
            get_settings().logstash_url,
            content=body,
            headers={"Content-Type": "application/x-ndjson"},
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("Failed to ship %d reading(s) to Logstash: %s", len(readings), exc)
        return False
    return True
